from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Rating

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']



class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score', 'review']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'review': forms.Textarea(attrs={'placeholder': 'Write your review...'}),
        }
