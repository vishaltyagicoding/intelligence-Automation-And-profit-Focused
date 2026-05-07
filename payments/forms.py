from django import forms
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import PaymentInfo


class PaymentInfoForm(forms.ModelForm):
    """
    Form for Payment Info with validation
    """
    user_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'vTextField',
            'placeholder': 'Enter username',
        }),
        help_text='Username must exist in User table'
    )
    
    subscription_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        widget=forms.NumberInput(attrs={
            'class': 'vTextField',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01',
        }),
        help_text='Enter numeric value only (e.g., 99.99)'
    )
    
    payment_valid_image = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'vFileField',
            'accept': 'image/*',
        }),
        help_text='Upload payment proof image (JPG, PNG, etc.)'
    )
    
    class Meta:
        model = PaymentInfo
        fields = ['user_name', 'subscription_price', 'payment_valid_image']
    
    def clean_user_name(self):
        """Validate that username exists"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        username = self.cleaned_data.get('user_name')
        if username:
            try:
                User.objects.get(username=username)
            except User.DoesNotExist:
                raise ValidationError("User not valid.")
        return username
    
    def clean_subscription_price(self):
        """Validate that price is numeric and positive"""
        price = self.cleaned_data.get('subscription_price')
        if price is not None:
            if price <= 0:
                raise ValidationError("Subscription price must be greater than 0")
        return price
    
    def clean_payment_valid_image(self):
        """Validate that uploaded file is an image"""
        image = self.cleaned_data.get('payment_valid_image')
        if image:
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_name = image.name.lower()
            if not any(file_name.endswith(ext) for ext in valid_extensions):
                raise ValidationError(
                    "Only image files are allowed (JPG, PNG, GIF, BMP, WEBP)"
                )
        
        return image
