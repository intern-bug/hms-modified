from django.contrib import admin
from security.models import Security, OutingInOutTimes

# Register your models here.
class SecurityAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_email', 'security_id', 'designation')

class OutingInOutTimesAdmin(admin.ModelAdmin):
    list_display = ('outing', 'outTime', 'inTime')

admin.site.register(Security, SecurityAdmin)
admin.site.register(OutingInOutTimes, OutingInOutTimesAdmin)