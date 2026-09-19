from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from complaints.models import Complaint, Notification
from .models import Department, Worker
from .forms import WorkerForm
from django.db.models import Count
from django.conf import settings

def is_department_officer(user):
    return user.is_authenticated and user.role == 'Department Officer'

@login_required
def department_dashboard_view(request):
    if not is_department_officer(request.user):
        return redirect('dashboard')
        
    complaints = Complaint.objects.select_related('user', 'department').order_by('-created_at')[:5]
    
    from django.db.models import Q
    stats_agg = Complaint.objects.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status__in=['Assigned', 'In Progress'])),
        resolved=Count('id', filter=Q(status__in=['Resolved', 'Closed']))
    )
    
    stats = {
        'total': stats_agg['total'] or 0,
        'pending': stats_agg['pending'] or 0,
        'resolved': stats_agg['resolved'] or 0
    }

    workload_by_category = Complaint.objects.exclude(status__in=['Resolved', 'Closed']).values('category').annotate(count=Count('id')).order_by('-count')
    
    total_workers = Worker.objects.count()
    available_workers = Worker.objects.filter(is_available=True).count()
    unavailable_workers_list = Worker.objects.filter(is_available=False)[:3]

    context = {
        'complaints': complaints, 
        'stats': stats,
        'workload_by_category': workload_by_category,
        'total_workers': total_workers,
        'available_workers': available_workers,
        'unavailable_workers_list': unavailable_workers_list
    }

    return render(request, 'department_dashboard.html', context)

@login_required
def assigned_complaints_view(request):
    if not is_department_officer(request.user):
        return redirect('dashboard')
    
    complaints = Complaint.objects.select_related('user', 'assigned_worker', 'department').order_by('-created_at')
    
    return render(request, 'assigned_complaints.html', {'complaints': complaints, 'is_unlinked': False})

@login_required
def update_status_view(request, id):
    if not is_department_officer(request.user):
        return redirect('dashboard')
        
    complaint = get_object_or_404(Complaint.objects.select_related('user'), id=id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        remarks = request.POST.get('remarks')
        assigned_worker_id = request.POST.get('assigned_worker')
        expected_completion_date = request.POST.get('expected_completion_date')
        
        if new_status in dict(Complaint.STATUS_CHOICES):
            old_status = complaint.status
            complaint.status = new_status
            if remarks:
                complaint.remarks = remarks
                
            if assigned_worker_id:
                worker = get_object_or_404(Worker, id=assigned_worker_id, department=complaint.department)
                if complaint.assigned_worker != worker:
                    complaint.assigned_worker = worker
                    sys_remark = f"[System: Worker '{worker.name}' assigned for field execution]"
                    complaint.remarks = f"{complaint.remarks}\n\n{sys_remark}".strip() if complaint.remarks else sys_remark
            else:
                complaint.assigned_worker = None
                
            if expected_completion_date:
                complaint.expected_completion_date = expected_completion_date
            else:
                complaint.expected_completion_date = None
                
            if new_status in ['Resolved', 'Closed']:
                from django.utils import timezone
                complaint.resolved_at = timezone.now()
                
            complaint.save()
            
            # Notify User
            msg = f'The status of your complaint "{complaint.title}" has been updated to {new_status}.'
            if new_status == 'Resolved':
                msg += ' Please visit the complaint page to confirm the resolution and provide your feedback.'
                
            Notification.objects.create(
                user=complaint.user,
                message=msg
            )
            
            # Send Status Update Email
            if complaint.user.email:
                from config.email_utils import send_transactional_email
                context = {
                    'complaint': complaint,
                    'old_status': old_status,
                    'site_url': request.build_absolute_uri('/')[:-1]
                }
                send_transactional_email(
                    f'Issue Status Update: {new_status}',
                    'status_update_email.html',
                    context,
                    [complaint.user.email]
                )
            
            messages.success(request, 'Complaint status updated successfully.')
            return redirect('assigned_complaints')
            
    similar_issues_count = Complaint.objects.filter(
        category=complaint.category,
        department=complaint.department
    ).exclude(id=complaint.id).count()
    
    workers = Worker.objects.filter(department=complaint.department, is_available=True)
    
    active_workload_count = 0
    if complaint.assigned_worker:
        active_workload_count = Complaint.objects.filter(
            assigned_worker=complaint.assigned_worker
        ).exclude(status__in=['Resolved', 'Closed']).exclude(id=complaint.id).count()
    
    return render(request, 'update_status.html', {
        'complaint': complaint,
        'geoapify_key': settings.GEOAPIFY_API_KEY,
        'similar_issues_count': similar_issues_count,
        'workers': workers,
        'active_workload_count': active_workload_count
    })

@login_required
def reports_view(request):
    if not is_department_officer(request.user):
        return redirect('dashboard')
        
    report_data = Complaint.objects.values('status').annotate(count=Count('id'))
    
    return render(request, 'reports.html', {'report_data': report_data, 'is_unlinked': False})

@login_required
def workers_list_view(request):
    if not is_department_officer(request.user):
        return redirect('dashboard')
    
    workers = Worker.objects.select_related('department').order_by('name')
    departments = Department.objects.all().order_by('department_name')
    return render(request, 'workers_list.html', {'workers': workers, 'departments': departments})

@login_required
def add_worker_view(request):
    if not is_department_officer(request.user):
        return redirect('dashboard')

    if request.method == 'POST':
        post_data = request.POST.copy()
        if 'worker_full_name_v2' in post_data:
            post_data['name'] = post_data['worker_full_name_v2']
        if 'worker_phone_v2' in post_data:
            post_data['phone_number'] = post_data['worker_phone_v2']
            
        form = WorkerForm(post_data)
        if form.is_valid():
            worker = form.save(commit=False)
            worker.created_by = request.user
            worker.save()
            messages.success(request, f'{worker.name} added to your team.')
            return redirect('workers_list')
    else:
        form = WorkerForm()
        
    return render(request, 'worker_form.html', {'form': form, 'title': 'Add Team Member'})

@login_required
def edit_worker_view(request, id):
    if not is_department_officer(request.user):
        return redirect('dashboard')
        
    worker = get_object_or_404(Worker, id=id)

    if request.method == 'POST':
        post_data = request.POST.copy()
        if 'worker_full_name_v2' in post_data:
            post_data['name'] = post_data['worker_full_name_v2']
        if 'worker_phone_v2' in post_data:
            post_data['phone_number'] = post_data['worker_phone_v2']
            
        form = WorkerForm(post_data, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, 'Worker updated successfully.')
            return redirect('workers_list')
    else:
        form = WorkerForm(instance=worker)
        
    return render(request, 'worker_form.html', {'form': form, 'title': 'Edit Team Member'})

@login_required
def toggle_worker_availability_view(request, id):
    if not is_department_officer(request.user):
        return redirect('dashboard')
        
    worker = get_object_or_404(Worker, id=id)
    
    if request.method == 'POST':
        worker.is_available = not worker.is_available
        worker.save()
        status = 'available' if worker.is_available else 'unavailable'
        messages.success(request, f'Worker marked as {status}.')
        
    return redirect('workers_list')
