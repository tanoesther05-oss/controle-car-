from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("inscription/", views.register, name="register"),
    path("espace/", views.dashboard, name="dashboard"),
    path("etudiant/connexion/", views.student_login, name="student_login"),
    path("etudiant/espace/", views.student_space, name="student_space"),
    path("etudiants/", views.student_list, name="student_list"),
    path("etudiants/ajouter/", views.student_create, name="student_create"),
    path("etudiants/<int:pk>/", views.student_detail, name="student_detail"),
    path("etudiants/<int:pk>/modifier/", views.student_edit, name="student_edit"),
    path("etudiants/<int:pk>/supprimer/", views.student_delete, name="student_delete"),
    path("licence/<slug:slug>/", views.level_list, name="level_list"),
    path("communes/", views.communes, name="communes"),
    path("import/", views.import_page, name="import_page"),
    path("export.csv", views.export_csv, name="export_csv"),
]
