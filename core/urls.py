from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("explore/", views.explore, name="explore"),
    path("issue/<int:pk>/", views.issue_detail, name="issue_detail"),
    path("u/<str:username>/", views.profile_view, name="profile"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]
