from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()

# Create your models here.
class MessFeedback(models.Model):
    TYPE_CHOICES = (
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Snacks', 'Snacks'),
        ('Dinner', 'Dinner')    
    ) 
    RATING_CHOICES = (
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(null=False)
    type = models.CharField(max_length=9, choices=TYPE_CHOICES) 
    rating = models.IntegerField(null=False, choices=RATING_CHOICES)
    review = models.TextField(null=True)

    def entity(self):
        return self.user.entity()
    
def get_type():
    present_time = (timezone.now().hour*100)+(timezone.now().minute)
    if present_time >= 200 and present_time <= 500:
        return 'Breakfast'
    elif present_time >= 630 and present_time <= 930:
        return 'Lunch'
    elif present_time >= 1100 and present_time <= 1330:
        return 'Snacks'
    elif present_time >= 1400 and present_time <= 1700:
        return 'Dinner'
    else:
        return None


