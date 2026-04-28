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
    class Meta:
        model = UserProfile
        fields = ('profile_picture', 'address', 'date_of_birth', 'gender')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class UserUpdateForm(forms.ModelForm):
    """User update form"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number')
