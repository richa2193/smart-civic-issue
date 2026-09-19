from django.db import models
from django.conf import settings

class Department(models.Model):
    department_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    head_name = models.CharField(max_length=100)
    sla_days = models.IntegerField(default=7)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.department_name

class Worker(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='workers')
    specialization = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_workers')
    
    def __str__(self):
        return f"{self.name} ({self.specialization})" if self.specialization else self.name
