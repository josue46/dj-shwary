from django.urls import path, include

urlpatterns = [
    path("shwary/", include("dj_shwary.urls", namespace="dj_shwary")),
]
