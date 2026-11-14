from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        password = request.data.get("password", "")

        if not email or not password:
            return Response(
                {"detail": "Email et mot de passe requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {"detail": "Identifiants incorrects."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {"detail": "Compte désactivé."},
                status=status.HTTP_403_FORBIDDEN,
            )

        login(request, user)
        return Response({
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_platform_admin": user.is_platform_admin,
            "preferred_locale": user.preferred_locale,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "Déconnecté."})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_platform_admin": user.is_platform_admin,
            "preferred_locale": user.preferred_locale,
        })
