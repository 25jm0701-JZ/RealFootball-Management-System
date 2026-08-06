# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Country(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'country'


class Employ(models.Model):
    licence_id = models.IntegerField(primary_key=True)
    team_api_id = models.IntegerField(blank=True, null=True)
    id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employ'


class Follow(models.Model):
    player_fifa_api_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'follow'


class FootballManager(models.Model):
    licence_id = models.IntegerField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'football_manager'


class Interested(models.Model):
    manager = models.ForeignKey(FootballManager, on_delete=models.CASCADE, db_column='licence_id')
    player_fifa_api_id = models.IntegerField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'interested'


class League(models.Model):
    id = models.IntegerField(primary_key=True)
    country_id = models.IntegerField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'league'


class ManagerAccount(models.Model):
    licence_id = models.IntegerField(blank=True, null=True)
    username = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'manager_account'


class Match(models.Model):
    id = models.IntegerField(primary_key=True)
    season = models.TextField(blank=True, null=True)
    stage = models.IntegerField(blank=True, null=True)
    date = models.TextField(blank=True, null=True)
    match_api_id = models.IntegerField(blank=True, null=True)
    home_team_api_id = models.IntegerField(blank=True, null=True)
    away_team_api_id = models.IntegerField(blank=True, null=True)
    home_team_goal = models.IntegerField(blank=True, null=True)
    away_team_goal = models.IntegerField(blank=True, null=True)
    league_id = models.IntegerField(blank=True, null=True)
    shoton1 = models.IntegerField(blank=True, null=True)
    shoton2 = models.IntegerField(blank=True, null=True)
    shotoff1 = models.IntegerField(blank=True, null=True)
    shotoff2 = models.IntegerField(blank=True, null=True)
    foulcommit1 = models.IntegerField(blank=True, null=True)
    foulcommit2 = models.IntegerField(blank=True, null=True)
    card1 = models.IntegerField(blank=True, null=True)
    card2 = models.IntegerField(blank=True, null=True)
    cross1 = models.IntegerField(blank=True, null=True)
    cross2 = models.IntegerField(blank=True, null=True)
    corner1 = models.IntegerField(blank=True, null=True)
    corner2 = models.IntegerField(blank=True, null=True)
    possession1 = models.IntegerField(blank=True, null=True)
    possession2 = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'match'


class Player(models.Model):
    id = models.IntegerField(blank=True, null=True)
    player_api_id = models.IntegerField(blank=True, null=True)
    player_name = models.TextField(blank=True, null=True)
    player_fifa_api_id = models.IntegerField(primary_key=True)
    birthday = models.TextField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True)
    league_id = models.IntegerField(blank=True, null=True)
    team_api_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'player'


class PlayerAttributes(models.Model):
    id = models.IntegerField(primary_key=True)
    player_fifa_api_id = models.IntegerField(blank=True, null=True)
    player_api_id = models.IntegerField(blank=True, null=True)
    date = models.TextField(blank=True, null=True)
    overall_rating = models.TextField(blank=True, null=True)
    potential = models.TextField(blank=True, null=True)
    preferred_foot = models.TextField(blank=True, null=True)
    attacking_work_rate = models.TextField(blank=True, null=True)
    defensive_work_rate = models.TextField(blank=True, null=True)
    crossing = models.TextField(blank=True, null=True)
    finishing = models.TextField(blank=True, null=True)
    heading_accuracy = models.TextField(blank=True, null=True)
    short_passing = models.TextField(blank=True, null=True)
    volleys = models.TextField(blank=True, null=True)
    dribbling = models.TextField(blank=True, null=True)
    curve = models.TextField(blank=True, null=True)
    free_kick_accuracy = models.TextField(blank=True, null=True)
    long_passing = models.TextField(blank=True, null=True)
    ball_control = models.TextField(blank=True, null=True)
    acceleration = models.TextField(blank=True, null=True)
    sprint_speed = models.TextField(blank=True, null=True)
    agility = models.TextField(blank=True, null=True)
    reactions = models.TextField(blank=True, null=True)
    balance = models.TextField(blank=True, null=True)
    shot_power = models.TextField(blank=True, null=True)
    jumping = models.TextField(blank=True, null=True)
    stamina = models.TextField(blank=True, null=True)
    strength = models.TextField(blank=True, null=True)
    long_shots = models.TextField(blank=True, null=True)
    aggression = models.TextField(blank=True, null=True)
    interceptions = models.TextField(blank=True, null=True)
    positioning = models.TextField(blank=True, null=True)
    vision = models.TextField(blank=True, null=True)
    penalties = models.TextField(blank=True, null=True)
    marking = models.TextField(blank=True, null=True)
    standing_tackle = models.TextField(blank=True, null=True)
    sliding_tackle = models.TextField(blank=True, null=True)
    gk_diving = models.TextField(blank=True, null=True)
    gk_handling = models.TextField(blank=True, null=True)
    gk_kicking = models.TextField(blank=True, null=True)
    gk_positioning = models.TextField(blank=True, null=True)
    gk_reflexes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'player_attributes'


class Subscribe(models.Model):
    team_api_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'subscribe'


class Team(models.Model):
    id = models.IntegerField(blank=True, null=True)
    team_api_id = models.IntegerField(primary_key=True)
    team_long_name = models.TextField(blank=True, null=True)
    team_short_name = models.TextField(blank=True, null=True)
    league_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'team'


class TeamAttributes(models.Model):
    id = models.IntegerField(primary_key=True)
    team_fifa_api_id = models.IntegerField(blank=True, null=True)
    team_api_id = models.IntegerField(blank=True, null=True)
    date = models.TextField(blank=True, null=True)
    buildupplayspeed = models.IntegerField(db_column='buildUpPlaySpeed', blank=True, null=True)  # Field name made lowercase.
    buildupplayspeedclass = models.TextField(db_column='buildUpPlaySpeedClass', blank=True, null=True)  # Field name made lowercase.
    buildupplaydribbling = models.IntegerField(db_column='buildUpPlayDribbling', blank=True, null=True)  # Field name made lowercase.
    buildupplaydribblingclass = models.TextField(db_column='buildUpPlayDribblingClass', blank=True, null=True)  # Field name made lowercase.
    buildupplaypassing = models.IntegerField(db_column='buildUpPlayPassing', blank=True, null=True)  # Field name made lowercase.
    buildupplaypassingclass = models.TextField(db_column='buildUpPlayPassingClass', blank=True, null=True)  # Field name made lowercase.
    buildupplaypositioningclass = models.TextField(db_column='buildUpPlayPositioningClass', blank=True, null=True)  # Field name made lowercase.
    chancecreationpassing = models.IntegerField(db_column='chanceCreationPassing', blank=True, null=True)  # Field name made lowercase.
    chancecreationpassingclass = models.TextField(db_column='chanceCreationPassingClass', blank=True, null=True)  # Field name made lowercase.
    chancecreationcrossing = models.IntegerField(db_column='chanceCreationCrossing', blank=True, null=True)  # Field name made lowercase.
    chancecreationcrossingclass = models.TextField(db_column='chanceCreationCrossingClass', blank=True, null=True)  # Field name made lowercase.
    chancecreationshooting = models.IntegerField(db_column='chanceCreationShooting', blank=True, null=True)  # Field name made lowercase.
    chancecreationshootingclass = models.TextField(db_column='chanceCreationShootingClass', blank=True, null=True)  # Field name made lowercase.
    chancecreationpositioningclass = models.TextField(db_column='chanceCreationPositioningClass', blank=True, null=True)  # Field name made lowercase.
    defencepressure = models.IntegerField(db_column='defencePressure', blank=True, null=True)  # Field name made lowercase.
    defencepressureclass = models.TextField(db_column='defencePressureClass', blank=True, null=True)  # Field name made lowercase.
    defenceaggression = models.IntegerField(db_column='defenceAggression', blank=True, null=True)  # Field name made lowercase.
    defenceaggressionclass = models.TextField(db_column='defenceAggressionClass', blank=True, null=True)  # Field name made lowercase.
    defenceteamwidth = models.IntegerField(db_column='defenceTeamWidth', blank=True, null=True)  # Field name made lowercase.
    defenceteamwidthclass = models.TextField(db_column='defenceTeamWidthClass', blank=True, null=True)  # Field name made lowercase.
    defencedefenderlineclass = models.TextField(db_column='defenceDefenderLineClass', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'team_attributes'


class User(models.Model):
    user_id = models.IntegerField()
    name = models.TextField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'user'


class UserAccount(models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    username = models.TextField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    id = models.IntegerField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'user_account'

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


# Ordinary User Authentication Manager
class UserAccountManager(BaseUserManager):
    def create_user(self, username, password=None):
        user = self.model(username=username)
        user.set_password(password)
        return user


class UserAccountUser(AbstractBaseUser):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField(blank=True, null=True)
    username = models.TextField(unique=True)
    password = models.TextField()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserAccountManager()

    class Meta:
        managed = False
        db_table = 'user_account'


# 足球经理认证管理器
class ManagerAccountManager(BaseUserManager):
    def create_user(self, username, password=None):
        user = self.model(username=username)
        user.set_password(password)
        return user


class ManagerAccountUser(AbstractBaseUser):
    id = models.IntegerField(primary_key=True)
    licence_id = models.IntegerField(blank=True, null=True)
    username = models.TextField(unique=True)
    password = models.TextField()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = ManagerAccountManager()

    class Meta:
        managed = False
        db_table = 'manager_account'