from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from complaints.models import Complaint, Notification
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
    users = User.objects.select_related('department').all().order_by('-date_joined')
    departments = Department.objects.all()
    return render(request, 'manage_users.html', {'users': users, 'departments': departments})

@login_required
def edit_user_view(request, user_id):
    if not is_admin(request.user):
        return redirect('dashboard')
    
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        role = request.POST.get('role')
        department_id = request.POST.get('department')
        
        if role in dict(User.ROLE_CHOICES):
            user_obj.role = role
            if role == 'Department Officer' and department_id:
                dept = Department.objects.filter(id=department_id).first()
                user_obj.department = dept
            else:
                user_obj.department = None
            user_obj.save()
            from django.contrib import messages
            messages.success(request, f'User {user_obj.email} updated successfully.')
            
    return redirect('manage_users')

@login_required
def toggle_user_status_view(request, user_id):
    if not is_admin(request.user):
        return redirect('dashboard')
        
    if request.method == 'POST':
        user_to_toggle = get_object_or_404(User, id=user_id)
        
        if user_to_toggle.id == request.user.id:
            from django.contrib import messages
            messages.error(request, 'You cannot deactivate your own account.')
            return redirect('manage_users')
            
        if user_to_toggle.is_active:
            # Check if this is the last active admin
            if user_to_toggle.role == 'Admin':
                active_admins = User.objects.filter(role='Admin', is_active=True).count()
                if active_admins <= 1:
                    from django.contrib import messages
                    messages.error(request, 'Cannot deactivate the last active Admin account.')
                    return redirect('manage_users')
                    
            user_to_toggle.is_active = False
            from django.contrib import messages
            messages.success(request, f'User {user_to_toggle.email} deactivated successfully.')
        else:
            user_to_toggle.is_active = True
            from django.contrib import messages
            messages.success(request, f'User {user_to_toggle.email} reactivated successfully.')
            
        user_to_toggle.save()
        
    return redirect('manage_users')

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
    
    departments = Department.objects.all()
    dept_stats = []
    for d in departments:
        dept_complaints = d.complaint_set.all()
        dept_total = dept_complaints.count()
        if dept_total == 0:
            continue
            
        resolved_comps = [c for c in dept_complaints if c.status in ['Resolved', 'Closed']]
        dept_resolved = len(resolved_comps)
        rate = int((dept_resolved / dept_total * 100))
        
        times = [(c.resolved_at - c.created_at).total_seconds() for c in resolved_comps if c.resolved_at]
        if times:
            avg_time_sec = sum(times) / len(times)
            days = int(avg_time_sec // 86400)
            hours = int((avg_time_sec % 86400) // 3600)
            if days > 0:
                avg_time_str = f"{days}d {hours}h"
            else:
                avg_time_str = f"{hours}h"
        else:
            avg_time_str = "N/A"
            
        ratings = [c.citizen_rating for c in resolved_comps if c.citizen_rating is not None]
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else "N/A"

        dept_stats.append({
            'name': d.department_name,
            'total': dept_total,
            'resolved': dept_resolved,
            'rate': rate,
            'avg_time': avg_time_str,
            'avg_rating': avg_rating
        })
    dept_stats.sort(key=lambda x: x['rate'], reverse=True)
    
    return render(request, 'analytics.html', {
        'category_data': category_data,
        'status_data': status_data,
        'dept_stats': dept_stats
    })

@login_required
def audit_log_view(request):
    if not is_admin(request.user):
        return redirect('dashboard')
    
    # We will mock the audit logs in the template for now,
    # as there is no AuditLog model currently.
    # In the future, this can query a real AuditLog table.
    return render(request, 'audit_log.html')


@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications_list.html', {'notifications': notifications})

@login_required
def mark_notifications_read_view(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
