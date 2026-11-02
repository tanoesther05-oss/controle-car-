from django import forms
from django.contrib.auth.models import User
from .models import ALLOWED_COMMUNES, Program, Student, StudyLevel

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["last_name", "first_names", "commune", "level", "program", "class_group", "bus_choice", "submitted_at", "phone", "notes"]
        widgets = {"submitted_at": forms.DateTimeInput(attrs={"type": "datetime-local"}), "notes": forms.Textarea(attrs={"rows": 2})}
    def clean(self):
        data = super().clean()
        level, program = data.get("level"), data.get("program")
        if program and level and program.level_id != level.id:
            self.add_error("program", "Cette filière n'appartient pas à la licence choisie.")
        return data


class RegistrationForm(forms.ModelForm):
    GROUPS_L1 = (("A", "Groupe A"), ("B", "Groupe B"), ("C", "Groupe C"))
    username = forms.CharField(label="Nom d'utilisateur", widget=forms.TextInput(attrs={"placeholder": "Choisissez votre identifiant"}), max_length=150)
    bus_choice = forms.ChoiceField(label="Souhaitez-vous payer le car maintenant ?", choices=(("yes", "Oui"), ("no", "Non")), widget=forms.Select())
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={"placeholder": "Au moins 8 caractères"}), min_length=8)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={"placeholder": "Répétez le mot de passe"}), min_length=8)

    class Meta:
        model = Student
        fields = ["last_name", "first_names", "level", "program", "class_group", "commune", "phone", "bus_choice", "notes"]
        labels = {
            "last_name": "Nom", "first_names": "Prénom(s)", "level": "Licence",
            "program": "Filière", "class_group": "Groupe", "commune": "Commune",
            "phone": "Numéro de téléphone", "notes": "Commentaire",
        }
        widgets = {
            "last_name": forms.TextInput(attrs={"placeholder": "Votre nom"}),
            "first_names": forms.TextInput(attrs={"placeholder": "Votre prénom"}),
            "level": forms.Select(attrs={"class": "js-level"}),
            "program": forms.Select(attrs={"class": "js-program"}),
            "class_group": forms.Select(choices=(("A", "Groupe A"), ("B", "Groupe B"), ("C", "Groupe C")), attrs={"class": "js-group"}),
            "commune": forms.Select(),
            "phone": forms.TextInput(attrs={"placeholder": "Ex. 07 00 00 00 00", "type": "tel"}),
            "notes": forms.Textarea(attrs={"placeholder": "Une précision à nous transmettre", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["level"].queryset = StudyLevel.objects.all()
        self.fields["level"].empty_label = "Choisissez votre licence"
        self.fields["program"].queryset = Program.objects.select_related("level").all()
        self.fields["program"].empty_label = "Choisissez votre filière"
        self.fields["commune"].widget.choices = [("", "Choisissez votre commune")] + [(value, value) for value in ALLOWED_COMMUNES]
        self.fields["class_group"].required = False

    def clean(self):
        data = super().clean()
        level, program, group = data.get("level"), data.get("program"), data.get("class_group")
        if program and level and program.level_id != level.id:
            self.add_error("program", "Cette filière n'appartient pas à la licence choisie.")
        if level and level.slug == "licence-1" and group not in {"A", "B", "C"}:
            self.add_error("class_group", "Choisissez le groupe A, B ou C.")
        if level and level.slug != "licence-1":
            data["class_group"] = ""
        if data.get("bus_choice") == "no" and not (data.get("notes") or "").strip():
            self.add_error("notes", "Indiquez quand vous pourrez payer ou ajoutez un commentaire.")
        if data.get("password1") != data.get("password2"):
            self.add_error("password2", "Les deux mots de passe ne correspondent pas.")
        return data

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé. Choisissez-en un autre.")
        return username
