from django.urls import path
from ..views.sign_option import (
    sign_up, decode_jwt, send_code, verify_code,
    change_password_forget, sign_in, log_out
)

urlpatterns = [
    path("sign_up/", sign_up),
    path("sign_in/", sign_in),
    path("log_out/", log_out),
    path("decode/", decode_jwt),
    path("send_code/", send_code),
    path("verify_code/", verify_code),
    path("change_password_forget/", change_password_forget),
]
