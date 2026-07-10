from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend to allow login via either username or email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
            
        try:
            # Check if the user exists with either username or email
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
            
            # Check the password
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
            
        return None
