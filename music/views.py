from django.http import JsonResponse, HttpResponse
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from django.urls import reverse_lazy
from .models import Album, Song
from .forms import UserForm, SongForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib import messages

AUDIO_FILE_TYPES = ['wav', 'mp3', 'ogg']
IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']


class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'music/index.html'
    context_object_name = 'albums'
    login_url = '/music/login/'

    def get(self, request, *args, **kwargs):
        query = request.GET.get("q")
        print("Q" + str(query))
        albums = Album.objects.filter(user=self.request.user)
        if query:
            song_results = Song.objects.all()
            if query:
                albums = albums.filter(
                    Q(album_title__icontains=query) |
                    Q(artist__icontains=query)
                ).distinct()
                song_results = song_results.filter(
                    Q(song_title__icontains=query)
                ).distinct()
                return render(request, 'music/index.html', {
                    'albums': albums,
                    'searcher': True,
                    'songs': song_results,
                })
        else:
            return render(request, 'music/index.html', {
                'albums': albums,
            })

    def get_queryset(self):
        return Album.objects.filter(user=self.request.user.id)


class DetailView(LoginRequiredMixin, generic.DetailView):
    model = Album
    template_name = 'music/detail.html'
    login_url = '/music/login/'


class AlbumCreate(LoginRequiredMixin, CreateView):
    model = Album
    fields = ['artist', 'album_title', 'genre', 'album_logo']

    def form_valid(self, form):
        form.instance.user = self.request.user
        file_type = form.instance.album_logo.url.split('.')[-1]
        file_type = file_type.lower()
        form_error = form.errors
        if file_type not in IMAGE_FILE_TYPES:
            form_error['album_logo'] = "INVALID FILE SELECTED. FILE MUST HAVE EXTENSION OF ['.jpg', '.png', 'jpeg']"
            return super(AlbumCreate, self).form_invalid(form)
        return super(AlbumCreate, self).form_valid(form)


class AlbumUpdate(LoginRequiredMixin, UpdateView):
    model = Album
    fields = ['artist', 'album_title', 'genre', 'album_logo']
    login_url = '/music/login/'

    def form_valid(self, form):
        file_type = form.instance.album_logo.url.split('.')[-1]
        file_type = file_type.lower()
        form_error = form.errors
        if file_type not in IMAGE_FILE_TYPES:
            form_error['album_logo'] = "INVALID FILE SELECTED. FILE MUST HAVE EXTENSION OF ['.jpg', '.png', 'jpeg']"
            return super(AlbumUpdate, self).form_invalid(form)
        return super(AlbumUpdate, self).form_valid(form)


class AlbumDelete(DeleteView):
    model = Album
    success_url = reverse_lazy('music:index')
    login_url = '/music/login/'


class UserFormView(View):
    form_class = UserForm
    template_name = 'music/registration_form.html'

    # display blank form
    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # process form data
    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            # clean/normalised data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()

            # returns user object if credentials are correct
            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('music:index')

        return render(request, self.template_name, {'form': form})


def add_song(request, album_id):
    if not request.user.is_authenticated:
        return redirect('music:login_user')
    else:
        form = SongForm(request.POST or None, request.FILES or None)
        album = get_object_or_404(Album, pk=album_id)
        if form.is_valid():
            albums_songs = album.song_set.all()
            for s in albums_songs:
                if s.song_title == form.cleaned_data.get("song_title"):
                    context = {
                        'album': album,
                        'form': form,
                        'error_message': 'You already added that song',
                    }
                    return render(request, 'music/add_song.html', context)
            song = form.save(commit=False)
            song.album = album
            song.audio_file = request.FILES['audio_file']
            file_type = song.audio_file.url.split('.')[-1]
            file_type = file_type.lower()

            if file_type not in AUDIO_FILE_TYPES:
                context = {
                    'album': album,
                    'form': form,
                    'error_message': 'Audio file must be WAV, MP3, or OGG',
                }
                return render(request, 'music/add_song.html', context)

            song.save()
            return render(request, 'music/detail.html', {'album': album})
        context = {
            'album': album,
            'form': form,
        }
        return render(request, 'music/add_song.html', context)


def delete_song(request, album_id, song_id):
    if not request.user.is_authenticated:
        return redirect('music:login_user')
    else:
        album = get_object_or_404(Album, pk=album_id)
        song = Song.objects.get(pk=song_id)
        song.delete()
        return redirect('music:detail', album.pk)


def songs(request, filter_by):
    if not request.user.is_authenticated:
        return redirect('music:login_user')
    else:
        try:
            song_ids = []
            for album in Album.objects.filter(user=request.user):
                for song in album.song_set.all():
                    song_ids.append(song.pk)
            users_songs = Song.objects.filter(pk__in=song_ids)
            if filter_by == 'favorites':
                users_songs = users_songs.filter(is_favorite=True)
        except Album.DoesNotExist:
            users_songs = []
        return render(request, 'music/songs.html', {
            'song_list': users_songs,
            'filter_by': filter_by,
        })


def login_user(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                albums = Album.objects.filter(user=request.user)
                return redirect('music:index')
            else:
                return render(request, 'music/login.html', {'error_message': 'Your account has been disabled'})
        else:
            return render(request, 'music/login.html', {'error_message': 'Invalid login'})
    return render(request, 'music/login.html')


def logout_user(request):
    logout(request)
    return redirect('home_page')


def favorite_song(request, song_id):
    song = get_object_or_404(Song, pk=song_id)
    current_url = request.resolver_match.view_name
    print(current_url)
    try:
        if song.is_favorite:
            song.is_favorite = False
        else:
            song.is_favorite = True
        song.save()
    except (KeyError, Song.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})


def favorite_album(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    try:
        if album.is_favorite:
            album.is_favorite = False
        else:
            album.is_favorite = True
        album.save()
    except (KeyError, Album.DoesNotExist):
        return JsonResponse({'success': False})
    else:
        return JsonResponse({'success': True})
