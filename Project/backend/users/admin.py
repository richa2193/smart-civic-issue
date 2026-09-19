from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'username', 'role', 'department', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('CivicSaathi Info', {'fields': ('role', 'department', 'phone', 'address', 'profile_picture', 'is_verified')}),
    )

admin.site.register(User, CustomUserAdmin)
