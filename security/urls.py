from django.urls import path
from . import views

app_name= 'security'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('scan/', views.scan, name='scan'),
    path('outing_action/<int:pk>', views.outing_action, name='outing_action'),
    path('outing-log', views.outing_log, name='outing-log'),
    path('generate-outing-sheet/', views.get_outing_sheet, name='generate_outing_sheet'),
]