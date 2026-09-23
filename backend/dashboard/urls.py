from django.urls import path
from . import views

urlpatterns = [
    path("summary/", views.summary), path("by-sector/", views.by_sector),
    path("by-technician/", views.by_technician), path("by-category/", views.by_category),
    path("timeline/", views.timeline), path("export.csv", views.export_csv),
]
