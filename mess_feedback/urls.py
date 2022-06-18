from django.urls import path
from . import views

app_name = 'mess_feedback'

urlpatterns = [
    path('mess_feedback', views.mess_feedback_view, name='mess_feedback'),
]
