import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

def send_transactional_email(subject, template_name, context, recipient_list):
    """
    Renders an HTML email template with text fallback and sends it.
    Wraps the send operation in a try/except to prevent SMTP errors from breaking the app.
    """
    try:
        # Render HTML content
        html_content = render_to_string(f'emails/{template_name}', context)
        # Create plain-text fallback
        text_content = strip_tags(html_content)
        
        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send(fail_silently=False)
        
        logger.info(f"Successfully sent email '{subject}' to {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email '{subject}' to {recipient_list}: {str(e)}")
        return False
