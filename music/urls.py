from django.urls import path
from . import views

app_name = 'music'

urlpatterns = [
    # /music/
    path('', views.IndexView.as_view(), name="index"),

    # /music/<album_id>/
    path('<int:pk>/', views.DetailView.as_view(), name="detail"),

    # /music/album/add/
    path('album/add', views.AlbumCreate.as_view(), name="album-add"),

    # /music/album/<album_id>/
    path('album/<int:pk>/', views.AlbumUpdate.as_view(), name="album-update"),

    # /music/album/<album_id>/delete/
    path('album/<int:pk>/delete/', views.AlbumDelete.as_view(), name="album-delete"),

    # /music/register/
    path('register/', views.UserFormView.as_view(), name="register"),

    # /music/<album_id>/add_songs/
    path('<int:album_id>/add_songs/', views.add_song, name='song-add'),

    # /music/<album_id>/delete_song/<song_id>/
    path('<int:album_id>/delete_song/<int:song_id>', views.delete_song, name='song-delete'),

    # /music/songs/<filter_by>/
    path('songs/<filter_by>/', views.songs, name='songs'),

    # /music/login/
    path('login/', views.login_user, name='login_user'),

    # /music/logout/
    path('logout/', views.logout_user, name='logout_user'),

    # /music/<song_id>/favorite/
    path('<int:song_id>/favorite/', views.favorite_song, name='favorite'),

    # /music/<album_id>/favorite_album/
    path('<int:album_id>/favorite_album/', views.favorite_album, name='favorite_album'),

]
