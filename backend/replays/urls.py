"""Rutas de la API."""

from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("filters/", views.filter_options, name="filters"),
    path("overview/", views.overview, name="overview"),
    path("coach/", views.coach, name="coach"),
    path("maps/", views.maps, name="maps"),
    path("operators/", views.operators, name="operators"),
    path("trends/", views.trends, name="trends"),
    path("teammates/", views.teammates, name="teammates"),
    path("matches/", views.match_list, name="match-list"),
    path("matches/<int:pk>/", views.match_detail, name="match-detail"),
    path("unknown/", views.unknown, name="unknown"),
    path("overrides/", views.save_overrides, name="overrides"),
    path("import/", views.run_import, name="import"),
    path("import/status/", views.import_status, name="import-status"),
]
