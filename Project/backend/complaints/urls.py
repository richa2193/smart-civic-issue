from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.report_issue_view, name='report_issue'),
    path('my-complaints/', views.my_complaints_view, name='my_complaints'),
    path('<int:id>/', views.complaint_detail_view, name='complaint_detail'),
    path('<int:id>/edit/', views.edit_complaint_view, name='edit_complaint'),
    path('community/', views.community_dashboard_view, name='community_dashboard'),
    path('<int:id>/upvote/', views.upvote_complaint_view, name='upvote_complaint'),
]
