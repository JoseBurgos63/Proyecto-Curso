from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cursos/', views.course_list, name='course_list'),
    path('cursos/crear/', views.course_create, name='course_create'),
    path('cursos/<int:course_id>/', views.course_detail, name='course_detail'),
    path('cursos/<int:course_id>/matricular/', views.enroll, name='course_enroll'),
    path('cursos/<int:course_id>/material/', views.upload_material, name='material_create'),
    path('cursos/<int:course_id>/actividades/crear/', views.create_activity, name='activity_create'),
    path('actividades/<int:activity_id>/entregar/', views.submit_activity, name='activity_submit'),
    path('entregas/<int:submission_id>/calificar/', views.grade_submission, name='submission_grade'),
    path('cursos/<int:course_id>/asistencia/', views.mark_attendance, name='attendance_mark'),
    path('notificaciones/nueva/', views.send_notification, name='notification_create'),
]
