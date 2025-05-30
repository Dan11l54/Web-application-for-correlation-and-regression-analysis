from django.urls import path
from . import views

urlpatterns = [
    path('', views.analysis_view, name='analysis_view'),
    path('download-pdf/', views.download_pdf_view, name='download_pdf_view'),
]