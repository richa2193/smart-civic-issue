from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.department_dashboard_view, name='department_dashboard'),
    path('assigned/', views.assigned_complaints_view, name='assigned_complaints'),
    path('update-status/<int:id>/', views.update_status_view, name='update_status'),
    path('reports/', views.reports_view, name='reports'),
]
