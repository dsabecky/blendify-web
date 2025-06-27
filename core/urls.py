from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('blend/', views.blend, name='blend'),
    path('lorumipsum/', views.lorumipsum, name='lorumipsum'),
    path('get_playlist_themes/', views.get_playlist_themes, name='get_playlist_themes'),
    path('hathor/', views.hathor, name='hathor')
]