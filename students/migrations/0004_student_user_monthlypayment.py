from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("students", "0003_add_licence_3_and_gare"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(
            model_name="student",
            name="user",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="student_profile", to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name="MonthlyPayment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("month", models.PositiveSmallIntegerField(choices=[(12, "Décembre"), (1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"), (5, "Mai"), (6, "Juin"), (7, "Juillet")])),
                ("paid", models.BooleanField(default=False, verbose_name="Payé")),
                ("paid_at", models.DateField(blank=True, null=True, verbose_name="Date du paiement")),
                ("note", models.CharField(blank=True, max_length=200, verbose_name="Note")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="students.student")),
            ],
            options={"ordering": ["month"]},
        ),
        migrations.AddConstraint(model_name="monthlypayment", constraint=models.UniqueConstraint(fields=("student", "month"), name="unique_student_payment_month")),
    ]
