"""Agent-style tools for football squad recommendations.

If DEEPSEEK_API_KEY or SOCCER_AGENT_API_KEY is configured, DeepSeek plans the
search profile from natural language. Local Django tools still execute database
lookup and ranking, so the model cannot invent players or SQL results. Without
an API key, the module falls back to a deterministic keyword parser.
"""
import builtins
import json
import os
import re
from datetime import date
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.utils.translation import gettext as _

from .models import Interested, Player, PlayerAttributes, Team, League


ATTRIBUTE_LABELS = {
    'overall_rating': 'Overall',
    'potential': 'Potential',
    'crossing': 'Crossing',
    'finishing': 'Finishing',
    'heading_accuracy': 'Heading',
    'short_passing': 'Short Passing',
    'long_passing': 'Long Passing',
    'ball_control': 'Ball Control',
    'dribbling': 'Dribbling',
    'acceleration': 'Acceleration',
    'sprint_speed': 'Sprint Speed',
    'stamina': 'Stamina',
    'strength': 'Strength',
    'shot_power': 'Shot Power',
    'long_shots': 'Long Shots',
    'interceptions': 'Interceptions',
    'marking': 'Marking',
    'standing_tackle': 'Standing Tackle',
    'sliding_tackle': 'Sliding Tackle',
    'vision': 'Vision',
    'gk_diving': 'GK Diving',
    'gk_handling': 'GK Handling',
    'gk_kicking': 'GK Kicking',
    'gk_positioning': 'GK Positioning',
    'gk_reflexes': 'GK Reflexes',
}


INTENT_PROFILES = [
    {
        'name': 'attacking finisher',
        'keywords': ['striker', 'forward', 'finish', 'scorer', 'shoot', 'attack',
                     '前锋', '射手', '进攻', '射门', '得分', '终结'],
        'weights': {
            'finishing': 1.5, 'shot_power': 1.0, 'positioning': 1.0,
            'dribbling': 0.8, 'ball_control': 0.8, 'overall_rating': 0.7,
        },
    },
    {
        'name': 'playmaker',
        'keywords': ['playmaker', 'pass', 'creative', 'midfield', 'vision',
                     '组织', '中场', '传球', '视野', '创造'],
        'weights': {
            'short_passing': 1.4, 'long_passing': 1.1, 'vision': 1.2,
            'ball_control': 1.0, 'dribbling': 0.7, 'overall_rating': 0.7,
        },
    },
    {
        'name': 'winger',
        'keywords': ['wing', 'wide', 'cross', 'pace', 'fast', 'speed',
                     '边路', '边锋', '传中', '速度', '快', '突破'],
        'weights': {
            'sprint_speed': 1.3, 'acceleration': 1.2, 'crossing': 1.1,
            'dribbling': 1.0, 'stamina': 0.6, 'overall_rating': 0.6,
        },
    },
    {
        'name': 'defensive ball winner',
        'keywords': ['defender', 'defence', 'defense', 'tackle', 'intercept',
                     '防守', '后卫', '抢断', '拦截', '盯人'],
        'weights': {
            'marking': 1.2, 'standing_tackle': 1.3, 'sliding_tackle': 0.9,
            'interceptions': 1.2, 'strength': 0.8, 'overall_rating': 0.6,
        },
    },
    {
        'name': 'goalkeeper',
        'keywords': ['goalkeeper', 'keeper', 'gk', '门将', '守门员'],
        'weights': {
            'gk_diving': 1.2, 'gk_handling': 1.2, 'gk_positioning': 1.1,
            'gk_reflexes': 1.2, 'gk_kicking': 0.6, 'overall_rating': 0.5,
        },
    },
    {
        'name': 'high-potential young player',
        'keywords': ['young', 'youth', 'future', 'potential', 'u23',
                     '年轻', '潜力', '未来', '小将'],
        'weights': {
            'potential': 1.5, 'overall_rating': 0.8, 'acceleration': 0.6,
            'stamina': 0.5,
        },
        'prefer_young': True,
    },
]


DEFAULT_WEIGHTS = {
    'overall_rating': 1.2,
    'potential': 1.0,
    'ball_control': 0.6,
    'stamina': 0.4,
}

ALLOWED_FIELDS = set(ATTRIBUTE_LABELS.keys()) | {'positioning'}
DEEPSEEK_CHAT_COMPLETIONS_URL = 'https://api.deepseek.com/chat/completions'


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _date_parts(value):
    match = re.match(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', str(value or ''))
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _age_from_birthday(birthday, as_of=None):
    if not birthday:
        return None
    birthday_parts = _date_parts(birthday)
    if not birthday_parts:
        return None
    year, month, day = birthday_parts
    as_of_parts = _date_parts(as_of)
    if as_of_parts:
        ref_year, ref_month, ref_day = as_of_parts
    else:
        today = date.today()
        ref_year, ref_month, ref_day = today.year, today.month, today.day
    return ref_year - year - ((ref_month, ref_day) < (month, day))


def _parse_age_limit(text):
    patterns = [
        r'under\s*(\d{2})',
        r'below\s*(\d{2})',
        r'u\s*(\d{2})',
        r'(\d{2})\s*岁以下',
        r'(\d{2})\s*以下',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def _clean_llm_weights(weights):
    cleaned = {}
    if not isinstance(weights, dict):
        return cleaned
    for field, weight in weights.items():
        if field not in ALLOWED_FIELDS:
            continue
        try:
            numeric_weight = float(weight)
        except (TypeError, ValueError):
            continue
        if numeric_weight > 0:
            cleaned[field] = min(numeric_weight, 2.0)
    return cleaned


def _call_deepseek_planner(query):
    """Ask DeepSeek for a structured player-search plan."""
    api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('SOCCER_AGENT_API_KEY')
    if not api_key:
        return None

    model = os.getenv('SOCCER_AGENT_MODEL', 'deepseek-chat')
    system_prompt = (
        'You are a football recruitment planning agent. Convert the manager request '
        'into JSON for local database tools. Do not invent players. '
        'Use only these attribute fields: '
        f"{', '.join(sorted(ALLOWED_FIELDS))}. "
        'Return JSON with keys: matched_intents (array of short English labels), '
        'weights (object mapping field names to numbers from 0.1 to 2.0), '
        'max_age (integer or null), rationale (short sentence). '
        'Write matched_intents and rationale in the same language as the manager request.'
    )
    body = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': query},
        ],
        'temperature': 0.2,
        'response_format': {'type': 'json_object'},
        'stream': False,
    }
    req = urlrequest.Request(
        DEEPSEEK_CHAT_COMPLETIONS_URL,
        data=json.dumps(body).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urlrequest.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return {'error': str(exc)}

    try:
        content = payload['choices'][0]['message']['content']
        plan = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        return {'error': f'Invalid DeepSeek planner response: {exc}'}

    weights = _clean_llm_weights(plan.get('weights'))
    if not weights:
        return {'error': 'DeepSeek planner did not return valid attribute weights.'}

    max_age = plan.get('max_age')
    try:
        max_age = int(max_age) if max_age is not None else None
    except (TypeError, ValueError):
        max_age = None

    matched_intents = plan.get('matched_intents') or ['deepseek planned player profile']
    if not isinstance(matched_intents, list):
        matched_intents = [str(matched_intents)]

    return {
        'query': query or '',
        'weights': weights,
        'matched_intents': [str(item)[:60] for item in matched_intents[:4]],
        'max_age': max_age,
        'source': 'deepseek',
        'rationale': str(plan.get('rationale') or '')[:240],
    }


def parse_manager_request(query):
    """Convert a natural-language request into a weighted search profile."""
    deepseek_plan = _call_deepseek_planner(query)
    if deepseek_plan and 'error' not in deepseek_plan:
        return deepseek_plan

    normalized = (query or '').strip().lower()
    weights = {}
    matched_intents = []
    prefer_young = False

    for profile in INTENT_PROFILES:
        if any(keyword in normalized for keyword in profile['keywords']):
            matched_intents.append(profile['name'])
            prefer_young = prefer_young or profile.get('prefer_young', False)
            for field, weight in profile['weights'].items():
                weights[field] = weights.get(field, 0) + weight

    if not weights:
        weights.update(DEFAULT_WEIGHTS)
        matched_intents.append('balanced player')

    max_age = _parse_age_limit(normalized)
    if prefer_young and max_age is None:
        max_age = 23

    return {
        'query': query or '',
        'weights': weights,
        'matched_intents': matched_intents,
        'max_age': max_age,
        'source': 'rules',
        'planner_error': deepseek_plan.get('error') if deepseek_plan else '',
    }


def _latest_attribute_snapshots(max_scan=60000):
    """Return one recent attribute row per player without relying on SQL DISTINCT ON."""
    snapshots = {}
    rows = PlayerAttributes.objects.exclude(
        player_fifa_api_id__isnull=True).order_by('-date')[:max_scan]
    for attrs in rows:
        if attrs.player_fifa_api_id not in snapshots:
            snapshots[attrs.player_fifa_api_id] = attrs
    return snapshots


def recommend_players_for_request(manager_id, query, limit=12):
    """Route a request through parser + player search tool and return ranked results."""
    plan = parse_manager_request(query)
    interested_ids = set(Interested.objects.filter(
        manager_id=manager_id).values_list('player_fifa_api_id', flat=True))

    snapshots = _latest_attribute_snapshots()
    players = {
        player.player_fifa_api_id: player
        for player in Player.objects.filter(player_fifa_api_id__in=snapshots.keys())
    }
    team_ids = {player.team_api_id for player in players.values() if player.team_api_id}
    teams = {
        team.team_api_id: team
        for team in Team.objects.filter(team_api_id__in=team_ids)
    }
    leagues = {
        league.id: league.name
        for league in League.objects.all()
    }

    scored = []
    for player_id, attrs in snapshots.items():
        if player_id in interested_ids or player_id not in players:
            continue

        player = players[player_id]
        age = _age_from_birthday(player.birthday, attrs.date)
        if plan['max_age'] is not None and (age is None or age > plan['max_age']):
            continue

        score_sum = 0
        weight_sum = 0
        evidence = []
        for field, weight in plan['weights'].items():
            value = _to_number(builtins.getattr(attrs, field, None))
            if value is None:
                continue
            score_sum += value * weight
            weight_sum += weight
            evidence.append((_(ATTRIBUTE_LABELS.get(field, field)), value, weight))

        if not weight_sum:
            continue

        score = score_sum / weight_sum
        if age is not None and plan['max_age'] is not None:
            score += max(0, plan['max_age'] - age) * 0.4

        evidence.sort(key=lambda item: item[2], reverse=True)
        team = teams.get(player.team_api_id)
        scored.append({
            'player': player,
            'team_name': team.team_long_name if team else 'Unknown Team',
            'league_name': leagues.get(player.league_id, 'Unknown League'),
            'age': age,
            'score': round(score, 1),
            'evidence': evidence[:3],
            'overall': _to_number(attrs.overall_rating),
            'potential': _to_number(attrs.potential),
        })

    scored.sort(key=lambda item: item['score'], reverse=True)
    return {
        'plan': plan,
        'tools_called': ([_('DeepSeek planner')] if plan.get('source') == 'deepseek' else [
            _('keyword intent parser')
        ]) + [_('latest player snapshots'), _('weighted player ranking')],
        'results': scored[:limit],
        'scanned_players': len(snapshots),
    }
