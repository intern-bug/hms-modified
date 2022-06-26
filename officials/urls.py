from django.urls import path
from django.conf.urls.static import static 
from django.conf import settings
from . import views

app_name= 'officials'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('attendance/', views.attendance, name='attendance'),
    path('attendance-staff/', views.attendance_workers, name='attendance_workers'),
    path('attendance-log/', views.attendance_log, name='attendance_log'),
    path('generate-attendance-sheet/', views.generate_attendance_sheet, name='generate_attendance_sheet'),
    path('grant-outing/', views.grant_outing, name='grant_outing'),
    path('outing/<int:pk>', views.outing_detail, name='outing_detail'),
    path('block-layout/', views.blockSearch, name='blockSearch'),
    # path('search/',views.search, name='search'),

    path('student-list/', views.StudentListView.as_view(), name='student_list'),
    path('student/<int:pk>', views.StudentDetailView.as_view(), name='student_detail'),
    path('register-student/', views.StudentRegisterView.as_view(), name='register_student'),
    path('edit-student/<int:pk>', views.StudentUpdateView.as_view(), name='edit_student'),
    path('delete-student/<int:pk>', views.StudentDeleteView.as_view(), name='delete_student'),

    path('official-list/',views.OfficialListView.as_view(),name="emp_list"),
    path('register-official/', views.OfficialRegisterView.as_view(), name='register_official'),
    path('edit-official/<int:pk>', views.OfficialUpdateView.as_view(), name='edit_official'),
    path('delete-official/<int:pk>', views.OfficialDeleteView.as_view(), name='delete_official'),

    path('staff-list/',views.WorkerListView.as_view(),name="workers_list"),
    path('register-staff/', views.WorkerRegisterView.as_view(), name='register_worker'),
    path('edit-staff/<int:pk>', views.WorkerUpdateView.as_view(), name='edit_worker'),
    path('delete-staff/<int:pk>', views.WorkerDeleteView.as_view(), name='delete_worker'),

    path('complaint-list/', views.ComplaintListView.as_view(), name="complaint_list"),
    path('medical-issue-list/', views.MedicalIssueListView.as_view(), name="medical_issue_list"),
    path('outing-log', views.outing_log, name='outing-log'),
    path('generate-outing-sheet/', views.get_outing_sheet, name='generate_outing_sheet'),

    path('mess_feedback_analysis', views.mess_feedback_analysis, name='mess_feedback_analysis'),
    path('mess_rebate_action', views.mess_rebate_action, name='mess_rebate_action'),
    path('mess_rebate_log', views.mess_rebate_detail_log, name='mess_rebate_log'),
    path('vacation_mess_report', views.vacation_mess_report, name='vacation_mess_report'),
    path('vacation_list', views.vacation_student_details, name='vacation_list'),
    path('vacation-form/<int:pk>', views.VacationDetails.as_view(), name='vacation-form'),
    path('vacation-form/<int:pk>/edit', views.VacationEditView.as_view(), name='vacation-form-edit'),
    path('vacation_detail/<int:pk>', views.vacation_detail, name='vacation_detail'),
    # path('vacation-list', views.vacation_history, name='vacation-list'),

    path('announcement_new', views.AnnouncementCreateView.as_view(), name='announcement_new'),
    path('announcement/<int:pk>/edit', views.AnnouncementsEditView.as_view(), name='announcement-edit'),
    path('announcement/<int:pk>/delete', views.announcement_delete, name='announcement-delete'),
    path('announcement_list', views.announcements_list, name='announcement_list'),
    # path('water-cans/', views.watercan, name='watercan'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)