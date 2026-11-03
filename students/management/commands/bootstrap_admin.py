import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée ou met à jour le compte administrateur défini par les variables Render."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()

        if not username or not password:
            self.stdout.write("Compte administrateur automatique non configuré.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        action = "créé" if created else "mis à jour"
        self.stdout.write(self.style.SUCCESS(f"Compte administrateur {action} : {username}"))
