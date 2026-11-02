from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("mot-de-passe/", auth_views.PasswordChangeView.as_view(template_name="registration/password_change.html", success_url="/etudiant/espace/"), name="password_change"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("students.urls")),
]
