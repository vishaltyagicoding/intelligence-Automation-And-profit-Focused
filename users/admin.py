from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from .models import User, UserSession, EmailVerification, PasswordReset, DeviceFingerprint


# Helper function to check if user has full admin access
def has_full_admin_access(user):
    """Check if user has full admin access"""
    return user.is_superuser and user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_active', 'manual_subscription', 'trial_allowed', 'created_at']
    list_filter = ['manual_subscription', 'is_active', 'email_verified', 'trial_allowed', 'trial_used', 'is_staff']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    list_per_page = 50
    list_max_show_all = 200
    
    # Full fieldsets for alberttyagi123@gmail.com
    fieldsets = (
        ('Basic Information', {
            'fields': ('email', 'username', 'first_name', 'last_name', 'phone'),
        }),
        ('Password', {
            'fields': ('password',),
            'classes': ('collapse',),
        }),
        ('Subscription Management', {
            'fields': ('manual_subscription',),
            'description': 'Change to "activated" to activate subscription (payment info popup will appear)'
        }),
        ('Verification Status', {
            'fields': ('is_verified', 'email_verified', 'phone_verified'),
            'classes': ('collapse',),
        }),
        ('Trial Information', {
            'fields': ('trial_allowed', 'trial_used'),
            'classes': ('collapse',),
        }),
        ('Device Information', {
            'fields': ('device_id', 'registration_ip', 'registration_user_agent'),
            'classes': ('collapse',),
        }),
        ('Admin Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'classes': ('collapse',),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'last_login_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Limited fieldsets for other superusers (only subscription)
    limited_fieldsets = (
        ('User Information (Read Only)', {
            'fields': ('email', 'username', 'first_name', 'last_name'),
            'description': 'You can only view this information. Contact alberttyagi123@gmail.com to make changes.'
        }),
        ('Subscription Management', {
            'fields': ('manual_subscription',),
            'description': 'You can change subscription status between Activated/Deactivated'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'last_login_ip', 'device_id', 'registration_ip', 'registration_user_agent']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """
        Return different fieldsets based on user permissions
        - alberttyagi123@gmail.com: Full access to all fields
        - Other superusers: Only subscription field (activated/deactivated)
        """
        if obj is None:
            # Creating new user - only alberttyagi123@gmail.com can do this
            return self.add_fieldsets
        
        # Check if user is alberttyagi123@gmail.com or pythonbyvishal@gmail.com
        if has_full_admin_access(request.user):
            # Full access
            return self.fieldsets
        else:
            # Limited access - only subscription
            return self.limited_fieldsets
    
    def get_readonly_fields(self, request, obj=None):
        """
        Control which fields are read-only based on user permissions
        - alberttyagi123@gmail.com: Only system fields are readonly
        - Other superusers: Everything except manual_subscription is readonly
        """
        base_readonly = ['created_at', 'updated_at', 'last_login', 'last_login_ip', 
                        'device_id', 'registration_ip', 'registration_user_agent']
        
        if obj is None:
            return base_readonly
        
        # Check if user has full admin access
        if has_full_admin_access(request.user):
            # Full access - only system fields are readonly
            return base_readonly
        else:
            # Limited access - everything except manual_subscription is readonly
            return base_readonly + [
                'email', 'username', 'first_name', 'last_name', 'phone',
                'password', 'is_verified', 'email_verified', 'phone_verified',
                'trial_allowed', 'trial_used', 'is_active', 'is_staff', 'is_superuser'
            ]
    
    def has_add_permission(self, request):
        """
        Only alberttyagi123@gmail.com and pythonbyvishal@gmail.com can add new users
        Other superusers can only view and edit existing users
        """
        return has_full_admin_access(request.user)
    
    def has_delete_permission(self, request, obj=None):
        """
        Only alberttyagi123@gmail.com and pythonbyvishal@gmail.com can delete users
        Other superusers cannot delete
        """
        return has_full_admin_access(request.user)
    
    def get_urls(self):
        """Add custom URL for payment info popup"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/payment-info/',
                self.admin_site.admin_view(self.payment_info_view),
                name='users_user_payment_info',
            ),
        ]
        return custom_urls + urls
    
    def payment_info_view(self, request, object_id):
        """Handle payment info popup"""
        from payments.forms import PaymentInfoForm
        from payments.models import PaymentInfo
        
        # Any superuser can fill the payment info form
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can access this feature")
        
        try:
            user = User.objects.get(pk=object_id)
        except User.DoesNotExist:
            messages.error(request, "User not found")
            return redirect('admin:users_user_changelist')
        
        if request.method == 'POST':
            form = PaymentInfoForm(request.POST, request.FILES)
            if form.is_valid():
                # Validate username exists
                username = form.cleaned_data['user_name']
                try:
                    target_user = User.objects.get(username=username)
                except User.DoesNotExist:
                    messages.error(request, "User not valid.")
                    return render(request, 'admin/payment_info_popup.html', {
                        'form': form,
                        'user': user,
                        'title': 'Payment Information Required'
                    })
                
                # Create payment info
                payment_info = form.save(commit=False)
                payment_info.user = target_user
                payment_info.created_by = request.user
                payment_info.save()
                
                # Activate subscription
                target_user.manual_subscription = 'activated'
                target_user.save()
                
                messages.success(
                    request,
                    f'Payment info saved and subscription activated for {username}'
                )
                return redirect('admin:users_user_change', object_id)
        else:
            # Pre-fill form with user's username
            form = PaymentInfoForm(initial={'user_name': user.username})
        
        return render(request, 'admin/payment_info_popup.html', {
            'form': form,
            'user': user,
            'title': 'Payment Information Required'
        })
    
    def save_model(self, request, obj, form, change):
        """Intercept save to show payment info popup if activating subscription"""
        # Check if this is an update (not a new user)
        if change:
            # Get the original value before save
            try:
                original_obj = User.objects.get(pk=obj.pk)
                original_subscription = original_obj.manual_subscription
            except User.DoesNotExist:
                original_subscription = None
            
            # Get the new value from form
            new_subscription = form.cleaned_data.get('manual_subscription')
            
            # Check if changing from deactivated to activated
            if new_subscription == 'activated' and original_subscription == 'deactivated':
                # Any superuser can trigger the popup
                if request.user.is_superuser:
                    # Store the intent to activate in session
                    request.session['pending_activation_user_id'] = obj.pk
                    # Don't save the activation yet
                    return
        
        # Normal save for all other cases
        super().save_model(request, obj, form, change)
    
    def response_change(self, request, obj):
        """Redirect to payment info popup if activation is pending"""
        # Check if there's a pending activation
        pending_user_id = request.session.get('pending_activation_user_id')
        
        if pending_user_id and pending_user_id == obj.pk:
            # Clear the session
            del request.session['pending_activation_user_id']
            # Redirect to payment info popup
            return HttpResponseRedirect(
                reverse('admin:users_user_payment_info', args=[obj.pk])
            )
        
        return super().response_change(request, obj)
    
    actions = []


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['id', 'created_at', 'last_activity']
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_view_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can view"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_add_permission(self, request):
        """Only alberttyagi123@gmail.com can add"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_change_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can change"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_delete_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can delete"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'is_verified', 'attempts', 'created_at', 'expires_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['email', 'username']
    readonly_fields = ['id', 'created_at', 'verified_at', 'password_hash']
    
    fieldsets = (
        ('User Info', {'fields': ('email', 'username', 'first_name', 'last_name')}),
        ('Verification', {'fields': ('otp', 'is_verified', 'attempts', 'verified_at')}),
        ('Timestamps', {'fields': ('created_at', 'expires_at')}),
        ('Security', {'fields': ('password_hash', 'ip_address')}),
    )
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_view_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can view"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_add_permission(self, request):
        """Only alberttyagi123@gmail.com can add"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_change_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can change"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_delete_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can delete"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']



@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'is_used', 'attempts', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['email', 'user__email', 'user__username']
    readonly_fields = ['id', 'created_at', 'used_at']
    
    fieldsets = (
        ('User Info', {'fields': ('user', 'email')}),
        ('Reset Info', {'fields': ('otp', 'is_used', 'attempts', 'used_at')}),
        ('Timestamps', {'fields': ('created_at', 'expires_at')}),
        ('Security', {'fields': ('ip_address',)}),
    )
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_view_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can view"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_add_permission(self, request):
        """Only alberttyagi123@gmail.com can add"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_change_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can change"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_delete_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can delete"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']


@admin.register(DeviceFingerprint)
class DeviceFingerprintAdmin(admin.ModelAdmin):
    list_display = ['device_id_short', 'user', 'trial_granted', 'trial_count', 'is_blocked', 'first_seen', 'last_seen']
    list_filter = ['trial_granted', 'is_blocked', 'first_seen']
    search_fields = ['device_id', 'user__email', 'user__username', 'ip_address']
    readonly_fields = ['id', 'first_seen', 'last_seen']
    ordering = ['-last_seen']
    
    fieldsets = (
        ('Device Info', {'fields': ('device_id', 'user', 'ip_address', 'user_agent')}),
        ('Trial Info', {'fields': ('trial_granted', 'trial_count')}),
        ('Security', {'fields': ('is_blocked', 'block_reason')}),
        ('Timestamps', {'fields': ('first_seen', 'last_seen')}),
    )
    
    def device_id_short(self, obj):
        """Show shortened device ID"""
        return f"{obj.device_id[:16]}..." if len(obj.device_id) > 16 else obj.device_id
    device_id_short.short_description = 'Device ID'
    
    actions = ['block_devices', 'unblock_devices']
    
    def block_devices(self, request, queryset):
        """Block selected devices"""
        count = queryset.update(is_blocked=True, block_reason='Blocked by admin')
        self.message_user(request, f'{count} device(s) blocked successfully.')
    block_devices.short_description = 'Block selected devices'
    
    def unblock_devices(self, request, queryset):
        """Unblock selected devices"""
        count = queryset.update(is_blocked=False, block_reason=None)
        self.message_user(request, f'{count} device(s) unblocked successfully.')
    unblock_devices.short_description = 'Unblock selected devices'
    
    def has_module_permission(self, request):
        """Only alberttyagi123@gmail.com can access this module"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_view_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can view"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_add_permission(self, request):
        """Only alberttyagi123@gmail.com can add"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_change_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can change"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
    
    def has_delete_permission(self, request, obj=None):
        """Only alberttyagi123@gmail.com can delete"""
        return request.user.is_superuser and request.user.email in ['alberttyagi123@gmail.com', 'pythonbyvishal@gmail.com']
