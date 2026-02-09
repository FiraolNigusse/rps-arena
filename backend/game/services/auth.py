from django.http import JsonResponse
from functools import wraps
from game.models import User
from game.services.jwt_service import decode_jwt


def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Missing token"}, status=401)

        token = auth_header.split(" ")[1]
        payload = decode_jwt(token)

        if not payload:
            return JsonResponse({"error": "Invalid or expired token"}, status=401)

        try:
            request.user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper
