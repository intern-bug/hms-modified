from secrets import choice
from django.db import models
from django.conf import settings


# Create your models here.
class Security(models.Model):
    DESIGNATION_CHOICES = (('Superintendent', 'Superintendent'),
                            ('Chief', 'Chief'))
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    account_email = models.EmailField(unique=True, null=False)
    security_id = models.CharField(unique=True, null=False, max_length=20)
    designation = models.CharField(max_length=50, choices=DESIGNATION_CHOICES)

    def __str__(self):
        return str(self.security_id)

class OutingInOutTimes(models.Model):
    outing = models.ForeignKey('students.Outing', on_delete=models.CASCADE, null=False)
    outTime = models.DateTimeField(auto_now_add=True)
    inTime = models.DateTimeField(null=True, blank=True)
    remark_by_security = models.TextField(null=True)


    class Meta:
        ordering = ['-outTime']
        managed = True

