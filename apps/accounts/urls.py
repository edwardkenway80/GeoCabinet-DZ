from django.urls import path
from .views import CSRFTokenView, LoginView, LogoutView, CurrentUserView

urlpatterns = [
    path("csrf/", CSRFTokenView.as_view(), name="csrf-token"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
]
