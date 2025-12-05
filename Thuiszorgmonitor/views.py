from random import randint
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .forms import CustomUserCreationForm, UserUpdateForm

from Thuiszorgmonitor.models import Heartbeat


def live_chart(request):
    return render(request, 'live-graph.html')

def show_heartbeat(request):
    heartbeat = randint(55,75)
    template = loader.get_template("index.html")
    context = {"heartbeat": heartbeat}
    return HttpResponse(template.render(context, request))

def check_heartbeat(request):
    return "New heartbeat " + str(show_heartbeat(request))
# Create your views here.

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')  # Verwijs naar de loginpagina na registratie
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')  # Verwijs naar de homepagina na inloggen
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def home(request):
    return render(request, 'home.html')

def calculate_max_heart_rate(age):
    """Bereken de maximale hartslag op basis van de leeftijd."""
    return round(206.9 - (0.67 * age))


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth.decorators import login_required

@login_required
def is_heartbeat_ok(request, heartbeat):
    # Get the user's age
    user = request.user
    age = user.age

    # Call the function
    max_heartbeat = round(206.9 - (0.67 * age))

    # Check for errors
    if heartbeat > max_heartbeat or heartbeat < 40:
        return True

    return False
@login_required  # Zorgt ervoor dat alleen ingelogde gebruikers toegang hebben

def home(request):
    user = request.user  # Huidige ingelogde gebruiker
    age = user.age  # Leeftijd van de gebruiker (van het CustomUser model)
    name = user.username

    max_heart_rate = calculate_max_heart_rate(age)  # Bereken maximale hartslag

    heart_rate = randint(55,75)  # Om de hartslag die de gebruiker invoert te bewaren

    if request.method == 'POST':
        # We gaan er hier vanuit dat de gebruiker de hartslag invoert via een POST-verzoek
        heart_rate = int(request.POST.get('heartbeat'))  # Haal de hartslag op uit het formulier
        if heart_rate> max_heart_rate:
            messages.warning(request, 'Warning: You have exceeded your maximum heart rate! Please contact your doctor!')
        elif heart_rate < 40:
            messages.warning(request, "Warning: Your heartrate is dangerously low, please contact your doctor.")
        else:
            messages.success(request, 'Your heart rate is within the safe range.')


    context = {
        'heart_rate': heart_rate,
        'max_heart_rate': max_heart_rate,
        'name': name,
    }

    return render(request, 'home.html', context)

def account_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('Account')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'Account.html', {'form': form})


