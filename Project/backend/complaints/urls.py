from django.urls import path
from . import views

urlpatterns = [
    path('report/', views.report_issue_view, name='report_issue'),
    path('my-complaints/', views.my_complaints_view, name='my_complaints'),
    path('<int:id>/', views.complaint_detail_view, name='complaint_detail'),
    path('<int:id>/edit/', views.edit_complaint_view, name='edit_complaint'),
    path('community/', views.community_dashboard_view, name='community_dashboard'),
    path('<int:id>/upvote/', views.upvote_complaint_view, name='upvote_complaint'),
    path('api/suggest-category/', views.suggest_category_view, name='suggest_category'),
    path('heatmap/', views.heatmap_view, name='heatmap'),
    path('api/heatmap-data/', views.heatmap_data_api_view, name='heatmap_data'),
    path('api/check-duplicates/', views.check_nearby_duplicates_view, name='check_duplicates'),
    path('<int:id>/feedback/', views.submit_feedback_view, name='submit_feedback'),
    path('<int:id>/upload-evidence/', views.upload_evidence_view, name='upload_evidence'),
    path('<int:id>/reassign/', views.reassign_complaint_view, name='reassign_complaint'),
    path('public-ledger/', views.public_ledger_view, name='public_ledger'),
    path('public-ledger/<int:id>/', views.public_complaint_detail_view, name='public_complaint_detail'),
]
