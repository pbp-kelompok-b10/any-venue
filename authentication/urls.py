from django.urls import path
from . import views
from authentication.views import register_view, login_view, logout_view, api_register_view, api_login_view, logout_flutter

app_name = 'authentication'

urlpatterns = [
    path("register/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("api/register/", api_register_view, name="api_register"),
    path("api/login/", api_login_view, name="api_login"),
    path("api/logout/", views.logout_flutter, name="logout_flutter"),
]
