from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.department_dashboard_view, name='department_dashboard'),
    path('assigned/', views.assigned_complaints_view, name='assigned_complaints'),
    path('update-status/<int:id>/', views.update_status_view, name='update_status'),
    path('reports/', views.reports_view, name='reports'),
    path('team/', views.workers_list_view, name='workers_list'),
    path('team/add/', views.add_worker_view, name='add_worker'),
    path('team/edit/<int:id>/', views.edit_worker_view, name='edit_worker'),
    path('team/toggle-availability/<int:id>/', views.toggle_worker_availability_view, name='toggle_worker_availability'),
]
