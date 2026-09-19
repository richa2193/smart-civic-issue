from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'full_name', 'phone', 'role')
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': True}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email or Username'
        
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_verified:
            raise forms.ValidationError(
                "This account is not verified. Please verify your email first.",
                code='inactive',
            )

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'profile_picture']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 mt-1 focus:ring-primary focus:border-primary'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 mt-1 focus:ring-primary focus:border-primary'}),
            'phone': forms.TextInput(attrs={'class': 'w-full border border-slate-200 rounded-lg px-4 py-2 mt-1 focus:ring-primary focus:border-primary'}),
        }
