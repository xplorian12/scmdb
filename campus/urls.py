from django.urls import path
from . import views

app_name = "campus"

urlpatterns = [
    path("rosters/upload/", views.roster_upload_view, name="roster_upload"),
]
