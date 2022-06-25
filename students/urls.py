from django.urls import path

from . import views

app_name= 'students'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('outings', views.OutingListView.as_view(), name='outing_list'),
    path('outing/new', views.OutingCreateView.as_view(), name='outing_new'),
    # path('outing/<int:pk>/edit', views.OutingUpdateView.as_view(), name='outing_edit'),
    path('outing/<int:pk>/extend', views.OutingExtendView.as_view(), name='outing_extend'),
    path('outing/<int:pk>/cancel', views.cancel_outing, name='outing_cancel'),
    path('attendance_history', views.attendance_history, name='attendance_history'),
    path('outingQRCode/<int:pk>', views.outing_QRCode, name="outing_QRCode"),
    path('outingDetails/<int:pk>', views.outing_details, name="outing_details"),
    path('vacation_form_download', views.vacation_form_download, name='vacation_form_downlaod'),
    path('vacation_history', views.vacation_history, name='vacation_history'),
    
]