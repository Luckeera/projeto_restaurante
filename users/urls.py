from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from restaurante import views
from .forms import EmailAuthenticationForm 

urlpatterns = [
    path(
        "login/", auth_views.LoginView.as_view(
            template_name="users/login.html",
            authentication_form=EmailAuthenticationForm # Adicione esta linha
        ), 
        name="login"
    ),
    path('logout/', LogoutView.as_view(next_page='cardapio'), name='logout'),
    path("registrar/", views.register, name="register"),
]
