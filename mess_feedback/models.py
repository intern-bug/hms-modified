from django.contrib.auth import get_user_model
from django.db import models

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


