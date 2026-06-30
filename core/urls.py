from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Páginas principales
    path('email/', views.inbox_view, name='inbox'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('sent/', views.sent_view, name='sent'),
    path('drafts/', views.drafts_view, name='drafts'),
    path('archived/', views.archived_view, name='archived'),
    path('trash/', views.trash_view, name='trash'),
    path('starred/', views.starred_view, name='starred'),
    path('compose/', views.compose_view, name='compose'),
    path('email/<int:pk>/', views.email_detail_view, name='email_detail'),
    
    # Acciones AJAX
    path('api/mark-read/', views.mark_as_read, name='mark_read'),
    path('api/mark-unread/', views.mark_as_unread, name='mark_unread'),
    path('api/archive/', views.archive_email, name='archive_email'),
    path('api/unarchive/', views.unarchive_email, name='unarchive_email'),
    path('api/delete/', views.delete_email, name='delete_email'),
    path('api/restore/', views.restore_email, name='restore_email'),
    path('api/permanent-delete/', views.permanent_delete_email, name='permanent_delete'),
    path('api/toggle-star/', views.toggle_star, name='toggle_star'),
    path('api/unread-count/', views.unread_count, name='unread_count'),

    path('resend-webhook/', views.resend_webhook, name='resend_webhook'),
]