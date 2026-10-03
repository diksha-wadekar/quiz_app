from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('questions/', views.question_list, name='question_list'),
    path('questions/add/', views.question_create, name='question_create'),
    path('questions/<int:pk>/edit/', views.question_update, name='question_update'),
    path('questions/<int:pk>/delete/', views.question_delete, name='question_delete'),
    path('quiz/', views.quiz_start, name='quiz_start'),
    path('quiz/take/', views.quiz_take, name='quiz_take'),
    path('quiz/result/<int:pk>/', views.quiz_result, name='quiz_result'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]