import json
from django.forms import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from account.models import Profile 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt 
from django.contrib.auth.password_validation import validate_password
import re

@csrf_exempt
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        is_owner = request.POST.get("is_owner") == "true"

        # Validasi basic
        if not username or not password1 or not password2:
            return JsonResponse({"success": False, "error": "All fields are required."})

        if password1 != password2:
            return JsonResponse({"success": False, "error": "Passwords do not match."})

        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "error": "Username already taken."})

        # Username validation (like Django's built-in)
        if len(username) > 150:
            return JsonResponse({"success": False, "error": "Username cannot exceed 150 characters."})
        if not re.match(r"^[\w.@+-]+$", username):
            return JsonResponse({"success": False, "error": "Username may contain only letters, digits, and @/./+/-/_ characters."})
        
         # Username-password similarity checks FIRST
        if password1 == username:
            return JsonResponse({"success": False, "error": "Password is too similar to the username."})    

        if username.lower() in password1.lower() or password1.lower() in username.lower():
            return JsonResponse({"success": False, "error": "Password cannot contain or be contained in the username."})

        # Common passwords check
        if password1 in ['password', '12345678']:
            return JsonResponse({"success": False, "error": "This password is too common."})

        # Basic length check
        if len(password1) < 8:
            return JsonResponse({"success": False, "error": "Password must be at least 8 characters long."})

        # Use Django's built-in validators (strongness, etc.)
        try:
            validate_password(password1)
        except ValidationError as e:
            return JsonResponse({"success": False, "error": " ".join(e.messages)})

        
        # Create user
        user = User.objects.create_user(username=username, password=password1)
        profile = user.profile  # auto dibuat lewat signal
        profile.role = 'OWNER' if is_owner else 'USER'
        profile.save()

        return JsonResponse({"success": True, "message": "Account created successfully!"})

    return render(request, "register.html")

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({"success": True, "message": "Login berhasil"})
        else:
            return JsonResponse({"success": False, "message": "Username atau password salah"})
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    # Check if request is AJAX by looking at HTTP_X_REQUESTED_WITH header
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "message": "Logout berhasil"})
    return redirect("landing:show_landing")

@csrf_exempt
def api_register_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        username = data.get("username")
        password1 = data.get("password1")
        password2 = data.get("password2")
        is_owner = data.get("is_owner") == "true"

        # Validasi basic
        if not username or not password1 or not password2:
            return JsonResponse({"success": False, "error": "All fields are required."}, status=400)

        if password1 != password2:
            return JsonResponse({"success": False, "error": "Passwords do not match."}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "error": "Username already taken."}, status=409)

        # Username validation (like Django's built-in)
        if len(username) > 150:
            return JsonResponse({"success": False, "error": "Username cannot exceed 150 characters."}, status=400)
        if not re.match(r"^[\w.@+-]+$", username):
            return JsonResponse({"success": False, "error": "Username may contain only letters, digits, and @/./+/-/_ characters."}, status=400)
        
         # Username-password similarity checks FIRST
        if password1 == username:
            return JsonResponse({"success": False, "error": "Password is too similar to the username."}, status=400)    

        if username.lower() in password1.lower() or password1.lower() in username.lower():
            return JsonResponse({"success": False, "error": "Password cannot contain or be contained in the username."}, status=400)

        # Common passwords check
        if password1 in ['password', '12345678']:
            return JsonResponse({"success": False, "error": "This password is too common."}, status=400)

        # Basic length check
        if len(password1) < 8:
            return JsonResponse({"success": False, "error": "Password must be at least 8 characters long."}, status=400)

        # Use Django's built-in validators (strongness, etc.)
        try:
            validate_password(password1)
        except ValidationError as e:
            return JsonResponse({"success": False, "error": " ".join(e.messages)}, status=400)

        
        # Create user
        user = User.objects.create_user(username=username, password=password1)
        profile = user.profile  # auto dibuat lewat signal
        profile.role = 'OWNER' if is_owner else 'USER'
        profile.save()

        return JsonResponse({"success": True, "message": "Account created successfully!"}, status=201)

    return render(request, "register.html")

@csrf_exempt
def api_login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                "username": user.username,
                "status": True,
                "message": "Login successful!"
                # Add other data if you want to send data to Flutter.
            }, status=200)
        else:
            return JsonResponse({"success": False, "message": "Username atau password salah"}, status=401)
    return render(request, "login.html")

def api_logout_view(request):
    logout(request)
    # Check if request is AJAX by looking at HTTP_X_REQUESTED_WITH header
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "message": "Logout berhasil"})
    return redirect("landing:show_landing")