from django.contrib import admin
from .models import Department, Worker

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'department_name', 'head_name', 'email', 'phone')
    search_fields = ('department_name', 'head_name')

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'department', 'phone_number', 'is_available')
    list_filter = ('department', 'is_available')
    search_fields = ('name', 'phone_number')
