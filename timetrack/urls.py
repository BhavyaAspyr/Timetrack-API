# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('save_time_logs/', views.insert_time_data, name='save_time_logs'),
    path('update_time_log/', views.update_time_data, name='update_time_log'),
    path('track_hours/', views.track_hours, name='track_hours'),
    path('get-customer-names/', views.get_customer_names, name='get_customer_names'),
    path('get-projects-by-company/', views.get_projects_by_company, name='get_projects_by_company'),
    path('delete-time-log/', views.delete_time_log, name='delete_time_log'),
    path('search/', views.search_filter, name='search'),
    # path('advanced-search/', views.advanced_search, name='advanced_search'),
]
