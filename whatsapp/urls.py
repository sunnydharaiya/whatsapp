from django.urls import path
from .views import run_campaign

urlpatterns = [
    path("run/<int:campaign_id>/", run_campaign),
    
]
