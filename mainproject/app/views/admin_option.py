from rest_framework.response import Response
from rest_framework.decorators import api_view
import math
import json
from django.conf import settings
from pathlib import Path
from sqlalchemy import and_
from ..database import SessionLocal
from ..models import Account, Jobs, Company, EmployerProfile
from django.contrib.auth.hashers import make_password


def model_to_list_json(model_db, relation=False, relations_name=None):
    list_json = []
    for item in model_db:
        value_json = {c.name: getattr(item, c.name) for c in item.__table__.columns}
        if relation and relations_name:
            for link_name in relations_name:
                related_obj = getattr(item, link_name, None)
                if related_obj:
                    if isinstance(related_obj, list):
                        value_json[link_name] = [
                            {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
                            for obj in related_obj
                        ]
                    else:
                        value_json[link_name] = {
                            c.name: getattr(related_obj, c.name) for c in related_obj.__table__.columns
                        }
        list_json.append(value_json)
    return list_json


def model_to_json(mode_db, relation=False, relations_name=None):
    value_json = {c.name: getattr(mode_db, c.name) for c in mode_db.__table__.columns}
    if relation and relations_name:
        for link_name in relations_name:
            related_obj = getattr(mode_db, link_name, None)
            if related_obj:
                if isinstance(related_obj, list):
                    value_json[link_name] = [{c.name: getattr(obj, c.name) for c in obj.__table__.columns}
                                             for obj in related_obj]
                else:
                    value_json[link_name] = {
                        c.name: getattr(related_obj, c.name) for c in related_obj.__table__.columns
                    }
    return value_json


@api_view(["GET"])
def get_account(request):
    session = SessionLocal()
    try:
        search_value = request.GET.get("searchValue")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))
        skip = (page - 1) * limit

        query = session.query(Account)
        if search_value:
            if isinstance(search_value, str):
                search_value = json.loads(search_value)
            filters = []
            if search_value.get("email"):
                filters.append(Account.email.ilike(f"%{search_value['email']}%"))
            if filters:
                query = query.filter(and_(*filters))
        query = query.distinct()
        total = query.count()
        account = query.order_by(Account.email).offset(skip).limit(limit).all()
        list_account = model_to_list_json(account)
        return Response({
            "status": "Success",
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": math.ceil(total / limit),
            "listAccount": list_account
        })

    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PATCH"])
def change_password_by_admin(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        if account.role != "Admin":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là quản trị viên!"})

        value_change = request.data.get("valueChange")
        if not value_change:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        hashed_password = make_password(value_change["password"])
        account = session.query(Account).filter(Account.email == value_change["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy tài khoản"})

        account.password = hashed_password
        session.commit()
        return Response({"status": "Success"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


def delete_image(file_name):
    file_path = Path(settings.MEDIA_ROOT) / file_name
    if file_name and file_path.exists():
        file_path.unlink()


@api_view(["DELETE"])
def delete_account(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        if account.role != "Admin":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là quản trị viên!"})

        email = request.GET.get("email")
        if not email:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        account = session.query(Account).filter(Account.email == email).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy tài khoản"})
        if account.candidate and account.candidate.image:
            delete_image(account.candidate.image)
        if account.employer and account.employer.image:
            delete_image(account.employer.image)
        session.delete(account)
        session.commit()
        return Response({"status": "Success"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        job_id = request.GET.get("id")
        if not job_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Admin":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là quản trị viên!"})

        job = session.query(Jobs).filter(Jobs.id == job_id).first()
        if not job:
            return Response({"status": "Not Found", "message": "Không tìm thấy tuyển dụng!"})

        session.delete(job)
        session.commit()
        return Response({"status": "Success"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_company(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        company_id = request.GET.get("id")
        if not company_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Admin":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là quản trị viên!"})

        company = session.query(Company).filter(Company.id == company_id).first()
        if not company:
            return Response({"status": "Not Found", "message": "Không tìm thấy công ti cần xóa!"})

        employer_profile = session.query(EmployerProfile).filter(EmployerProfile.companyId == company_id).first()
        if employer_profile:
            employer_profile.companyId = None

        session.delete(company)
        session.commit()
        return Response({"status": "Success"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()