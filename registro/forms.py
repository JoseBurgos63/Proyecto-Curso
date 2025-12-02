from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import DateInput

from .models import Activity, Attendance, Course, Enrollment, Material, Notification, Submission


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario", max_length=150)
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "code", "level", "description"]


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["full_name", "national_id"]


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ["type", "title", "description", "file", "url"]

    def clean(self):
        cleaned = super().clean()
        material_type = cleaned.get("type")
        file = cleaned.get("file")
        url = cleaned.get("url")
        if material_type == "link" and not url:
            self.add_error("url", "Agrega el enlace del recurso.")
        if material_type in {"pdf", "video"} and not file:
            self.add_error("file", "Sube un archivo para este material.")
        return cleaned


class ActivityForm(forms.ModelForm):
    due_date = forms.DateTimeField(label="Fecha límite", widget=DateInput(attrs={"type": "datetime-local"}))

    class Meta:
        model = Activity
        fields = ["title", "description", "due_date"]


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["attachment", "link"]

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("attachment") and not cleaned.get("link"):
            raise forms.ValidationError("Sube un archivo o agrega un enlace de tu entrega.")
        return cleaned


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["status"]


class GradeForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["grade"]


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ["course", "message", "audience"]
