from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.throttling import AnonRateThrottle

class ThrottledTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [AnonRateThrottle]
    throttle_scope = "auth"
from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view()),
    path("login/", ThrottledTokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
    path("me/", views.MeView.as_view()),
    path("geocode/", views.GeocodeView.as_view()),
]
