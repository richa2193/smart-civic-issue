from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from complaints.models import Complaint
from users.models import User
from departments.models import Department
from django.db.models import Count

def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'Citizen':
        complaints = Complaint.objects.select_related('department').filter(user=user).order_by('-created_at')[:5]
        
        from django.db.models import Q
        stats_agg = Complaint.objects.filter(user=user).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status__in=['Submitted', 'Assigned'])),
            resolved=Count('id', filter=Q(status__in=['Resolved', 'Closed']))
        )
        stats = {
            'total': stats_agg['total'],
            'pending': stats_agg['pending'],
            'resolved': stats_agg['resolved']
        }
        return render(request, 'dashboard.html', {'complaints': complaints, 'stats': stats})
    elif user.role == 'Department Officer':
        return redirect('department_dashboard')
    elif user.role == 'Admin':
        return redirect('admin_dashboard')
    
    return redirect('home')

@login_required
def admin_dashboard_view(request):
    if not is_admin(request.user):
        return redirect('dashboard')
        
    stats = {
        'total_complaints': Complaint.objects.count(),
        'pending': Complaint.objects.filter(status__in=['Submitted', 'Assigned']).count(),
        'resolved': Complaint.objects.filter(status__in=['Resolved', 'Closed']).count(),
        'users': User.objects.filter(role='Citizen').count(),
        'departments': Department.objects.count(),
    }
    
    recent_complaints = Complaint.objects.select_related('user', 'department').order_by('-created_at')[:5]
    
    return render(request, 'admin_dashboard.html', {'stats': stats, 'recent_complaints': recent_complaints})

@login_required
def manage_users_view(request):
    if not is_admin(request.user):
        return redirect('dashboard')
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'manage_users.html', {'users': users})

@login_required
def manage_departments_view(request):
    if not is_admin(request.user):
        return redirect('dashboard')
    departments = Department.objects.all().order_by('-created_at')
    return render(request, 'manage_departments.html', {'departments': departments})

@login_required
def manage_complaints_view(request):
    if not is_admin(request.user):
        return redirect('dashboard')
    complaints = Complaint.objects.select_related('user', 'department').all().order_by('-created_at')
    return render(request, 'manage_complaints.html', {'complaints': complaints})

@login_required
def analytics_view(request):
    if not is_admin(request.user):
        return redirect('dashboard')
        
    category_data = Complaint.objects.values('category').annotate(count=Count('id'))
    status_data = Complaint.objects.values('status').annotate(count=Count('id'))
    
    return render(request, 'analytics.html', {
        'category_data': category_data,
        'status_data': status_data
    })

@login_required
def audit_log_view(request):
    if not is_admin(request.user):
        return redirect('dashboard')
    
    # We will mock the audit logs in the template for now,
    # as there is no AuditLog model currently.
    # In the future, this can query a real AuditLog table.
    return render(request, 'audit_log.html')
