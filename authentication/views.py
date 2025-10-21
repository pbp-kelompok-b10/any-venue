from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from user.models import Profile 
from django.http import JsonResponse

def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        role = request.POST["role"]  # ambil role dari form

        if User.objects.filter(username=username).exists():
             return JsonResponse({"success": False, "message": "Username already taken"})

        # buat user baru
        user = User.objects.create_user(username=username, password=password)
        user.save()

        # update role profile (signal create otomatis sudah bikin profile)
        user.profile.role = role
        user.profile.save()

        return JsonResponse({"success": True, "message": "Account created successfully!"})

    return render(request, "register.html")

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
    if request.is_ajax():
        return JsonResponse({"success": True, "message": "Logout berhasil"})
    return redirect("login")