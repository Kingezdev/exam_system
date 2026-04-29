from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile


class UserRegistrationForm(UserCreationForm):
    """User registration form"""
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=User.USER_ROLES,
        required=True,
        help_text="Select your role in the system"
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        help_text="Enter your phone number"
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 
                 'phone_number', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.phone_number = self.cleaned_data['phone_number']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """User profile form"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = UserProfile
        fields = ('profile_picture', 'address', 'date_of_birth', 'gender')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to user fields
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control'})
        
        # If user instance is available, populate user fields
        if 'instance' in kwargs and kwargs['instance']:
            user = kwargs['instance'].user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['phone_number'].initial = user.phone_number
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        # Update user fields
        if hasattr(self, 'cleaned_data'):
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.phone_number = self.cleaned_data['phone_number']
            if commit:
                user.save()
        if commit:
            profile.save()
        return profile


class UserUpdateForm(forms.ModelForm):
    """User update form"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number')
