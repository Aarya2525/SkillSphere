from django.urls import path

from .views import (
    CertificateCreateView,
    StudentCertificateListView,
    StudentCertificateDetailView,
    CertificateVerifyView,
)


urlpatterns = [
    # ============================================================
    # CERTIFICATE GENERATION
    # ============================================================

    path(
        "",
        CertificateCreateView.as_view(),
        name="certificate-create",
    ),

    # ============================================================
    # STUDENT CERTIFICATES
    # ============================================================

    path(
        "my/",
        StudentCertificateListView.as_view(),
        name="student-certificate-list",
    ),

    path(
        "<int:pk>/",
        StudentCertificateDetailView.as_view(),
        name="student-certificate-detail",
    ),

    # ============================================================
    # PUBLIC CERTIFICATE VERIFICATION
    # ============================================================

    path(
        "verify/<uuid:certificate_id>/",
        CertificateVerifyView.as_view(),
        name="certificate-verify",
    ),
] 