import random
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import User
from .forms import CustomUserCreationForm, CustomAuthenticationForm

def generate_otp():
    return str(random.randint(100000, 999999))

from complaints.models import Complaint
from departments.models import Department

def home_view(request):
    # Live Statistics
    total_complaints = Complaint.objects.count()
    resolved_complaints = Complaint.objects.filter(status='Resolved').count()
    resolution_rate = int((resolved_complaints / total_complaints * 100)) if total_complaints > 0 else 0
    total_departments = Department.objects.count()
    
    # Public Complaints for Map (last 10 with locations)
    public_complaints = Complaint.objects.filter(latitude__isnull=False, longitude__isnull=False).order_by('-created_at')[:10]
    
    context = {
        'total_complaints': total_complaints,
        'resolved_complaints': resolved_complaints,
        'resolution_rate': resolution_rate,
        'total_departments': total_departments,
        'public_complaints': public_complaints,
        'geoapify_key': settings.GEOAPIFY_API_KEY
    }
    return render(request, 'home.html', context)

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # Will activate after OTP
            user.otp = generate_otp()
            user.save()
            
            # Send HTML OTP Email
            subject = 'Verify Your Account - Smart Civic Issue Reporting'
            html_content = render_to_string('emails/otp_email.html', {'otp': user.otp})
            text_content = strip_tags(html_content)
            
            email_msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send()
            
            request.session['verification_email'] = user.email
            messages.success(request, 'Registration successful. Please check your email for the OTP.')
            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def verify_otp_view(request):
    email = request.session.get('verification_email')
    if not email:
        return redirect('register')
        
    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            user = User.objects.get(email=email)
            if user.otp == otp:
                user.is_active = True
                user.is_verified = True
                user.otp = ''
                user.save()
                messages.success(request, 'Account verified successfully. You can now login.')
                del request.session['verification_email']
                return redirect('login')
            else:
                messages.error(request, 'Invalid OTP.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            
    return render(request, 'verify_otp.html')

def resend_otp_view(request):
    email = request.session.get('verification_email')
    if not email:
        return redirect('register')
        
    try:
        user = User.objects.get(email=email)
        user.otp = generate_otp()
        user.save()
        
        # Send HTML OTP Email
        subject = 'Verify Your Account - Smart Civic Issue Reporting'
        html_content = render_to_string('emails/otp_email.html', {'otp': user.otp})
        text_content = strip_tags(html_content)
        
        email_msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()
        
        messages.success(request, 'A new OTP has been sent to your email.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        
    return redirect('verify_otp')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            user.otp = generate_otp()
            user.save()
            
            # Send HTML OTP Email
            subject = 'Password Reset OTP - Smart Civic Issue Reporting'
            html_content = render_to_string('emails/reset_password_email.html', {'otp': user.otp})
            text_content = strip_tags(html_content)
            
            email_msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send()
            
            request.session['reset_email'] = user.email
            messages.success(request, 'OTP sent to your email.')
            return redirect('reset_password')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
            
    return render(request, 'forgot_password.html')

def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')
        
    if request.method == 'POST':
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        
        try:
            user = User.objects.get(email=email)
            if user.otp == otp:
                user.set_password(new_password)
                user.otp = ''
                user.save()
                messages.success(request, 'Password reset successfully. You can now login.')
                del request.session['reset_email']
                return redirect('login')
            else:
                messages.error(request, 'Invalid OTP.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            
    return render(request, 'reset_password.html')

def profile_view(request):
    return render(request, 'profile.html')
