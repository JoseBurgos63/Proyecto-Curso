from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ROLE_CHOICES = (
        ("teacher", "Docente"),
        ("student", "Estudiante"),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Course(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    level = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")

    def __str__(self):
        return f"{self.code} - {self.name}"


class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    full_name = models.CharField(max_length=150)
    national_id = models.CharField(max_length=20)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "course")

    def __str__(self):
        return f"{self.full_name} en {self.course}"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ("present", "Presente"),
        ("absent", "Ausente"),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attendances")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendances")
    session_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="present")

    class Meta:
        unique_together = ("course", "student", "session_date")
        ordering = ["-session_date"]

    def __str__(self):
        return f"{self.course} - {self.student} ({self.session_date})"


class Material(models.Model):
    MATERIAL_TYPES = (
        ("pdf", "PDF"),
        ("video", "Video"),
        ("link", "Enlace"),
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    type = models.CharField(max_length=10, choices=MATERIAL_TYPES)
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="materials/", blank=True, null=True)
    url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course})"


class Activity(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="activities")
    title = models.CharField(max_length=150)
    description = models.TextField()
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.course})"


class Submission(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    attachment = models.FileField(upload_to="submissions/", blank=True, null=True)
    link = models.URLField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    class Meta:
        unique_together = ("activity", "student")

    def __str__(self):
        return f"Entrega de {self.student} para {self.activity}"


class Notification(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="notifications", blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.CharField(max_length=255)
    audience = models.CharField(max_length=20, choices=(
        ("all", "Todos"),
        ("students", "Estudiantes"),
        ("teachers", "Docentes"),
    ), default="all")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "profile"):
        Profile.objects.create(user=instance, role="student")
