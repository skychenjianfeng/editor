from django.urls import path

from .auth_views import CsrfView, LoginView, LogoutView, MeView, RegisterView
from .views import (
    BatchCsvView,
    BatchView,
    DxfExportView,
    GeometryView,
    ModulesView,
    ParamSpecView,
    PngExportView,
    ProjectDetailView,
    ProjectListView,
    ProjectSchemeListView,
    ReportView,
    ResultsCsvView,
    RunDetailView,
    RunView,
    SchemeDetailView,
)

urlpatterns = [
    path("auth/csrf", CsrfView.as_view()),
    path("auth/register", RegisterView.as_view()),
    path("auth/login", LoginView.as_view()),
    path("auth/logout", LogoutView.as_view()),
    path("auth/me", MeView.as_view()),
    path("projects", ProjectListView.as_view()),
    path("projects/<uuid:project_id>", ProjectDetailView.as_view()),
    path("projects/<uuid:project_id>/schemes", ProjectSchemeListView.as_view()),
    path("schemes/<uuid:scheme_id>", SchemeDetailView.as_view()),
    path("catalog/param-spec/<slug:module>", ParamSpecView.as_view()),
    path("catalog/modules", ModulesView.as_view()),
    path("runs", RunView.as_view()),
    path("runs/<uuid:run_id>", RunDetailView.as_view()),
    path("report.docx", ReportView.as_view()),
    path("geometry", GeometryView.as_view()),
    path("export.dxf", DxfExportView.as_view()),
    path("export.png", PngExportView.as_view()),
    path("batches", BatchView.as_view()),
    path("export.batch.csv", BatchCsvView.as_view()),
    path("export.results.csv", ResultsCsvView.as_view()),
]
