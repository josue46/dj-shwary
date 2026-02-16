from django.urls import path
from .views import ShwaryWebhookView

app_name = "dj_shwary"

urlpatterns = [
    path("webhook/", ShwaryWebhookView.as_view(), name="webhook"),
]