from django.contrib import admin
from .models import Complaint, Notification, Votes

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'description', 'address')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('message', 'user__username')

@admin.register(Votes)
class VotesAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'complaint', 'created_at')
