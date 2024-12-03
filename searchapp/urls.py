from django.urls import path
from .views import SearchTimetrackView

urlpatterns = [
    path('search/', SearchTimetrackView.as_view(), name='search-timetrack'),
]
