from django.urls import path
from .views import MediaUploadView

app_name = 'uploads'

urlpatterns = [
    path('media/', MediaUploadView.as_view(), name='upload_media'),
] 