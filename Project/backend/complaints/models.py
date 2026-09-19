from django.db import models
from django.conf import settings
from departments.models import Department

class Complaint(models.Model):
    CATEGORY_CHOICES = (
        ('Road Damage', 'Road Damage'),
        ('Garbage', 'Garbage'),
        ('Street Light', 'Street Light'),
        ('Water Leakage', 'Water Leakage'),
        ('Drainage', 'Drainage'),
        ('Traffic Signal', 'Traffic Signal'),
        ('Electricity', 'Electricity'),
        ('Public Toilet', 'Public Toilet'),
        ('Illegal Dumping', 'Illegal Dumping'),
        ('Tree Fallen', 'Tree Fallen'),
        ('Others', 'Others'),
    )
    
    STATUS_CHOICES = (
        ('Submitted', 'Submitted'),
        ('Assigned', 'Assigned'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='complaint_images/', blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Submitted')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_overdue = models.BooleanField(default=False)
    
    # Citizen Feedback fields
    citizen_rating = models.IntegerField(null=True, blank=True)
    citizen_feedback = models.TextField(null=True, blank=True)
    citizen_confirmed_resolved = models.BooleanField(null=True, blank=True)
    
    # Resolution Evidence
    resolved_image = models.ImageField(upload_to='resolution_evidence/', blank=True, null=True)

    # Worker Assignment (Optional)
    assigned_worker = models.ForeignKey('departments.Worker', on_delete=models.SET_NULL, null=True, blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)


    def __str__(self):
        return f"{self.title} - {self.status}"


class Votes(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'complaint')

    def __str__(self):
        return f"Vote by {self.user} on {self.complaint}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user}"
