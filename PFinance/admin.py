from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfiles'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Category)
admin.site.register(UserProfile)
admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(RecurringPayment)
admin.site.register(Alert)
admin.site.register(RecurringIncome)
