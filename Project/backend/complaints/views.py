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
        'Traffic Signal': 'Traffic Department',
        'Tree Fallen': 'Road Department',
        'Public Toilet': 'Sanitation Department',
        'Illegal Dumping': 'Sanitation Department'
    }
    dept_name = mapping.get(category, 'General Department')
    dept = Department.objects.filter(department_name__iexact=dept_name).first()
    if not dept:
        dept = Department.objects.create(
            department_name=dept_name,
            email=f'{dept_name.lower().replace(" ", "")}@smartcivic.com',
            phone='0000000000',
            head_name='Pending'
        )
    return dept

@login_required
def report_issue_view(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        
        # Require image on the frontend via HTML5 and set custom error message
        form.fields['image'].required = True
        form.fields['image'].widget.attrs.update({'required': 'required'})
        form.fields['image'].error_messages = {'required': 'A photo is required to help departments verify and resolve your issue.'}
        
        if form.is_valid():
            # Strict backend validation in case frontend validation is bypassed
            if not request.FILES.get('image'):
                form.add_error('image', 'A photo is required to help departments verify and resolve your issue.')
                public_complaints = Complaint.objects.filter(latitude__isnull=False, longitude__isnull=False).order_by('-created_at')[:20]
                return render(request, 'report_issue.html', {'form': form, 'geoapify_key': settings.GEOAPIFY_API_KEY, 'public_complaints': public_complaints})

            complaint = form.save(commit=False)
            
            # Require coordinates or attempt fallback geocoding
            if not complaint.latitude or not complaint.longitude:
                if complaint.address:
                    import requests
                    url = f"https://api.geoapify.com/v1/geocode/search?text={complaint.address}&apiKey={settings.GEOAPIFY_API_KEY}"
                    try:
                        resp = requests.get(url, timeout=5)
                        if resp.status_code == 200:
                            data = resp.json()
                            if data.get('features') and len(data['features']) > 0:
                                coords = data['features'][0]['geometry']['coordinates']
                                complaint.longitude = coords[0]
                                complaint.latitude = coords[1]
                            else:
                                messages.warning(request, 'Map/Geocoding temporarily unavailable - saved without precise coordinates.')
                        else:
                            messages.warning(request, 'Map/Geocoding temporarily unavailable - saved without precise coordinates.')
                    except Exception:
                        messages.warning(request, 'Map/Geocoding temporarily unavailable - saved without precise coordinates.')
                else:
                    form.add_error('address', 'Location is required. Please drop a pin on the map.')
                    public_complaints = Complaint.objects.filter(latitude__isnull=False, longitude__isnull=False).order_by('-created_at')[:20]
                    return render(request, 'report_issue.html', {'form': form, 'geoapify_key': settings.GEOAPIFY_API_KEY, 'public_complaints': public_complaints})
            
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
            
            # Send Emails
            from config.email_utils import send_transactional_email
            site_url = request.build_absolute_uri('/')[:-1]
            
            # 1. Citizen Confirmation
            send_transactional_email(
                'Issue Reported Successfully',
                'issue_reported_email.html',
                {'name': request.user.first_name or 'Citizen', 'complaint': complaint, 'site_url': site_url},
                [request.user.email]
            )
            
            # 2. Officer Assignment
            from users.models import User
            officers = User.objects.filter(role='Department Officer', department=department)
            officer_emails = []
            
            for officer in officers:
                if officer.email:
                    officer_emails.append(officer.email)
                
                # Create Notification for each officer
                Notification.objects.create(
                    user=officer,
                    message=f'New issue reported: Ticket #{complaint.id} "{complaint.title}" has been assigned to your department.'
                )
                
            if officer_emails:
                send_transactional_email(
                    'New Issue Assignment',
                    'officer_assignment_email.html',
                    {'complaint': complaint, 'site_url': site_url},
                    officer_emails
                )
            
            messages.success(request, 'Issue reported successfully! It has been assigned to the relevant department.')
            return redirect('dashboard')
    else:
        form = ComplaintForm()
        form.fields['image'].required = True
        form.fields['image'].widget.attrs.update({'required': 'required'})
        
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
    
    context = {'complaint': complaint, 'geoapify_key': settings.GEOAPIFY_API_KEY}
    if request.user.role == 'Admin':
        from departments.models import Department
        context['departments'] = Department.objects.all()
        
    return render(request, 'complaint_detail.html', context)

def public_complaint_detail_view(request, id):
    complaint = get_object_or_404(Complaint.objects.select_related('department'), id=id)
    return render(request, 'public_complaint_detail.html', {'complaint': complaint, 'geoapify_key': settings.GEOAPIFY_API_KEY})

@login_required
def edit_complaint_view(request, id):
    complaint = get_object_or_404(Complaint, id=id, user=request.user)
    if complaint.status not in ['Submitted', 'Assigned']:
        messages.error(request, 'This issue can no longer be edited once work has begun.')
        return redirect('complaint_detail', id=complaint.id)
        
    if request.method == 'POST':
        old_category = complaint.category
        old_image = complaint.image
        
        form = ComplaintForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            # Handle photo replacement
            if request.FILES.get('image') and old_image:
                old_image.delete(save=False)
                
            updated_complaint = form.save(commit=False)
            
            # Handle category change correctly
            if updated_complaint.category != old_category:
                new_department = get_department_for_category(updated_complaint.category)
                old_dept_name = updated_complaint.department.department_name if updated_complaint.department else 'None'
                updated_complaint.department = new_department
                
                # Log this in Status History
                from django.utils import timezone
                timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                log_msg = f"[{timestamp}] Citizen updated issue details — recategorized from {old_category} to {updated_complaint.category}, re-routed to {new_department.department_name}."
                updated_complaint.remarks = f"{updated_complaint.remarks or ''}\n\n{log_msg}".strip()
            else:
                # Log standard edit
                from django.utils import timezone
                timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                log_msg = f"[{timestamp}] Issue details updated by citizen."
                updated_complaint.remarks = f"{updated_complaint.remarks or ''}\n\n{log_msg}".strip()
                
            updated_complaint.save()
            
            # Notify the assigned department (if already assigned)
            if updated_complaint.department:
                from users.models import User
                officers = User.objects.filter(role='Department Officer', department=updated_complaint.department)
                officer_emails = []
                for officer in officers:
                    Notification.objects.create(
                        user=officer,
                        message=f'A complaint assigned to you (Ticket #{updated_complaint.id}) has been updated by the citizen — please review the latest details.'
                    )
                    if officer.email:
                        officer_emails.append(officer.email)
                        
                if officer_emails:
                    from config.email_utils import send_transactional_email
                    site_url = request.build_absolute_uri('/')[:-1]
                    send_transactional_email(
                        'Issue Details Updated',
                        'officer_assignment_email.html',
                        {'complaint': updated_complaint, 'site_url': site_url},
                        officer_emails
                    )
            
            messages.success(request, 'Complaint updated successfully.')
            return redirect('complaint_detail', id=updated_complaint.id)
    else:
        form = ComplaintForm(instance=complaint)
        
    return render(request, 'edit_complaint.html', {'form': form, 'complaint': complaint, 'geoapify_key': settings.GEOAPIFY_API_KEY})

def community_dashboard_view(request):
    complaints = Complaint.objects.select_related('user', 'department').all().order_by('-created_at')
    
    # Calculate simple stats
    total = complaints.count()
    resolved = complaints.filter(status__in=['Resolved', 'Closed']).count()
    resolution_rate = int((resolved / total * 100)) if total > 0 else 0
    
    from django.db.models import Count
    category_data = list(Complaint.objects.values('category').annotate(count=Count('id')).order_by('-count')[:5])
    
    # Calculate department performance stats in python (safe for SQLite)
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

        dept_stats.append({
            'name': d.department_name,
            'total': dept_total,
            'resolved': dept_resolved,
            'rate': rate,
            'avg_time': avg_time_str
        })
    dept_stats.sort(key=lambda x: x['rate'], reverse=True)
    
    priority_issues = Complaint.objects.filter(
        status__in=['Submitted', 'Assigned', 'In Progress']
    ).annotate(num_votes=Count('votes')).order_by('-num_votes', '-created_at')[:6]
    
    return render(request, 'community_dashboard.html', {
        'complaints': complaints,
        'total': total,
        'resolved': resolved,
        'resolution_rate': resolution_rate,
        'category_data': category_data,
        'dept_stats': dept_stats,
        'priority_issues': priority_issues,
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

@login_required
def suggest_category_view(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        try:
            from .ai_classifier import suggest_category_from_image
            # Read image bytes
            image_bytes = image_file.read()
            suggested = suggest_category_from_image(image_bytes)
            if suggested is None:
                return JsonResponse({'status': 'success', 'suggested_category': None, 'message': 'no suggestion available'})
            return JsonResponse({'status': 'success', 'suggested_category': suggested})
        except Exception as e:
            return JsonResponse({'status': 'success', 'suggested_category': None, 'message': 'no suggestion available'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def heatmap_view(request):
    return render(request, 'heatmap.html', {
        'geoapify_key': settings.GEOAPIFY_API_KEY
    })

def heatmap_data_api_view(request):
    category = request.GET.get('category', 'all')
    status = request.GET.get('status', 'all')
    days = request.GET.get('days', '30')

    qs = Complaint.objects.filter(latitude__isnull=False, longitude__isnull=False)
    
    if category != 'all':
        qs = qs.filter(category=category)
        
    if status != 'all':
        if status == 'pending':
            qs = qs.filter(status__in=['Submitted', 'Assigned', 'In Progress'])
        elif status == 'resolved':
            qs = qs.filter(status__in=['Resolved', 'Closed'])
            
    if days != 'all':
        try:
            days_int = int(days)
            from django.utils import timezone
            import datetime
            threshold = timezone.now() - datetime.timedelta(days=days_int)
            qs = qs.filter(created_at__gte=threshold)
        except ValueError:
            pass
            
    data = []
    for c in qs:
        # Give a higher intensity to pending/unresolved issues
        intensity = 1.0 if c.status in ['Submitted', 'Assigned', 'In Progress'] else 0.5
        data.append([float(c.latitude), float(c.longitude), intensity])
        
    return JsonResponse({'data': data})

@login_required
def check_nearby_duplicates_view(request):
    """
    Finds active complaints within 100 meters of the given lat/lng for a specific category.
    """
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    category = request.GET.get('category')
    
    if not all([lat, lng, category]):
        return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)
        
    try:
        lat = float(lat)
        lng = float(lng)
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid coordinates'}, status=400)
        
    from .utils import haversine
    
    # Only check active complaints of the same category
    active_complaints = Complaint.objects.filter(
        category=category, 
        latitude__isnull=False, 
        longitude__isnull=False
    ).exclude(status__in=['Resolved', 'Closed'])
    
    duplicates = []
    for c in active_complaints:
        # Don't match against the user's own unresolved complaints if they are just editing
        # (Though this view is primarily used on create, so this shouldn't be an issue, but it's safe)
        dist = haversine(lat, lng, c.latitude, c.longitude)
        if dist <= 100: # 100 meters
            duplicates.append({
                'id': c.id,
                'title': c.title,
                'status': c.status,
                'distance': int(dist),
                'upvotes': c.votes.count()
            })
            
    # Sort by nearest
    duplicates.sort(key=lambda x: x['distance'])
    
    # Return top 5
    return JsonResponse({'status': 'success', 'duplicates': duplicates[:5]})

@login_required
def submit_feedback_view(request, id):
    complaint = get_object_or_404(Complaint, id=id, user=request.user)
    
    if request.method == 'POST' and complaint.status == 'Resolved' and complaint.citizen_confirmed_resolved is None:
        confirmed = request.POST.get('confirmed')
        feedback = request.POST.get('feedback', '')
        
        if confirmed == 'yes':
            rating = request.POST.get('rating')
            complaint.citizen_confirmed_resolved = True
            complaint.citizen_feedback = feedback
            try:
                complaint.citizen_rating = int(rating)
            except (ValueError, TypeError):
                pass
            complaint.save()
            messages.success(request, 'Thank you for confirming the resolution and providing your feedback!')
            
        elif confirmed == 'no':
            complaint.citizen_confirmed_resolved = False
            complaint.citizen_feedback = feedback
            complaint.status = 'In Progress'
            complaint.save()
            
            # Notify the department officers
            from users.models import User
            if complaint.department:
                officers = User.objects.filter(role='Department Officer', department=complaint.department)
                for officer in officers:
                    Notification.objects.create(
                        user=officer,
                        message=f'Citizen reported that issue "{complaint.title}" is not resolved. Reason: {feedback}'
                    )
            messages.warning(request, 'The issue has been reopened and the department has been notified.')
            
    return redirect('complaint_detail', id=complaint.id)

@login_required
def reassign_complaint_view(request, id):
    complaint = get_object_or_404(Complaint, id=id)
    
    if request.user.role != 'Admin':
        messages.error(request, 'Unauthorized access. Only admins can reassign complaints.')
        return redirect('complaint_detail', id=complaint.id)
        
    if request.method == 'POST':
        new_dept_id = request.POST.get('department_id')
        try:
            new_dept = Department.objects.get(id=new_dept_id)
            if complaint.department == new_dept:
                messages.info(request, f'Complaint is already assigned to {new_dept.department_name}.')
                return redirect('complaint_detail', id=complaint.id)
                
            old_dept_name = complaint.department.department_name if complaint.department else 'None'
            complaint.department = new_dept
            
            # Log this change
            complaint.remarks = f"{complaint.remarks or ''}\n\n[Admin Note: Reassigned from {old_dept_name} to {new_dept.department_name} by Admin]".strip()
            complaint.save()
            
            # Notify new department officer(s)
            from users.models import User
            officers = User.objects.filter(role='Department Officer', department=new_dept)
            officer_emails = []
            for officer in officers:
                Notification.objects.create(
                    user=officer,
                    message=f'Complaint "{complaint.title}" has been reassigned to your department by Admin.'
                )
                if officer.email:
                    officer_emails.append(officer.email)
                    
            if officer_emails:
                from config.email_utils import send_transactional_email
                site_url = request.build_absolute_uri('/')[:-1]
                send_transactional_email(
                    'New Issue Assignment',
                    'officer_assignment_email.html',
                    {'complaint': complaint, 'site_url': site_url},
                    officer_emails
                )
            
            messages.success(request, f'Complaint successfully reassigned to {new_dept.department_name}.')
        except Department.DoesNotExist:
            messages.error(request, 'Selected department does not exist.')
            
    return redirect('complaint_detail', id=complaint.id)

@login_required
def upload_evidence_view(request, id):
    complaint = get_object_or_404(Complaint, id=id)
    
    # Only Department Officers can upload evidence
    if request.user.role != 'Department Officer':
        messages.error(request, 'Unauthorized access. Only department officers can upload evidence.')
        return redirect('complaint_detail', id=complaint.id)
        
    if request.method == 'POST' and request.FILES.get('evidence'):
        complaint.resolved_image = request.FILES['evidence']
        complaint.save()
        messages.success(request, 'Evidence photo uploaded successfully.')
    else:
        messages.error(request, 'No image file was provided.')
        
    return redirect('complaint_detail', id=complaint.id)


def public_ledger_view(request):
    complaints_list = Complaint.objects.select_related('department', 'user').all().order_by('-created_at')
    
    # Filter functionality
    category = request.GET.get('category')
    status = request.GET.get('status')
    
    if category and category.strip():
        complaints_list = complaints_list.filter(category=category.strip())
    if status and status.strip():
        complaints_list = complaints_list.filter(status=status.strip())
        
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(complaints_list, 20) # 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'public_ledger.html', {
        'complaints': page_obj,
        'categories': [c[0] for c in Complaint.CATEGORY_CHOICES],
        'statuses': [s[0] for s in Complaint.STATUS_CHOICES if s[0] != 'Submitted']
    })
