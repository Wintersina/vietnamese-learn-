from django.urls import path

from . import views

app_name = "learning"

urlpatterns = [
    path("", views.home, name="home"),
    path("study/<slug:slug>/", views.study, name="study"),
    path("study/<slug:slug>/review/<int:card_id>/", views.review, name="review"),
    path("match/<slug:slug>/", views.match, name="match"),
    path("match/<slug:slug>/grade/", views.match_grade, name="match_grade"),
    path("audio/<int:card_id>/", views.card_audio, name="card_audio"),
]
