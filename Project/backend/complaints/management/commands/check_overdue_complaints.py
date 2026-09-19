from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from complaints.models import Complaint, Notification
from users.models import User

class Command(BaseCommand):
    help = 'Checks for complaints that have exceeded their department SLA and marks them as overdue'

    def handle(self, *args, **options):
        now = timezone.now()
        # Find complaints that are not resolved/closed, not yet marked overdue, 
        # and where department SLA exists
        pending_complaints = Complaint.objects.exclude(status__in=['Resolved', 'Closed']).filter(is_overdue=False, department__isnull=False)
        
        overdue_count = 0
        
        for complaint in pending_complaints:
            sla_days = complaint.department.sla_days
            sla_deadline = complaint.created_at + timedelta(days=sla_days)
            
            if now > sla_deadline:
                complaint.is_overdue = True
                complaint.save(update_fields=['is_overdue'])
                overdue_count += 1
                
                # Notify the user
                Notification.objects.create(
                    user=complaint.user,
                    message=f'Your complaint "{complaint.title}" is taking longer than expected. It has been escalated.'
                )
                
                # Notify department officers
                officers = User.objects.filter(role='Department Officer', department=complaint.department)
                for officer in officers:
                    Notification.objects.create(
                        user=officer,
                        message=f'URGENT: Complaint "{complaint.title}" has breached the {sla_days}-day SLA and is now overdue.'
                    )
                    
                # Optionally notify Admins
                admins = User.objects.filter(role='Admin')
                for admin in admins:
                    Notification.objects.create(
                        user=admin,
                        message=f'SLA BREACH: Complaint "{complaint.title}" in {complaint.department.department_name} is overdue.'
                    )
                    
        self.stdout.write(self.style.SUCCESS(f'Successfully checked SLAs. Marked {overdue_count} complaints as overdue.'))
