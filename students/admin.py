from django.contrib import admin
from .models import MonthlyPayment, StudyLevel, Program, Student, SyncLog

class ProgramInline(admin.TabularInline):
    model = Program
    extra = 0

@admin.register(StudyLevel)
class StudyLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    inlines = [ProgramInline]

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "order")
    list_filter = ("level",)

class MonthlyPaymentInline(admin.TabularInline):
    model = MonthlyPayment
    extra = 0
    fields = ("month", "paid", "paid_at", "note")
    ordering = ("month",)

    def get_queryset(self, request):
        order = {12: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7}
        from django.db.models import Case, IntegerField, Value, When
        return super().get_queryset(request).annotate(month_order=Case(*[When(month=month, then=Value(position)) for month, position in order.items()], output_field=IntegerField())).order_by("month_order")

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_names", "level", "program", "commune", "bus_choice", "user", "local_override")
    list_filter = ("level", "program", "commune", "bus_choice")
    search_fields = ("last_name", "first_names", "commune")
    inlines = [MonthlyPaymentInline]

@admin.register(MonthlyPayment)
class MonthlyPaymentAdmin(admin.ModelAdmin):
    list_display = ("student", "month", "paid", "paid_at", "note")
    list_filter = ("month", "paid")
    search_fields = ("student__last_name", "student__first_names")

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ("started_at", "source", "created", "updated", "ignored", "errors")
    readonly_fields = tuple(f.name for f in SyncLog._meta.fields)
