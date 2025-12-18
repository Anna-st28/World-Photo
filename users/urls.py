from django.urls import path, include
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('specialists/', views.specialists, name='specialists'),
    path('specialists/<int:pk>/', views.photographer_detail, name='photographer_detail'),
    path('specialists/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('news/', views.news, name='news'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('gallery/', views.gallery, name='gallery'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/delete-image/', views.delete_profile_image, name='delete_profile_image'),
    path('', include('django.contrib.auth.urls')),
]

