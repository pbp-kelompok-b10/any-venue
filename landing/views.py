from django.shortcuts import render

# Create your views here.

def show_main(request):
    return render(request, "hello_world.html")

def features_preview(request):
    return render(request, "sections/features_preview.html")

def header_test(request):
    return render(request, "sections/header.html")
