from django.contrib import admin

from .models import Activity, Attendance, Course, Enrollment, Material, Notification, Profile, Submission

admin.site.register(Profile)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Attendance)
admin.site.register(Material)
admin.site.register(Activity)
admin.site.register(Submission)
admin.site.register(Notification)
