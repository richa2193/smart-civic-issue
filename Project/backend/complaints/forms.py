from django import forms
from .models import Complaint

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'image', 'latitude', 'longitude', 'address']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type or let map detect location'}),
        }
