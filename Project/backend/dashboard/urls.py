from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('manage-users/', views.manage_users_view, name='manage_users'),
    path('manage-departments/', views.manage_departments_view, name='manage_departments'),
    path('manage-complaints/', views.manage_complaints_view, name='manage_complaints'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
]
