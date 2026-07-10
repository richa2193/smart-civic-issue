from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from .models import Complaint, Notification, Votes
from .forms import ComplaintForm
from departments.models import Department

def get_department_for_category(category):
    mapping = {
        'Road Damage': 'Road Department',
        'Garbage': 'Sanitation Department',
        'Street Light': 'Electrical Department',
        'Water Leakage': 'Water Department',
        'Drainage': 'Drainage Department',
        'Traffic Signal': 'Traffic Department'
    }
    dept_name = mapping.get(category, 'General Department')
    dept, created = Department.objects.get_or_create(
        department_name=dept_name,
        defaults={'email': f'{dept_name.lower().replace(" ", "")}@smartcivic.com', 'phone': '0000000000', 'head_name': 'Pending'}
    )
    return dept

@login_required
def report_issue_view(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            
            # Auto-assign department
            department = get_department_for_category(complaint.category)
            complaint.department = department
            complaint.status = 'Assigned'
            complaint.save()
            
            # Create Notification
            Notification.objects.create(
                user=request.user,
                message=f'Your complaint "{complaint.title}" has been submitted and assigned to {department.department_name}.'
            )
            
            messages.success(request, 'Issue reported successfully! It has been assigned to the relevant department.')
            return redirect('dashboard')
    else:
        form = ComplaintForm()
        
    public_complaints = Complaint.objects.filter(latitude__isnull=False, longitude__isnull=False).order_by('-created_at')[:20]
        
    return render(request, 'report_issue.html', {
        'form': form, 
        'geoapify_key': settings.GEOAPIFY_API_KEY,
        'public_complaints': public_complaints
    })

@login_required
def my_complaints_view(request):
    complaints = Complaint.objects.select_related('department').filter(user=request.user).order_by('-created_at')
    return render(request, 'complaints.html', {'complaints': complaints})

@login_required
def complaint_detail_view(request, id):
    complaint = get_object_or_404(Complaint.objects.select_related('department', 'user'), id=id)
    return render(request, 'complaint_detail.html', {'complaint': complaint, 'geoapify_key': settings.GEOAPIFY_API_KEY})

@login_required
def edit_complaint_view(request, id):
    complaint = get_object_or_404(Complaint, id=id, user=request.user)
    if complaint.status != 'Submitted':
        messages.warning(request, 'You can only edit complaints that are in Submitted status.')
        return redirect('complaint_detail', id=complaint.id)
        
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, 'Complaint updated successfully.')
            return redirect('complaint_detail', id=complaint.id)
    else:
        form = ComplaintForm(instance=complaint)
        
    return render(request, 'edit_complaint.html', {'form': form, 'complaint': complaint, 'geoapify_key': settings.GEOAPIFY_API_KEY})

def community_dashboard_view(request):
    complaints = Complaint.objects.select_related('user', 'department').all().order_by('-created_at')
    
    # Calculate simple stats
    total = complaints.count()
    resolved = complaints.filter(status='Resolved').count()
    resolution_rate = int((resolved / total * 100)) if total > 0 else 0
    
    from django.db.models import Count
    category_data = list(Complaint.objects.values('category').annotate(count=Count('id')).order_by('-count')[:5])
    
    return render(request, 'community_dashboard.html', {
        'complaints': complaints,
        'total': total,
        'resolved': resolved,
        'resolution_rate': resolution_rate,
        'category_data': category_data,
        'geoapify_key': settings.GEOAPIFY_API_KEY
    })

@login_required
def upvote_complaint_view(request, id):
    if request.method == 'POST':
        complaint = get_object_or_404(Complaint, id=id)
        vote, created = Votes.objects.get_or_create(user=request.user, complaint=complaint)
        
        if not created:
            vote.delete()
            action = 'unvoted'
        else:
            action = 'voted'
            
        upvotes = complaint.votes.count()
        return JsonResponse({'status': 'success', 'action': action, 'upvotes': upvotes})
    return JsonResponse({'status': 'error'}, status=400)
