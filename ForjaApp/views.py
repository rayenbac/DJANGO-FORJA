from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm, RatingForm
from django.contrib.auth.decorators import login_required
from .utils import get_similar_movies
from .models import Recommendation, Movie, Rating, WatchLater
from django.db.models import Avg
import re

def index(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Votre compte a été créé avec succès !')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Vous êtes connecté !')
                return redirect('index')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté.')
    return redirect('login')

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

@login_required
def recommend_similar_movies(request):
    similar_movies = []
    movie_title = ""

    if request.method == 'POST':
        movie_title = request.POST.get('movie_title')

        # Obtenir les films similaires à l'aide de l'algorithme optimisé
        similar_movies = get_similar_movies(movie_title)

        # Vérifier si le film est trouvé dans la base de données
        movie = Movie.objects.filter(title__icontains=movie_title).first()

        # Si le film n'est pas trouvé, l'ajouter à la base de données
        if not movie and similar_movies:  # Vérifiez qu'il y a des films similaires
            movie_data = similar_movies[0]  # Prenons le premier film similaire
            movie = Movie(
                title=movie_data['title'],
                release_date=movie_data['release_date'],
                overview=movie_data['overview'],
                poster_path=movie_data['poster_path']
            )
            movie.save()  # Sauvegarder le nouveau film dans la base de données

        # Si le film est trouvé ou a été ajouté, enregistrer la recommandation
        if movie:
            Recommendation.objects.create(
                user=request.user,
                movie=movie,
                similar_movies=[{"title": m['title'], "id": m['id']} for m in similar_movies]  # Enregistrer les titres et IDs des films similaires
            )

        return render(request, 'recommendations.html', {'similar_movies': similar_movies, 'movie_title': movie_title})

    return render(request, 'recommendations.html', {'similar_movies': similar_movies, 'movie_title': movie_title})

def generate_image(request):
    image_url = None
    error_message = None

    if request.method == 'POST':
        description = request.POST.get('description')

        # Liste de mots-clés associés aux films
        movie_keywords = ['film', 'movie', 'character', 'plot', 'scene', 'actor', 'actress', 'director', 'genre', 'cinema', 'trailer']

        # Vérifier si la description contient des mots-clés de film
        if any(re.search(r'\b' + keyword + r'\b', description, re.IGNORECASE) for keyword in movie_keywords):
            image_url = f"https://image.pollinations.ai/prompt/{description}"
        else:
            error_message = "Veuillez entrer une description liée aux films."

    return render(request, 'image_generator.html', {'image_url': image_url, 'error_message': error_message})

@login_required
def rate_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    
    ratings = Rating.objects.filter(movie=movie).order_by('-date_rated')
    
    user_rating = Rating.objects.filter(movie=movie, user=request.user).first()

    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            # Save or update the user's rating
            if user_rating:
                user_rating.score = form.cleaned_data['score']
                user_rating.review = form.cleaned_data['review']
                user_rating.save()
            else:
                rating = form.save(commit=False)
                rating.movie = movie
                rating.user = request.user  
                rating.save()

            # Handle Watch Later checkbox
            if 'watch_later' in request.POST:
                # Add movie to Watch Later
                WatchLater.objects.get_or_create(user=request.user, movie=movie)
            else:
                # Remove movie from Watch Later
                WatchLater.objects.filter(user=request.user, movie=movie).delete()

            return redirect('rate_movie', movie_id=movie.id)  
    else:
        form = RatingForm() if not user_rating else None  

    return render(request, 'rate_movie.html', {
        'movie': movie,
        'form': form,
        'ratings': ratings,
        'user_rating': user_rating,
    })

def movie_list(request):
    movies = Movie.objects.annotate(average_rating=Avg('rating__score'))
    return render(request, 'movie_list.html', {'movies': movies})
