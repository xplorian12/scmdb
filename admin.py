from django.contrib import admin
from .models import School, Professor, Student

class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    fields = ("email", "name", "expiration_date", "archived_at")
    readonly_fields = ()
    show_change_link = True

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "state", "payment_preference", "point_of_contact_name", "point_of_contact_email", "created_at")
    search_fields = ("name", "point_of_contact_name", "point_of_contact_email")
    list_filter = ("payment_preference", "country", "state")
    inlines = []

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ("name", "school", "email", "account_type", "expiration_date", "created_at")
    list_filter = ("account_type", "school")
    search_fields = ("name", "email", "school__name")
    inlines = [StudentInline]

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "professor", "expiration_date", "created_at")
    list_filter = ("professor__school", "professor")
    search_fields = ("email", "name", "professor__name", "professor__school__name")
