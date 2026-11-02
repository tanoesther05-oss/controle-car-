import csv, unicodedata
from collections import Counter
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import RegistrationForm, StudentForm
from .models import ALLOWED_COMMUNES, MonthlyPayment, Student, StudyLevel, Program, SyncLog
from .services import import_csv, import_google_sheet

def home(request):
    return render(request, "home.html")

admin_required = user_passes_test(lambda user: user.is_authenticated and user.is_staff, login_url="login")

def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data["username"]
        user = User.objects.create_user(username=username, first_name=form.cleaned_data["first_names"], last_name=form.cleaned_data["last_name"], password=form.cleaned_data["password1"])
        student = form.save(commit=False)
        student.user = user
        student.bus_choice = form.cleaned_data["bus_choice"]
        student.submitted_at = timezone.now()
        student.save()
        for month, _label in MonthlyPayment.MONTHS:
            MonthlyPayment.objects.create(student=student, month=month)
        return render(request, "registration/success.html", {"student": student, "username": username})
    levels = list(StudyLevel.objects.prefetch_related("programs").all())
    level_data = [{"pk": level.pk, "slug": level.slug, "programs": [{"pk": p.pk, "name": p.name} for p in level.programs.all()]} for level in levels]
    return render(request, "registration/register.html", {"form": form, "levels": level_data})

def accent_key(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value or "").casefold() if not unicodedata.combining(c))

def filtered_students(request):
    qs = Student.objects.select_related("level", "program").all()
    term = request.GET.get("q", "").strip()
    for token in term.split():
        qs = qs.filter(Q(last_name__icontains=token) | Q(first_names__icontains=token))
    for param, field in [("commune", "commune"), ("level", "level_id"), ("program", "program_id"), ("bus", "bus_choice")]:
        val = request.GET.get(param)
        if val: qs = qs.filter(**{field: val})
    order = request.GET.get("order", "alpha")
    if order == "recent": qs = qs.order_by("-submitted_at", "last_name", "first_names")
    elif order == "name_desc": qs = qs.order_by("-last_name", "-first_names")
    else: qs = sorted(qs, key=lambda s: (accent_key(s.last_name), accent_key(s.first_names)))
    return qs

@admin_required
def dashboard(request):
    students = Student.objects.select_related("level", "program")
    total = students.count()
    yes = students.filter(bus_choice="yes").count()
    no = students.filter(bus_choice="no").count()
    review = total - yes - no
    levels = list(StudyLevel.objects.annotate(count=Count("students")))
    programs = list(Program.objects.select_related("level").annotate(count=Count("students")))
    interested_programs = list(Program.objects.select_related("level").annotate(count=Count("students", filter=Q(students__bus_choice="yes"))))
    municipalities = list(students.values("commune").annotate(total=Count("id"), interested=Count("id", filter=Q(bus_choice="yes"))).order_by("-interested")[:12])
    logs = SyncLog.objects.order_by("-started_at")[:1]
    return render(request, "students/dashboard.html", { "total": total, "yes": yes, "no": no, "review": review,
        "pct": round(yes * 100 / total) if total else 0, "levels": levels, "programs": programs, "interested_programs": interested_programs,
        "municipalities": municipalities, "last_sync": logs.first() })

def student_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard" if request.user.is_staff else "student_space")
    form = __import__("django.contrib.auth.forms", fromlist=["AuthenticationForm"]).AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if user.is_staff:
            auth_login(request, user)
            return redirect("dashboard")
        if not hasattr(user, "student_profile"):
            form.add_error(None, "Ce compte étudiant n'est pas encore rattaché à une inscription.")
        else:
            auth_login(request, user)
            return redirect("student_space")
    return render(request, "registration/student_login.html", {"form": form})

@login_required
def student_space(request):
    if request.user.is_staff:
        return redirect("dashboard")
    student = getattr(request.user, "student_profile", None)
    if not student:
        return redirect("student_login")
    month_order = {month: index for index, (month, _label) in enumerate(MonthlyPayment.MONTHS)}
    payments = sorted(student.payments.all(), key=lambda payment: month_order.get(payment.month, 99))
    paid_count = sum(1 for payment in payments if payment.paid)
    return render(request, "students/student_space.html", {"student": student, "payments": payments, "paid_count": paid_count})

@admin_required
def student_list(request):
    raw_payment_month = request.POST.get("payment_month", request.GET.get("payment_month", 12)) or 12
    try:
        payment_month = int(raw_payment_month)
    except (TypeError, ValueError):
        payment_month = 12
    if request.method == "POST" and request.POST.get("action") == "payment":
        student = get_object_or_404(Student, pk=request.POST.get("student_id"))
        payment, _created = MonthlyPayment.objects.get_or_create(student=student, month=payment_month)
        payment.paid = request.POST.get("paid") == "yes"
        payment.paid_at = timezone.localdate() if payment.paid else None
        payment.save(update_fields=["paid", "paid_at"])
        messages.success(request, f"Paiement de {student} mis à jour pour {payment.get_month_display()}.")
        return redirect(f"{request.path}?payment_month={payment_month}")
    qs = filtered_students(request)
    communes = ALLOWED_COMMUNES
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    student_ids = [student.pk for student in page]
    payments = MonthlyPayment.objects.filter(student_id__in=student_ids, month=payment_month)
    payment_by_student = {payment.student_id: payment for payment in payments}
    for student in page:
        student.selected_payment = payment_by_student.get(student.pk)
    return render(request, "students/student_list.html", {"page": page, "communes": communes, "levels": StudyLevel.objects.all(), "programs": Program.objects.select_related("level"), "payment_month": payment_month, "payment_months": MonthlyPayment.MONTHS})

@admin_required
def student_create(request):
    form = StudentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Étudiant ajouté."); return redirect("student_list")
    return render(request, "students/student_form.html", {"form": form, "title": "Ajouter un étudiant"})

@admin_required
def student_detail(request, pk):
    return render(request, "students/student_detail.html", {"student": get_object_or_404(Student.objects.select_related("level", "program"), pk=pk)})

@admin_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == "POST" and form.is_valid():
        changed = form.save(commit=False)
        changed.local_override = True
        changed.save(); messages.success(request, "Fiche mise à jour localement. La prochaine synchronisation préservera ces changements."); return redirect("student_detail", pk=pk)
    return render(request, "students/student_form.html", {"form": form, "title": "Modifier la fiche"})

@admin_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.delete(); messages.success(request, "Étudiant supprimé."); return redirect("student_list")
    return render(request, "students/student_confirm_delete.html", {"student": student})

@admin_required
def level_list(request, slug):
    level = get_object_or_404(StudyLevel, slug=slug)
    qs = Student.objects.filter(level=level).select_related("level", "program")
    if request.GET.get("program"): qs = qs.filter(program_id=request.GET["program"])
    if request.GET.get("bus") in ("yes", "no", "review"): qs = qs.filter(bus_choice=request.GET["bus"])
    if request.GET.get("commune"): qs = qs.filter(commune=request.GET["commune"])
    yes = qs.filter(bus_choice="yes").count()
    no = qs.filter(bus_choice="no").count()
    review = qs.filter(bus_choice="review").count()
    students = sorted(qs, key=lambda s: (accent_key(s.last_name), accent_key(s.first_names)))
    programs = level.programs.annotate(
        total=Count("students", filter=Q(students__level=level)),
        interested=Count("students", filter=Q(students__level=level, students__bus_choice="yes")),
    )
    return render(request, "students/level_list.html", {
        "level": level, "students": students, "yes": yes, "no": no, "review": review,
        "programs": programs,
        "communes": [commune for commune in ALLOWED_COMMUNES if Student.objects.filter(level=level, commune=commune).exists()],
        "selected_program": request.GET.get("program", ""),
    })

@admin_required
def communes(request):
    rows = Student.objects.filter(commune__in=ALLOWED_COMMUNES).values("commune").annotate(total=Count("id"), yes=Count("id", filter=Q(bus_choice="yes")), no=Count("id", filter=Q(bus_choice="no"))).order_by("-yes", "commune")
    return render(request, "students/communes.html", {"rows": rows})

@admin_required
def import_page(request):
    if request.method == "POST":
        try:
            if request.POST.get("action") == "google":
                log = import_google_sheet()
            else:
                upload = request.FILES.get("csv_file")
                if not upload: raise ValueError("Choisissez un fichier CSV.")
                if not upload.name.lower().endswith(".csv"): raise ValueError("Le fichier doit être au format CSV.")
                log = import_csv(upload)
            messages.success(request, f"Import terminé : {log.created} ajoutés, {log.updated} mis à jour, {log.ignored} ignorés, {log.errors} erreur(s).")
        except Exception as exc:
            messages.error(request, f"Import impossible : {exc}")
        return redirect("import_page")
    return render(request, "students/import.html", {"logs": SyncLog.objects.order_by("-started_at")[:10]})

@admin_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="etudiants-emsp.csv"'
    response.write("\ufeff")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Nom", "Prénom(s)", "Commune", "Licence", "Filière", "Classe/groupe", "Car", "Date inscription"])
    for s in filtered_students(request):
        writer.writerow([s.last_name, s.first_names, s.commune, s.level or "À vérifier", s.program.name if s.program else "À vérifier", s.class_group, s.get_bus_choice_display(), s.submitted_at or ""])
    return response
