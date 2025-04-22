from django.urls import path
from .views import ImageUploadView

app_name = 'uploads'

urlpatterns = [
    path('images/', ImageUploadView.as_view(), name='upload_image'),
] 