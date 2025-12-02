from datetime import date

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ActivityForm,
    AttendanceForm,
    CourseForm,
    EnrollmentForm,
    GradeForm,
    LoginForm,
    MaterialForm,
    NotificationForm,
    SubmissionForm,
)
from .models import Activity, Attendance, Course, Enrollment, Material, Notification, Profile, Submission


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        role = request.POST.get("role")
        if form.is_valid() and role in {"teacher", "student"}:
            user = form.save()
            Profile.objects.create(user=user, role=role)
            messages.success(request, "Usuario registrado. Ahora puedes iniciar sesión.")
            return redirect("login")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect("dashboard")
    return render(request, "registration/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


def _require_role(user, role):
    profile = getattr(user, "profile", None)
    return profile and profile.role == role


@login_required
def dashboard(request):
    profile = getattr(request.user, "profile", None)
    if not profile:
        messages.error(request, "Asigna un rol para continuar.")
        return redirect("login")
    if profile.role == "teacher":
        courses = request.user.courses.all()
        notifications = Notification.objects.filter(created_by=request.user).order_by("-created_at")[:5]
        submissions = Submission.objects.filter(activity__course__teacher=request.user, grade__isnull=True)[:5]
        context = {"courses": courses, "notifications": notifications, "pending_submissions": submissions}
        return render(request, "dashboard_teacher.html", context)
    courses = Course.objects.all()
    enrolled_ids = request.user.enrollments.values_list("course_id", flat=True)
    notifications = Notification.objects.filter(audience__in=["all", "students"]).order_by("-created_at")[:5]
    context = {"courses": courses, "enrolled_ids": enrolled_ids, "notifications": notifications}
    return render(request, "dashboard_student.html", context)


@login_required
def course_list(request):
    profile = request.user.profile
    if profile.role == "teacher":
        courses = request.user.courses.all()
    else:
        courses = Course.objects.all()
    query = request.GET.get("q")
    level = request.GET.get("level")
    if query:
        courses = courses.filter(name__icontains=query)
    if level:
        courses = courses.filter(level__icontains=level)
    return render(request, "courses/list.html", {"courses": courses})


@login_required
def course_create(request):
    if not _require_role(request.user, "teacher"):
        return HttpResponseForbidden("Solo docentes pueden crear cursos")
    form = CourseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        course = form.save(commit=False)
        course.teacher = request.user
        course.save()
        messages.success(request, "Curso creado")
        return redirect("course_detail", course_id=course.id)
    return render(request, "courses/create.html", {"form": form})


@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    materials = course.materials.order_by("-created_at")
    activities = course.activities.order_by("-created_at")
    enrollments = course.enrollments.select_related("student")
    attendance_records = course.attendances.select_related("student")[:20]
    return render(
        request,
        "courses/detail.html",
        {
            "course": course,
            "materials": materials,
            "activities": activities,
            "enrollments": enrollments,
            "attendance_records": attendance_records,
        },
    )


@login_required
def enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if not _require_role(request.user, "student"):
        return HttpResponseForbidden("Solo estudiantes pueden matricularse")
    form = EnrollmentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user, course=course, defaults=form.cleaned_data
        )
        if created:
            messages.success(request, "Te has matriculado en el curso")
        else:
            messages.info(request, "Ya estabas matriculado en este curso")
        return redirect("course_detail", course_id=course.id)
    return render(request, "courses/enroll.html", {"course": course, "form": form})


@login_required
def upload_material(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    form = MaterialForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        material = form.save(commit=False)
        material.course = course
        material.save()
        messages.success(request, "Material agregado")
        return redirect("course_detail", course_id=course.id)
    return render(request, "materials/create.html", {"course": course, "form": form})


@login_required
def create_activity(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    form = ActivityForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        activity = form.save(commit=False)
        activity.course = course
        activity.save()
        messages.success(request, "Actividad creada")
        return redirect("course_detail", course_id=course.id)
    return render(request, "activities/create.html", {"course": course, "form": form})


@login_required
def submit_activity(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    if not _require_role(request.user, "student"):
        return HttpResponseForbidden("Solo estudiantes pueden entregar actividades")
    form = SubmissionForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        submission, _ = Submission.objects.update_or_create(
            activity=activity, student=request.user, defaults=form.cleaned_data
        )
        messages.success(request, "Entrega enviada")
        return redirect("course_detail", course_id=activity.course.id)
    return render(request, "activities/submit.html", {"activity": activity, "form": form})


@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id, activity__course__teacher=request.user)
    form = GradeForm(request.POST or None, instance=submission)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Calificación registrada")
        return redirect("course_detail", course_id=submission.activity.course.id)
    return render(request, "activities/grade.html", {"submission": submission, "form": form})


@login_required
def mark_attendance(request, course_id):
    course = get_object_or_404(Course, id=course_id, teacher=request.user)
    enrollments = course.enrollments.select_related("student", "student__profile")
    today = date.today()
    if request.method == "POST":
        for enrollment in enrollments:
            status = request.POST.get(f"status_{enrollment.student_id}", "present")
            Attendance.objects.update_or_create(
                course=course, student=enrollment.student, session_date=today, defaults={"status": status}
            )
        messages.success(request, "Asistencia guardada")
        return redirect("course_detail", course_id=course.id)
    attendance_forms = [
        {
            "enrollment": enrollment,
            "form": AttendanceForm(prefix=str(enrollment.student_id)),
            "status_name": f"status_{enrollment.student_id}",
        }
        for enrollment in enrollments
    ]
    return render(
        request,
        "attendance/mark.html",
        {"course": course, "attendance_forms": attendance_forms, "today": today},
    )


@login_required
def send_notification(request):
    if not _require_role(request.user, "teacher"):
        return HttpResponseForbidden("Solo docentes pueden enviar avisos")
    form = NotificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        notif = form.save(commit=False)
        notif.created_by = request.user
        notif.save()
        messages.success(request, "Notificación publicada")
        return redirect("dashboard")
    return render(request, "notifications/create.html", {"form": form})
