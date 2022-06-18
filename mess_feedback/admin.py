from django.contrib import admin
from .models import MessFeedback

# Register your models here.
class MessFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'type', 'rating', 'review')
admin.site.register(MessFeedback, MessFeedbackAdmin)
