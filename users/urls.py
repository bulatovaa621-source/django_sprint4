from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('registration/', views.registration, name='registration'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='users_profile'),
]
