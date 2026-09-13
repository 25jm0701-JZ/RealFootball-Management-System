"""Views for the RealFootball management system.

双角色功能：
- 普通用户（球迷）：关注球队/球员、查看与取消关注、球队推荐、猜球员游戏
- 足球经理（教练）：关注感兴趣的球员、申请执教球队、查看我的球队/球员、球员推荐

身份统一约定：会话中 user_id 表示普通用户、manager_id 表示足球经理，
所有需要登录的视图都通过 @user_required / @manager_required 保护。
"""
import random
import builtins

from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Avg, Max, Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt

from .agent_tools import recommend_players_for_request
from .models import (
    Employ, Follow, FootballManager, Interested, League, ManagerAccountUser,
    Match, Player, PlayerAttributes, Subscribe, Team, TeamAttributes,
    User, UserAccountUser,
)

# ---------------------------------------------------------------------------
# 登录保护装饰器
# ---------------------------------------------------------------------------


def user_required(view_func):
    """要求当前会话为已登录的普通用户。"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('custom_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """要求当前会话为已登录的足球经理。"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('manager_id'):
            return redirect('custom_login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# 通用辅助
# ---------------------------------------------------------------------------


def _success_response(request, heading, message, primary_url, primary_label,
                      secondary_url=None, secondary_label=None):
    """渲染统一的成功提示页（URL 参数为 urls.py 中的路由名）。"""
    return render(request, 'success_page.html', {
        'heading': heading,
        'message': message,
        'primary_url': primary_url,
        'primary_label': primary_label,
        'secondary_url': secondary_url,
        'secondary_label': secondary_label,
    })


def _league_team_player_context(leagues, league_id, team_api_id):
    """构造「联赛→球队→球员」级联下拉所需的统一上下文（键恒齐全）。

    无论参数是否缺失，都返回 leagues/league_id/team_api_id/teams/players
    五个键，其中 teams 与 players 可能为 None。
    """
    ctx = {
        'leagues': leagues,
        'league_id': league_id,
        'team_api_id': team_api_id,
        'teams': None,
        'players': None,
    }
    if league_id:
        ctx['teams'] = Team.objects.filter(league_id=league_id).order_by('team_long_name')
        if team_api_id:
            ctx['players'] = Player.objects.filter(
                team_api_id=team_api_id).order_by('player_name')
    return ctx


# ---------------------------------------------------------------------------
# 认证：登录 / 注册 / 登出
# ---------------------------------------------------------------------------


@csrf_exempt
def custom_login_view(request):
    if request.method == 'GET':
        # 打开登录页时清除可能残留的会话身份
        request.session.pop('manager_id', None)
        request.session.pop('manager_username', None)
        request.session.pop('user_id', None)
        request.session.pop('user_username', None)
        return render(request, 'login.html')

    if request.method == 'POST':
        identity = request.POST.get('identity')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if identity == 'user':
            try:
                user = UserAccountUser.objects.get(username=username)
                if user.check_password(password):
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    # 清除可能残留的经理身份，避免交叉身份错乱
                    request.session.pop('manager_id', None)
                    request.session.pop('manager_username', None)
                    request.session['user_id'] = user.id
                    request.session['user_username'] = user.username
                    return _success_response(
                        request,
                        _('Login Successful'),
                        _('You are now logged in as a regular user.'),
                        'user_dashboard', _('Go to User Dashboard'))
            except UserAccountUser.DoesNotExist:
                pass

        elif identity == 'manager':
            try:
                manager = ManagerAccountUser.objects.get(username=username)
                if manager.check_password(password):
                    login(request, manager, backend='django.contrib.auth.backends.ModelBackend')
                    request.session.pop('user_id', None)
                    request.session.pop('user_username', None)
                    request.session['manager_id'] = manager.id
                    request.session['manager_username'] = manager.username
                    return redirect('manager_dashboard')
            except ManagerAccountUser.DoesNotExist:
                pass

        return HttpResponse(_('Invalid username or password.'))

    return HttpResponse(_('Only POST requests are supported for login.'))


@csrf_exempt
def register_view(request):
    if request.method == 'GET':
        request.session.pop('manager_id', None)
        request.session.pop('manager_username', None)
        request.session.pop('user_id', None)
        request.session.pop('user_username', None)
        return render(request, 'register.html')

    if request.method == 'POST':
        identity = request.POST.get('identity')
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name')
        age = request.POST.get('age')

        if identity == 'user':
            if UserAccountUser.objects.filter(username=username).exists():
                return render(request, 'register.html',
                              {'error': _('Username already exists.')})

            # 新用户 id 取 user 表最大 user_id + 1（课程项目范围内够用，未做并发保护）
            max_user_id = User.objects.aggregate(max_id=Max('user_id'))['max_id'] or 0
            new_user_id = max_user_id + 1

            User.objects.create(user_id=new_user_id, id=new_user_id, name=name, age=age)
            user = UserAccountUser(user_id=new_user_id, id=new_user_id, username=username)
            user.set_password(password)
            user.save()
            request.session['user_id'] = user.id
            request.session['user_username'] = user.username
            return _success_response(
                request,
                _('Registration Successful'),
                _('Registration successful. You are now logged in as a regular user.'),
                'user_dashboard', _('Go to User Dashboard'))

        elif identity == 'manager':
            if ManagerAccountUser.objects.filter(username=username).exists():
                return render(request, 'register.html',
                              {'error': _('Username already exists.')})

            max_licence_id = FootballManager.objects.aggregate(max_id=Max('licence_id'))['max_id'] or 0
            new_licence_id = max_licence_id + 1

            FootballManager.objects.create(
                licence_id=new_licence_id, id=new_licence_id, name=name, age=age)
            manager = ManagerAccountUser(
                licence_id=new_licence_id, id=new_licence_id, username=username)
            manager.set_password(password)
            manager.save()
            request.session['manager_id'] = manager.id
            request.session['manager_username'] = manager.username
            return redirect('manager_dashboard')

        return HttpResponse(_('Invalid identity type.'))


def logout_view(request):
    logout(request)
    return redirect('custom_login')


# ---------------------------------------------------------------------------
# 首页与仪表盘
# ---------------------------------------------------------------------------


def home_view(request):
    return render(request, 'index.html')


@user_required
def user_dashboard(request):
    return render(request, 'user_dashboard.html')


@manager_required
def manager_dashboard(request):
    return render(request, 'manager_dashboard.html')


# ---------------------------------------------------------------------------
# 普通用户：关注球队 / 球员
# ---------------------------------------------------------------------------


@csrf_exempt
@user_required
def follow_team_view(request):
    if request.method == 'GET':
        leagues = League.objects.all().order_by('name')
        league_id = request.GET.get('league_id')
        teams = (Team.objects.filter(league_id=league_id).order_by('team_long_name')
                 if league_id else None)
        return render(request, 'follow_team.html', {
            'leagues': leagues, 'teams': teams, 'league_id': league_id})

    if request.method == 'POST':
        user_id = request.session.get('user_id')
        team_api_id = request.POST.get('team_api_id')
        if team_api_id:
            max_id = Subscribe.objects.aggregate(max_id=Max('id'))['max_id'] or 0
            Subscribe.objects.create(id=max_id + 1, user_id=user_id, team_api_id=team_api_id)
            return _success_response(
                request, _('Success'), _('Team followed successfully.'),
                'user_dashboard', _('Back to Dashboard'),
                'view_followed_teams', _('View my followed teams'))
        return redirect('follow_team')


@csrf_exempt
@user_required
def follow_player_view(request):
    if request.method == 'GET':
        leagues = League.objects.all().order_by('name')
        league_id = request.GET.get('league_id')
        team_api_id = request.GET.get('team_api_id')
        ctx = _league_team_player_context(leagues, league_id, team_api_id)
        return render(request, 'follow_player.html', ctx)

    if request.method == 'POST':
        user_id = request.session.get('user_id')
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        if player_fifa_api_id:
            max_id = Follow.objects.aggregate(max_id=Max('id'))['max_id'] or 0
            Follow.objects.create(id=max_id + 1, user_id=user_id,
                                  player_fifa_api_id=player_fifa_api_id)
            return _success_response(
                request, _('Success'), _('Player followed successfully.'),
                'user_dashboard', _('Back to Dashboard'),
                'view_followed_players', _('View my followed players'))
        return redirect('follow_player')


@user_required
def view_followed_teams(request):
    user_id = request.session.get('user_id')
    team_ids = list(Subscribe.objects.filter(user_id=user_id).values_list(
        'team_api_id', flat=True))

    followed_teams = []
    for team in Team.objects.filter(team_api_id__in=team_ids).order_by('team_long_name'):
        attrs = TeamAttributes.objects.filter(
            team_api_id=team.team_api_id).order_by('-date').first()
        followed_teams.append({'team': team, 'attributes': attrs})

    return render(request, 'view_followed_teams.html', {
        'followed_teams': followed_teams, 'has_data': bool(followed_teams)})


@user_required
def view_followed_players(request):
    user_id = request.session.get('user_id')
    player_ids = list(Follow.objects.filter(user_id=user_id).values_list(
        'player_fifa_api_id', flat=True))

    followed_players = []
    for player in Player.objects.filter(player_fifa_api_id__in=player_ids).order_by('player_name'):
        attrs = PlayerAttributes.objects.filter(
            player_fifa_api_id=player.player_fifa_api_id).order_by('-date').first()
        followed_players.append({'player': player, 'attributes': attrs})

    return render(request, 'view_followed_players.html', {
        'followed_players': followed_players, 'has_data': bool(followed_players)})


@user_required
def view_followed_matches(request):
    user_id = request.session.get('user_id')
    team_ids = list(Subscribe.objects.filter(user_id=user_id).values_list(
        'team_api_id', flat=True))
    selected_team_id = request.GET.get('team_id')

    teams = Team.objects.filter(team_api_id__in=team_ids).order_by('team_long_name')

    if selected_team_id:
        matches = Match.objects.filter(
            Q(home_team_api_id=selected_team_id) | Q(away_team_api_id=selected_team_id)
        ).order_by('-date')
    else:
        matches = Match.objects.filter(
            Q(home_team_api_id__in=team_ids) | Q(away_team_api_id__in=team_ids)
        ).order_by('-date')

    # 给比赛行补充队名，供模板直接显示（含未关注的对手队）
    match_team_ids = set()
    for match in matches:
        match_team_ids.add(match.home_team_api_id)
        match_team_ids.add(match.away_team_api_id)
    all_team_names = dict(Team.objects.filter(
        team_api_id__in=match_team_ids).values_list('team_api_id', 'team_long_name'))
    for match in matches:
        match.home_team_name = all_team_names.get(match.home_team_api_id, match.home_team_api_id)
        match.away_team_name = all_team_names.get(match.away_team_api_id, match.away_team_api_id)

    return render(request, 'view_followed_matches.html', {
        'matches': matches, 'teams': teams, 'selected_team_id': selected_team_id,
        'has_data': matches.exists()})


# ---------------------------------------------------------------------------
# 普通用户：取消关注
# ---------------------------------------------------------------------------


@csrf_exempt
@user_required
def unfollow_team_view(request):
    if request.method == 'GET':
        user_id = request.session.get('user_id')
        subscriptions = Subscribe.objects.filter(user_id=user_id)
        teams = Team.objects.filter(
            team_api_id__in=[s.team_api_id for s in subscriptions]).order_by('team_long_name')
        return render(request, 'unfollow_team.html', {'teams': teams})

    if request.method == 'POST':
        user_id = request.session.get('user_id')
        team_api_id = request.POST.get('team_api_id')
        if team_api_id:
            Subscribe.objects.filter(user_id=user_id, team_api_id=team_api_id).delete()
            return _success_response(
                request, _('Success'), _('Team unfollowed successfully.'),
                'user_dashboard', _('Back to Dashboard'))
        return redirect('unfollow_team')


@csrf_exempt
@user_required
def unfollow_player_view(request):
    if request.method == 'GET':
        user_id = request.session.get('user_id')
        follows = Follow.objects.filter(user_id=user_id)
        players = Player.objects.filter(
            player_fifa_api_id__in=[f.player_fifa_api_id for f in follows]).order_by('player_name')
        return render(request, 'unfollow_player.html', {'players': players})

    if request.method == 'POST':
        user_id = request.session.get('user_id')
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        if player_fifa_api_id:
            Follow.objects.filter(user_id=user_id,
                                  player_fifa_api_id=player_fifa_api_id).delete()
            return _success_response(
                request, _('Success'), _('Player unfollowed successfully.'),
                'user_dashboard', _('Back to Dashboard'))
        return redirect('unfollow_player')


# ---------------------------------------------------------------------------
# 普通用户：球队推荐 / 猜球员
# ---------------------------------------------------------------------------


@csrf_exempt
@user_required
def recommend_team_view(request):
    user_id = request.session.get('user_id')
    all_attributes = [
        'buildupplayspeed', 'buildupplaypassing', 'chancecreationpassing',
        'defencepressure', 'defenceaggression', 'defenceteamwidth',
    ]

    selected_attribute = request.GET.get('attribute')
    recommended_teams = []
    message = ''

    if selected_attribute:
        team_ids = Subscribe.objects.filter(user_id=user_id).values_list(
            'team_api_id', flat=True)
        subscribed_attrs = TeamAttributes.objects.filter(
            team_api_id__in=team_ids).exclude(**{selected_attribute: None})
        avg_value = subscribed_attrs.aggregate(avg=Avg(selected_attribute))['avg']

        if avg_value is not None:
            nearby_attrs = TeamAttributes.objects.exclude(team_api_id__in=team_ids).filter(
                **{f'{selected_attribute}__range': (avg_value - 5, avg_value + 5)})
            # 同一球队有多个日期快照，按球队去重后取一条
            attr_by_team = {}
            for attr in nearby_attrs:
                if attr.team_api_id not in attr_by_team:
                    attr_by_team[attr.team_api_id] = builtins.getattr(attr, selected_attribute)

            teams_map = {t.team_api_id: t for t in Team.objects.filter(
                team_api_id__in=list(attr_by_team.keys()))}
            recommended_teams = [
                {'team': teams_map[tid], 'attribute_value': val}
                for tid, val in attr_by_team.items() if tid in teams_map
            ]
            recommended_teams.sort(key=lambda x: x['team'].team_long_name)
        else:
            message = _('The followed teams do not have valid data for this attribute.')

    if request.method == 'POST':
        user_id = request.session.get('user_id')
        team_api_id = request.POST.get('team_api_id')
        if team_api_id:
            max_id = Subscribe.objects.aggregate(max_id=Max('id'))['max_id'] or 0
            Subscribe.objects.create(id=max_id + 1, user_id=user_id, team_api_id=team_api_id)
            return _success_response(
                request, _('Success'), _('Recommended team followed successfully.'),
                'user_dashboard', _('Back to Dashboard'))

    return render(request, 'recommend_team.html', {
        'attributes': all_attributes,
        'selected_attribute': selected_attribute,
        'recommended_teams': recommended_teams,
        'message': message,
    })


@csrf_exempt
@user_required
def guess_player_view(request):
    context = {}
    if request.method == 'POST':
        selected = request.POST.get('selected')
        # 正确答案存于会话，避免把答案写进 HTML
        correct = request.session.get('guess_answer')
        context['answered'] = True
        context['is_correct'] = (selected == correct)
        context['previous_correct'] = correct

    # 选出一个随机球员及其属性
    candidates = PlayerAttributes.objects.exclude(player_fifa_api_id__isnull=True)
    if not candidates.exists():
        return render(request, 'guess_player.html',
                      {'error': _('No player data available.')})
    selected_attr = random.choice(list(candidates))
    player = Player.objects.filter(player_fifa_api_id=selected_attr.player_fifa_api_id).first()

    show_fields = ['overall_rating', 'potential', 'preferred_foot',
                   'attacking_work_rate', 'defensive_work_rate']
    attribute_info = {field: builtins.getattr(selected_attr, field, None)
                      for field in show_fields}
    attribute_info['birthday'] = player.birthday if player else '—'
    attribute_info['height'] = player.height if player else '—'
    attribute_info['weight'] = player.weight if player else '—'

    correct_name = player.player_name if player else _('Unknown Player')
    other_names = list(Player.objects.exclude(player_name=correct_name).values_list(
        'player_name', flat=True).distinct())
    options = random.sample(other_names, min(3, len(other_names))) + [correct_name]
    random.shuffle(options)

    request.session['guess_answer'] = correct_name

    context.update({
        'attribute_info': attribute_info,
        'options': options,
        'correct': correct_name,
    })
    return render(request, 'guess_player.html', context)


# ---------------------------------------------------------------------------
# 足球经理：关注感兴趣的球员
# ---------------------------------------------------------------------------


@csrf_exempt
@manager_required
def manager_follow_player_view(request):
    manager_id = request.session.get('manager_id')

    if request.method == 'GET':
        leagues = League.objects.all().order_by('name')
        league_id = request.GET.get('league_id')
        team_api_id = request.GET.get('team_api_id')
        ctx = _league_team_player_context(leagues, league_id, team_api_id)
        return render(request, 'manager_follow_player.html', ctx)

    if request.method == 'POST':
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        football_manager = FootballManager.objects.filter(id=manager_id).first()
        if player_fifa_api_id and football_manager:
            if not Interested.objects.filter(
                    manager=football_manager,
                    player_fifa_api_id=player_fifa_api_id).exists():
                Interested.objects.create(
                    manager=football_manager, player_fifa_api_id=player_fifa_api_id)
                messages.success(request, _('Player added to your interested list.'))
            else:
                messages.warning(request, _('This player is already in your interested list.'))
            return redirect('manager_view_interested_players')
        return redirect('manager_follow_player')


@manager_required
def manager_view_interested_players(request):
    manager_id = request.session.get('manager_id')
    football_manager = FootballManager.objects.filter(id=manager_id).first()

    interest_records = (Interested.objects.filter(manager=football_manager)
                        if football_manager else Interested.objects.none())
    player_ids = [record.player_fifa_api_id for record in interest_records]

    interested_players = []
    for player in Player.objects.filter(player_fifa_api_id__in=player_ids).order_by('player_name'):
        attrs = PlayerAttributes.objects.filter(
            player_fifa_api_id=player.player_fifa_api_id).order_by('-date').first()
        interested_players.append({'player': player, 'attributes': attrs})

    return render(request, 'manager_view_interested_players.html', {
        'interested_players': interested_players, 'manager': football_manager})


@csrf_exempt
@manager_required
def manager_delete_interested_player(request, player_fifa_api_id):
    manager_id = request.session.get('manager_id')
    football_manager = FootballManager.objects.filter(id=manager_id).first()
    if football_manager:
        Interested.objects.filter(
            manager=football_manager, player_fifa_api_id=player_fifa_api_id).delete()
    return redirect('manager_view_interested_players')


# ---------------------------------------------------------------------------
# 足球经理：申请执教 / 我的球队
# ---------------------------------------------------------------------------


@manager_required
def check_employment(request):
    manager_id = request.session.get('manager_id')

    # POST 申请执教：先于「已执教」判断，以便已执教经理也能收到错误提示
    if request.method == 'POST':
        if Employ.objects.filter(licence_id=manager_id).exists():
            messages.error(request, _('You can only manage one club at a time.'))
            return redirect('manager_check_employment')
        team_api_id = request.POST.get('team_api_id')
        if not team_api_id:
            messages.error(request, _('Please select a team.'))
            return redirect('manager_check_employment')
        try:
            # Employ 主键是 licence_id
            Employ.objects.create(licence_id=manager_id, team_api_id=team_api_id)
            return redirect('application_success')
        except IntegrityError:
            messages.error(request, _('Failed to create the employment record.'))
            return redirect('manager_check_employment')

    # GET：显示当前执教状态或申请表单
    employment = Employ.objects.filter(licence_id=manager_id).first()
    if employment:
        team = Team.objects.filter(team_api_id=employment.team_api_id).first()
        return render(request, 'manager_check_employment.html', {
            'has_employment': True, 'team': team})

    league_id = request.GET.get('league_id')
    leagues = League.objects.all().order_by('name')
    teams = (Team.objects.filter(league_id=league_id).order_by('team_long_name')
             if league_id else [])
    return render(request, 'manager_check_employment.html', {
        'has_employment': False,
        'leagues': leagues,
        'teams': teams,
        'show_teams': bool(league_id),
        'league_id': league_id,
    })


@manager_required
def application_success(request):
    return _success_response(
        request,
        _('Application Submitted'),
        _('Your application was submitted successfully.'),
        'manager_view_my_team', _('View My Team'),
        'manager_dashboard', _('Back to Manager Dashboard'))


@manager_required
def view_my_team(request):
    manager_id = request.session.get('manager_id')
    employment = Employ.objects.filter(licence_id=manager_id).first()

    if not employment:
        return render(request, 'manager_view_my_team.html', {'has_team': False})

    team = Team.objects.filter(team_api_id=employment.team_api_id).first()
    league = League.objects.filter(id=team.league_id).first() if team else None
    team_attr = TeamAttributes.objects.filter(
        team_api_id=employment.team_api_id).order_by('-date').first()

    players_with_attrs = []
    for player in Player.objects.filter(
            team_api_id=employment.team_api_id).order_by('player_name'):
        attrs = PlayerAttributes.objects.filter(
            player_fifa_api_id=player.player_fifa_api_id).order_by('-date').first()
        players_with_attrs.append({'player': player, 'attributes': attrs})

    return render(request, 'manager_view_my_team.html', {
        'has_team': True, 'team': team, 'team_attr': team_attr,
        'league_name': league.name if league else '',
        'players_with_attrs': players_with_attrs})


@manager_required
def manager_view_my_players(request):
    manager_id = request.session.get('manager_id')
    employment = Employ.objects.filter(licence_id=manager_id).first()

    if not employment:
        return render(request, 'manager_view_my_players.html', {'has_team': False})

    players = Player.objects.filter(
        team_api_id=employment.team_api_id).order_by('player_name')
    return render(request, 'manager_view_my_players.html', {
        'has_team': True, 'players': players})


# ---------------------------------------------------------------------------
# 足球经理：浏览全部球员 / 球员详情
# ---------------------------------------------------------------------------


@manager_required
def manager_view_all_players(request):
    league_id = request.GET.get('league_id')
    team_api_id = request.GET.get('team_api_id')
    search_query = request.GET.get('search_query')

    players = Player.objects.all()
    if league_id:
        team_ids = list(Team.objects.filter(league_id=league_id).values_list(
            'team_api_id', flat=True))
        players = players.filter(team_api_id__in=team_ids)
    if team_api_id:
        # 兜底：若提交的球队不属于当前所选联赛，说明是切换联赛时残留的旧参数，
        # 忽略它，避免出现"未找到匹配球员"的误报
        if league_id and not Team.objects.filter(
                league_id=league_id, team_api_id=team_api_id).exists():
            team_api_id = None
        if team_api_id:
            players = players.filter(team_api_id=team_api_id)
    if search_query:
        players = players.filter(player_name__icontains=search_query)
    players = players.order_by('player_name')

    # 队名映射，供模板 O(1) 查询，避免模板内两层循环
    team_name_by_id = {t.team_api_id: t.team_long_name for t in Team.objects.all()}
    teams = (Team.objects.filter(league_id=league_id).order_by('team_long_name')
             if league_id else Team.objects.all().order_by('team_long_name'))
    leagues = League.objects.all().order_by('name')

    # 分页：每页 50 条，避免一次性渲染上万行把页面拖慢
    paginator = Paginator(players, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_numbers = paginator.get_elided_page_range(
        page_obj.number, on_each_side=2, on_ends=1)

    # 分页链接需保留当前的联赛/球队/搜索筛选条件
    query_params = urlencode({k: v for k, v in {
        'league_id': league_id, 'team_api_id': team_api_id,
        'search_query': search_query,
    }.items() if v})

    return render(request, 'manager_view_all_players.html', {
        'players': page_obj,
        'page_numbers': page_numbers,
        'query_params': query_params,
        'has_players': paginator.count > 0,
        'leagues': leagues,
        'teams': teams,
        'team_name_by_id': team_name_by_id,
        'selected_league_id': league_id,
        'selected_team_api_id': team_api_id,
        'search_query': search_query,
    })


STAT_FIELDS = [
    ('Crossing', 'crossing'), ('Finishing', 'finishing'),
    ('Heading Accuracy', 'heading_accuracy'), ('Short Passing', 'short_passing'),
    ('Volleys', 'volleys'), ('Dribbling', 'dribbling'), ('Curve', 'curve'),
    ('Free Kick Accuracy', 'free_kick_accuracy'), ('Long Passing', 'long_passing'),
    ('Ball Control', 'ball_control'),
    ('Acceleration', 'acceleration'), ('Sprint Speed', 'sprint_speed'),
    ('Agility', 'agility'), ('Reactions', 'reactions'), ('Balance', 'balance'),
    ('Shot Power', 'shot_power'), ('Jumping', 'jumping'), ('Stamina', 'stamina'),
    ('Strength', 'strength'), ('Long Shots', 'long_shots'),
    ('Aggression', 'aggression'), ('Interceptions', 'interceptions'),
    ('Positioning', 'positioning'), ('Vision', 'vision'), ('Penalties', 'penalties'),
    ('Marking', 'marking'), ('Standing Tackle', 'standing_tackle'),
    ('Sliding Tackle', 'sliding_tackle'),
    ('GK Diving', 'gk_diving'), ('GK Handling', 'gk_handling'),
    ('GK Kicking', 'gk_kicking'), ('GK Positioning', 'gk_positioning'),
    ('GK Reflexes', 'gk_reflexes'),
]


def _player_detail(request, player_fifa_api_id, back_url, back_label):
    player = Player.objects.filter(player_fifa_api_id=player_fifa_api_id).first()
    if not player:
        return render(request, 'error_page.html', {'error_message': _('Player not found.')})
    attributes = PlayerAttributes.objects.filter(
        player_fifa_api_id=player_fifa_api_id).order_by('-date').first()
    stats = [(_(label), field) for label, field in STAT_FIELDS]
    return render(request, 'manager_view_player_details.html', {
        'player': player,
        'attributes': attributes,
        'stats': stats,
        'back_url': back_url,
        'back_label': back_label,
    })


@manager_required
def manager_view_player_details(request, player_fifa_api_id):
    return _player_detail(request, player_fifa_api_id, 'manager_view_my_players',
                          _('Back to My Players'))


@manager_required
def manager_view_player_attributes(request, player_fifa_api_id):
    return _player_detail(request, player_fifa_api_id, 'manager_view_all_players',
                          _('Back to All Players'))


@manager_required
def delete_success(request):
    return _success_response(
        request, _('Deleted'), _('The item was deleted successfully.'),
        'manager_view_interested_players', _('Back'))


# ---------------------------------------------------------------------------
# 足球经理：球员推荐
# ---------------------------------------------------------------------------


@csrf_exempt
@manager_required
def recommend_player_view(request):
    manager_id = request.session.get('manager_id')

    all_attributes = [
        'overall_rating', 'potential', 'crossing', 'finishing', 'heading_accuracy',
        'short_passing', 'volleys', 'dribbling', 'curve', 'free_kick_accuracy',
        'long_passing', 'ball_control', 'acceleration', 'sprint_speed', 'agility',
        'reactions', 'balance', 'shot_power', 'jumping', 'stamina', 'strength',
        'long_shots', 'aggression', 'interceptions', 'positioning', 'vision',
        'penalties', 'marking', 'standing_tackle', 'sliding_tackle',
    ]

    selected_attribute = request.GET.get('attribute')
    recommended_players = []
    message = ''
    avg_value = None
    valid_count = 0

    interested_player_ids = list(Interested.objects.filter(
        manager_id=manager_id).values_list('player_fifa_api_id', flat=True))

    if selected_attribute:
        followed_attrs = PlayerAttributes.objects.filter(
            player_fifa_api_id__in=interested_player_ids).exclude(
            **{selected_attribute: None})

        valid_values = []
        for attr in followed_attrs:
            try:
                valid_values.append(int(builtins.getattr(attr, selected_attribute)))
            except (ValueError, TypeError):
                continue

        if valid_values:
            avg_value = sum(valid_values) / len(valid_values)
            valid_count = len(valid_values)
            recommended_attrs = PlayerAttributes.objects.filter(
                **{f'{selected_attribute}__gte': avg_value - 5,
                   f'{selected_attribute}__lte': avg_value + 5}
            ).exclude(player_fifa_api_id__in=interested_player_ids)

            # 同一球员多日期快照去重，取一条
            attr_by_player = {}
            for attr in recommended_attrs:
                if attr.player_fifa_api_id not in attr_by_player:
                    attr_by_player[attr.player_fifa_api_id] = builtins.getattr(
                        attr, selected_attribute)

            players_map = {p.player_fifa_api_id: p for p in Player.objects.filter(
                player_fifa_api_id__in=list(attr_by_player.keys()))}
            recommended_players = [
                {'player': players_map[pid], 'attribute_value': val}
                for pid, val in attr_by_player.items() if pid in players_map
            ]
            recommended_players.sort(key=lambda x: x['player'].player_name)

            if not recommended_players:
                message = _('No matching players found.')
        else:
            message = _('Your interested players do not have valid data for this attribute.')

    if request.method == 'POST':
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        if player_fifa_api_id:
            Interested.objects.create(
                manager_id=manager_id, player_fifa_api_id=player_fifa_api_id)
            messages.success(request, _('Player added to your interested list.'))
            return redirect('manager_view_interested_players')

    # 分页：每页 50 条，避免一次渲染上千条推荐拖慢页面
    paginator = Paginator(recommended_players, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    page_numbers = paginator.get_elided_page_range(
        page_obj.number, on_each_side=2, on_ends=1)
    # 翻页时保留当前选择的属性
    query_params = urlencode({'attribute': selected_attribute}) if selected_attribute else ''

    return render(request, 'recommend_player.html', {
        'attributes': all_attributes,
        'selected_attribute': selected_attribute,
        'recommended_players': page_obj,
        'page_numbers': page_numbers,
        'query_params': query_params,
        'recommended_total': paginator.count,
        'message': message,
        'interested_count': len(interested_player_ids),
        'valid_count': valid_count,
        'avg_value': avg_value,
        'range_low': (avg_value - 5) if avg_value is not None else None,
        'range_high': (avg_value + 5) if avg_value is not None else None,
    })


@manager_required
def manager_squad_agent_view(request):
    manager_id = request.session.get('manager_id')
    query = request.GET.get('q', '').strip()
    agent_response = None

    if request.method == 'POST':
        player_fifa_api_id = request.POST.get('player_fifa_api_id')
        original_query = request.POST.get('q', '').strip()
        if player_fifa_api_id:
            if not Interested.objects.filter(
                    manager_id=manager_id,
                    player_fifa_api_id=player_fifa_api_id).exists():
                Interested.objects.create(
                    manager_id=manager_id,
                    player_fifa_api_id=player_fifa_api_id)
                messages.success(request, _('Player added to your interested list.'))
            else:
                messages.warning(request, _('This player is already in your interested list.'))
        redirect_url = 'manager_squad_agent'
        if original_query:
            return redirect(f"{redirect_url}?{urlencode({'q': original_query})}")
        return redirect(redirect_url)

    if query:
        agent_response = recommend_players_for_request(manager_id, query)

    return render(request, 'manager_squad_agent.html', {
        'query': query,
        'agent_response': agent_response,
    })


# 模板过滤器已迁移到 templatetags/custom_filters.py
