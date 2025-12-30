from datetime import datetime, timedelta
import jwt
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
import random
import ulid
from ..models.Account import Account
from ..database import SessionLocal


def send_mail_code(to_email, code, template, title):
    infor = {
        "username": to_email,
        "code": code
    }
    html_message = render_to_string(template, infor)
    email = EmailMessage(title, html_message, settings.EMAIL_HOST_USER, [to_email])
    email.content_subtype = "html"
    email.send()


def generate_and_store_code(user_email):
    code = str(random.randint(100000, 999999))
    cache.set(f"reset_code:{user_email}", code, timeout=180)
    return code


def generate_custom_jwt(payload, expires_in=24 * 60 * 60):
    exp_time = datetime.utcnow() + timedelta(seconds=expires_in)
    payload["exp"] = int(exp_time.timestamp())
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


@api_view(["POST"])
def sign_up(request):
    session = SessionLocal()
    try:
        email_value = request.data.get("email")
        password_value = request.data.get("password")
        remember_login = request.data.get("remember")
        if email_value and password_value:
            exists_account = session.query(Account).filter(Account.email == email_value).first()
            if exists_account:
                return Response({"status": "Exists Account", "message": "Tài khoản này đã tồn tại"})
            else:
                account_id = str(ulid.new())
                hashed_password = make_password(password_value)
                new_account = Account(email=email_value, dateCreate=datetime.now(), password=hashed_password,
                                      role="Pending", id=account_id)
                session.add(new_account)
                session.commit()
                jwt_payload = {
                    "id": account_id,
                    "email": new_account.email,
                    "role": new_account.role
                }
                expires_in = 30 * 24 * 60 * 60 if remember_login else 24 * 60 * 60
                access_token = generate_custom_jwt(jwt_payload, expires_in=expires_in)
                response = Response({
                    "status": "Success",
                    "message": "Tạo tài khoản thành công"
                })
                response.set_cookie(
                    key="accessToken",
                    value=access_token,
                    httponly=True,
                    secure=False,
                    samesite="Lax",
                    max_age=expires_in
                )
                return response
        else:
            return Response({"status": "Empty Value", "message": "Email hay mật khẩu trống"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
def decode_jwt(request):
    try:
        encoded_jwt = request.COOKIES.get("accessToken")
        if encoded_jwt is None:
            return Response({"status": "Invalid Token", "message": "Không tìm thấy cookie"})

        decoded_token = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=["HS256"])
        exp_timestamp = decoded_token.get("exp")
        if not exp_timestamp:
            return Response({"status": "Invalid Token", "message": "Thiếu trường exp"})

        exp_time = datetime.utcfromtimestamp(exp_timestamp)
        current_time = datetime.utcnow()

        if exp_time < current_time:
            return Response({"status": "Expired", "message": "Token đã hết hạn"})

        expires_in = (exp_time - current_time).total_seconds()

        return Response({
            "status": "Success",
            "tokenJwt": decoded_token,
            "expiresIn": expires_in
        })

    except jwt.ExpiredSignatureError:
        response = Response({"status": "Expired Token", "message": "Token hết hạn"})
        response.delete_cookie(key="accessToken", samesite="Lax")
        return response
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


@api_view(["POST"])
def send_code(request):
    try:
        email_value = request.data.get("email")
        type_value = request.data.get("type")
        if email_value:
            session = SessionLocal()
            get_code = generate_and_store_code(email_value)
            if type_value == "Forgot":
                exists_email = session.query(Account).filter(Account.email == email_value).first()
                if exists_email:
                    send_mail_code(email_value, get_code, "code_repassword.html", "Lấy mã thay đổi mật khẩu")
                    session.close()
                    return Response({"status": "Success"})
                else:
                    session.close()
                    return Response({"status": "Not Found", "message": "Email này không tồn tại"})
            else:
                send_mail_code(email_value, get_code, "code_signin.html", "Xác nhận email")
                session.close()
                return Response({"status": "Success"})
        else:
            return Response({"status": "Empty Value", "message": "Trường email trống"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


@api_view(["POST"])
def verify_code(request):
    try:
        code_value = request.data.get("code")
        email_value = request.data.get("email")
        if email_value and code_value:
            cached_code = cache.get(f"reset_code:{email_value}")
            if cached_code:
                if cached_code == code_value:
                    return Response({"status": "Success", "message": "Mã xác thực hợp lệ"})
                else:
                    return Response({
                        "status": "Invalid",
                        "message": "Mã xác thực không đúng"
                    })
            else:
                return Response({
                    "status": "Expired or Invalid",
                    "message": "Mã đã hết hạn hoặc không tồn tại"
                })
        else:
            return Response({
                "status": "Invalid Input",
                "message": "Email và mã xác thực không được để trống"
            })
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


@api_view(["POST"])
def change_password_forget(request):
    try:
        email_value = request.data.get("email")
        password_value = request.data.get("password")
        if email_value and password_value:
            session = SessionLocal()
            account = session.query(Account).filter(Account.email == email_value).first()
            if account:
                hash_pass = make_password(password_value)
                account.password = hash_pass
                session.commit()
                session.close()
                return Response({"status": "Success"})
            else:
                session.close()
                return Response({"status": "Not Found", "message": "Tài khoản không tồn tại"})
        else:
            return Response({
                "status": "Invalid Input",
                "message": "Email và mật khẩu xác thực không được để trống"
            })
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


@api_view(["POST"])
def sign_in(request):
    session = SessionLocal()
    try:
        email_value = request.data.get("email")
        password_value = request.data.get("password")
        remember_login = request.data.get("remember")

        if not email_value or not password_value:
            return Response({"status": "Invalid Field", "message": "Tên tài khoản hoặc mật khẩu trống"})

        exists_account = session.query(Account).filter(Account.email == email_value).first()
        if not exists_account:
            return Response({"status": "Not Found", "message": "Tài khoản không tồn tại"})

        if not check_password(password_value, exists_account.password):
            return Response({"status": "Invalid Password", "message": "Sai mật khẩu"})

        jwt_payload = {"id": exists_account.id, "email": exists_account.email, "role": exists_account.role}
        expires_in = 30 * 24 * 60 * 60 if remember_login else 24 * 60 * 60
        access_token = generate_custom_jwt(jwt_payload, expires_in=expires_in)

        response = Response({
            "status": "Success",
            "message": "Đăng nhập thành công",
        })
        response.set_cookie(
            key="accessToken",
            value=access_token,
            httponly=True,
            samesite="Lax",
            secure=False,
            max_age=expires_in
        )
        return response

    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
def log_out(request):
    try:
        response = Response({"status": "Success"})
        response.delete_cookie(
            key="accessToken",
            samesite="Lax",
        )
        return response
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})

