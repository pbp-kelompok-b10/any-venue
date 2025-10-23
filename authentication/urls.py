from django.urls import path
from . import views
from authentication.views import register_view, login_view, logout_view

app_name = 'authentication'

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]
