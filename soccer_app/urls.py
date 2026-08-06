from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.custom_login_view, name='custom_login'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('follow_team/', views.follow_team_view, name='follow_team'),    
    path('follow_player/', views.follow_player_view, name='follow_player'),
    path('view_followed_teams/', views.view_followed_teams, name='view_followed_teams'),
    path('view_followed_players/', views.view_followed_players, name='view_followed_players'),
    path('view_followed_matches/', views.view_followed_matches, name='view_followed_matches'),
    path('unfollow_team/', views.unfollow_team_view, name='unfollow_team'),
    path('unfollow_player/', views.unfollow_player_view, name='unfollow_player'),
    path('recommend_team/', views.recommend_team_view, name='recommend_team'),
    path('guess_player/', views.guess_player_view, name='guess_player'),
    path('logout/', views.logout_view, name='logout'),
    ###经理人
    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager_follow_player/', views.manager_follow_player_view, name='manager_follow_player'),
    path('manager_view_interested_players/', views.manager_view_interested_players, name='manager_view_interested_players'),
    path('manager_check_employment/',views.check_employment, name='manager_check_employment'),
    path('manager_view_my_team/', views.view_my_team, name='manager_view_my_team'),
    path('application_success/', views.application_success, name='application_success'),  # 添加应聘成功页面路由
    path('manager_view_all_players/', views.manager_view_all_players, name='manager_view_all_players'),
    path('manager_view_player_attributes/<int:player_fifa_api_id>/', views.manager_view_player_attributes, name='manager_view_player_attributes'),
    path('manager_view_my_players/', views.manager_view_my_players, name='manager_view_my_players'),
    path('manager_view_player_details/<int:player_fifa_api_id>/', views.manager_view_player_details, name='manager_view_player_details'),
    path('manager_delete_interested_player/<int:player_fifa_api_id>/', views.manager_delete_interested_player, name='manager_delete_interested_player'),
    path('delete_success/', views.delete_success, name='delete_success'),  # 添加删除成功页面
    path('recommend_player/', views.recommend_player_view, name='recommend_player_view'),
]
