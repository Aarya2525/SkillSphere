from django.urls import path

from .views import EnrollmentListCreateView


urlpatterns = [
    path(
        "",
        EnrollmentListCreateView.as_view(),
        name="enrollment-list-create",
    ),
] 