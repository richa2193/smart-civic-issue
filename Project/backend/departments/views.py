from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from complaints.models import Complaint, Notification
from .models import Department
from django.db.models import Count

def is_department_officer(user):
    return user.is_authenticated and user.role == 'Department Officer'

@login_required
def department_dashboard_view(request):
    if not is_department_officer(request.user):
        return redirect('dashboard')
        
    # Get the department assigned to this officer based on their email domain or a mapping
    # For simplicity, we assume one department per officer matching their email logic or we just grab the first one
    # In a real app, you would have a ForeignKey from User to Department
    try:
        # Simplification: Officer sees complaints for their mapped department
        # Here we just fetch all complaints if department is not explicitly linked, but ideally we link it.
        # Let's say all officers can see all departments for now or we filter if they have a specific department.
        department = Department.objects.first() # Placeholder
        complaints = Complaint.objects.select_related('user').filter(department=department).order_by('-created_at')[:5]
        
        from django.db.models import Q
        stats_agg = Complaint.objects.filter(department=department).aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status__in=['Assigned', 'In Progress'])),
            resolved=Count('id', filter=Q(status__in=['Resolved', 'Closed']))
        )
        
        stats = {
            'total': stats_agg['total'] or 0,
            'pending': stats_agg['pending'] or 0,
            'resolved': stats_agg['resolved'] or 0
        }
    except Department.DoesNotExist:
        complaints = []
        stats = {'total': 0, 'pending': 0, 'resolved': 0}

    return render(request, 'department_dashboard.html', {'complaints': complaints, 'stats': stats})

@login_required
def assigned_complaints_view(request):
    if not is_department_officer(request.user):
        return redirect('dashboard')
    
    department = Department.objects.first() # Placeholder
    complaints = Complaint.objects.select_related('user').filter(department=department).order_by('-created_at')
    
    return render(request, 'assigned_complaints.html', {'complaints': complaints})

@login_required
def update_status_view(request, id):
    if not is_department_officer(request.user):
        return redirect('dashboard')
        
    complaint = get_object_or_404(Complaint.objects.select_related('user'), id=id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks')
        
        if new_status in dict(Complaint.STATUS_CHOICES):
            complaint.status = new_status
            if remarks:
                complaint.remarks = remarks
            complaint.save()
            
            # Notify User
            Notification.objects.create(
                user=complaint.user,
                message=f'The status of your complaint "{complaint.title}" has been updated to {new_status}.'
            )
            
            messages.success(request, 'Complaint status updated successfully.')
            return redirect('assigned_complaints')
            
    return render(request, 'update_status.html', {'complaint': complaint})

@login_required
def reports_view(request):
    if not is_department_officer(request.user):
        return redirect('dashboard')
        
    department = Department.objects.first() # Placeholder
    report_data = Complaint.objects.filter(department=department).values('status').annotate(count=Count('id'))
    
    return render(request, 'reports.html', {'report_data': report_data})
