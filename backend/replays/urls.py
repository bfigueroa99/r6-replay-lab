"""Rutas de la API."""

from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("filters/", views.filter_options, name="filters"),
    path("overview/", views.overview, name="overview"),
    path("coach/", views.coach, name="coach"),
    path("positioning/", views.positioning, name="positioning"),
    path("positioning/site-after-loss/", views.site_after_loss, name="site-after-loss"),
    path("operators/", views.operators, name="operators"),
    path("operators/catalog/", views.operator_catalog, name="operator-catalog"),
    path("operators/sites/", views.operators_by_site, name="operators-by-site"),
    path("operators/pool/", views.operators_pool, name="operators-pool"),
    path("operators/after-result/", views.operators_after_result,
         name="operators-after-result"),
    path("trends/", views.trends, name="trends"),
    path("teammates/", views.teammates, name="teammates"),
    path("duels/", views.duels, name="duels"),
    path("duels/death-state/", views.death_state, name="death-state"),
    path("duels/thrown-advantage/", views.thrown_advantage, name="thrown-advantage"),
    path("sessions/", views.sessions, name="sessions"),
    path("compare/", views.compare, name="compare"),
    path("players/<int:pk>/", views.player_detail, name="player-detail"),
    path("players/<int:pk>/ubisoft/", views.player_ubisoft, name="player-ubisoft"),
    path("matches/", views.match_list, name="match-list"),
    path("matches/<int:pk>/", views.match_detail, name="match-detail"),
    path("export/", views.export_table, name="export"),
    path("unknown/", views.unknown, name="unknown"),
    path("overrides/", views.save_overrides, name="overrides"),
    path("settings/", views.app_settings, name="settings"),
    path("backup/", views.make_backup, name="backup"),
    path("import/", views.run_import, name="import"),
    path("import/status/", views.import_status, name="import-status"),
    path("import/progress/", views.import_progress, name="import-progress"),
]
