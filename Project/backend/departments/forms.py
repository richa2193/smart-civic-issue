from django import forms
from .models import Worker

class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ['name', 'phone_number', 'department', 'specialization', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full h-11 px-4 border border-slate-300 rounded-lg text-base text-slate-800 bg-white focus:outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-200 shadow-sm transition-colors', 'autocomplete': 'new-password'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full h-11 px-4 border border-slate-300 rounded-lg text-base text-slate-800 bg-white focus:outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-200 shadow-sm transition-colors', 
                'placeholder': '10-digit mobile number',
                'pattern': '[0-9]{10}',
                'autocomplete': 'new-password'
            }),
            'department': forms.Select(attrs={'class': 'w-full h-11 px-4 border border-slate-300 rounded-lg text-base text-slate-800 bg-white focus:outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-200 shadow-sm transition-colors'}),
            'specialization': forms.TextInput(attrs={'class': 'w-full h-11 px-4 border border-slate-300 rounded-lg text-base text-slate-800 bg-white focus:outline-none focus:border-slate-800 focus:ring-2 focus:ring-slate-200 shadow-sm transition-colors', 'placeholder': 'e.g. Electrical, Plumbing, Road Patching'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].empty_label = "Select a department"
