import jwt
from django.conf import settings
from django.http import JsonResponse


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        check_paths = [
            "/api/account",
            "/api/admin",
            "/api/notify"
        ]

        if any(request.path.startswith(p) for p in check_paths):
            token = request.COOKIES.get("accessToken")
            if not token:
                return JsonResponse({"status": "Unauthorized", "message": "Không có token!"}, status=401)

            try:
                decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                request.decode_token = decoded
            except jwt.ExpiredSignatureError:
                response = JsonResponse({"status": "Expired Token", "message": "Token hết hạn!"}, status=401)
                response.delete_cookie(
                    key="accessToken",
                    samesite="Lax",
                )
                return response

            except Exception as ex:
                return JsonResponse({"status": "Invalid Token", "message": "Token không hợp lệ!", "error": str(ex)}, status=401)

            return self.get_response(request)

        return self.get_response(request)
