import json
from channels.layers import get_channel_layer
import jwt
import ulid
import os
import imghdr
from pathlib import Path
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from asgiref.sync import async_to_sync
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
from ..database import SessionLocal
from ..models import Account
from ..models import CandidateProfile
from ..models import EmployerProfile
from ..models import SaveJob
from ..models import SaveCompany
from ..models import Jobs
from ..models import Company
from ..models import JobRequire
from ..models import JobDecryption
from ..models import Applied
from ..models import EducationCandidate
from ..models import ExperienceCandidate
from ..models import ProjectCandidate
from ..models import Notify


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


def new_model_to_json(new_model_db, relation=False, relations_name=None):
    json_value = {}
    if hasattr(new_model_db, "__table__"):
        for column in new_model_db.__table__.columns:
            json_value[column.name] = getattr(new_model_db, column.name)
    if relation and relations_name:
        for link_name in relations_name:
            related_obj = getattr(new_model_db, link_name, None)
            if related_obj:
                if isinstance(related_obj, list):
                    json_value[link_name] = [{c.name: getattr(obj, c.name) for c in obj.__table__.columns}
                                             for obj in related_obj]
                else:
                    json_value[link_name] = {
                        c.name: getattr(related_obj, c.name) for c in related_obj.__table__.columns
                    }
    return json_value


status_dict = {
    "pending": "Chưa xem",
    "seen": "Đã xem",
    "accept": "Đã duyệt",
    "reject": "Đã bị từ chối"
}


def send_mail_notify(to_email, template, title, message):
    infor = {
        "username": to_email,
        "message": message,
        "title": title
    }
    html_message = render_to_string(template, infor)
    email = EmailMessage(title, html_message, settings.EMAIL_HOST_USER, [to_email])
    email.content_subtype = "html"
    email.send()


def delete_image(file_name):
    file_path = Path(settings.MEDIA_ROOT) / file_name
    if file_name and file_path.exists():
        file_path.unlink()


def save_image(account_id, image_file):
    if not image_file.content_type.startswith("image/"):
        return ""

    ext = imghdr.what(image_file)
    if ext not in ["jpeg", "jpg", "png", "gif", "webp"]:
        return ""

    file_name = f"{account_id}.{ext}"
    save_path = os.path.join(settings.MEDIA_ROOT, file_name)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        for chunk in image_file.chunks():
            f.write(chunk)
    return file_name


def handle_notify(
    session,
    job_id=None,
    company_id=None,
    employer_id=None,
    candidate_id=None,
    apply_id=None,
    title=None,
    message=None,
    type=None,
    value=None
):
    account_info = None

    # JOB
    if job_id:
        account = (session.query(Account)
                   .join(EmployerProfile, EmployerProfile.accountId == Account.id)
                   .join(Jobs, Jobs.employerId == EmployerProfile.id)
                   .filter(Jobs.id == job_id).first())
        if account:
            account_info = account

    # COMPANY
    if company_id:
        account = (session.query(Account)
                   .join(EmployerProfile, EmployerProfile.accountId == Account.id)
                   .filter(EmployerProfile.companyId == company_id).first())
        if account:
            account_info = account

    # EMPLOYER
    if employer_id:
        account = (session.query(Account)
                   .join(EmployerProfile, EmployerProfile.accountId == Account.id)
                   .filter(EmployerProfile.id == employer_id).first())
        if account:
            account_info = account

    # CANDIDATE
    if candidate_id:
        account = (session.query(Account)
                   .join(CandidateProfile, CandidateProfile.accountId == Account.id)
                   .filter(CandidateProfile.id == candidate_id).first())
        if account:
            account_info = account

    # APPLIED
    if apply_id:
        account = (session.query(Account)
                   .join(Applied, Applied.accountId == Account.id)
                   .filter(Applied.id == apply_id).first())
        if account:
            account_info = account

    # TẠO NOTIFY
    if account_info:
        new_notify = Notify(
            id=str(ulid.new()),
            accountId=account_info.id,
            title=title,
            message=message,
            type=type,
            value=json.dumps(value),
            status=False,
            dateCreate=datetime.now()
        )
        session.add(new_notify)

    return account_info


@api_view(["GET"])
def get_infor_account(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        if account.role == "Candidate":
            account_info = model_to_json(account, True, ["candidate", "exp", "education", "project"])
            return Response({"status": "Success", "accountInfo": account_info})

        if account.role == "Employer":
            account_info = model_to_json(account, True, ["employer"])
            return Response({"status": "Success", "accountInfo": account_info})

        return Response({"status": "Not Found", "message": "Không tìm thấy quyền người dùng"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PATCH"])
@parser_classes([MultiPartParser, FormParser])
def save_image_account(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        image_file = request.FILES.get("image")

        if not image_file:
            return Response({"status": "Not Found", "message": "Không tìm thấy ảnh"})

        if account.role == "Candidate":
            candidate = session.query(CandidateProfile).filter(
                CandidateProfile.accountId == account.id).first()
            if not candidate:
                return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng ứng viên"})

            name_image = save_image(candidate.id, image_file)
            if candidate.image and name_image:
                delete_image(candidate.image)
            candidate.image = name_image if name_image else candidate.image
            session.commit()
            return Response({"status": "Success", "image": candidate.image})
        elif account.role == "Employer":
            employer = session.query(EmployerProfile).filter(
                EmployerProfile.accountId == account.id).first()
            if not employer:
                return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng nhà tuyển dụng!"})

            name_image = save_image(employer.id, image_file)
            if employer.image and name_image:
                delete_image(employer.image)
            employer.image = name_image if name_image else employer.image
            session.commit()
            return Response({"status": "Success", "image": employer.image})
        else:
            return Response({"status": "Not Found", "message": "Không tìm thấy quyền tài khoản!"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def save_project_candidate(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        image_file = request.FILES.get("image")
        value_change = request.data.get("valueChange")

        if not value_change:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        try:
            value_change = json.loads(value_change)
        except json.JSONDecodeError:
            return Response({"status": "Invalid Value", "message": "Sai kiểu dữ liệu!"})

        if value_change.get("id"):
            project = session.query(ProjectCandidate).filter(ProjectCandidate.id == value_change["id"]).first()
            if not project:
                return Response({"status": "Not Found", "message": "Không tìm thấy dự án!"})

            project.name = value_change.get("name", project.name)
            project.field = value_change.get("field", project.field)
            project.executionTime = value_change.get("executionTime", project.executionTime)
            project.decryption = value_change.get("decryption", project.decryption)
            project.link = value_change.get("link", None)
            if project.image:
                delete_image(project.image)
            if image_file:
                project.image = save_image(project.id, image_file)
            session.commit()
            return Response({"status": "Success",
                             "updatedAccount": model_to_json(account,
                                                             True, ["candidate", "education", "exp", "project"])})

        new_id = str(ulid.new())
        file_name = None
        if image_file:
            file_name = save_image(new_id, image_file)
        new_project = ProjectCandidate(
            id=new_id,
            accountId=account.id,
            name=value_change["name"],
            executionTime=value_change["executionTime"],
            field=value_change["field"],
            link=value_change["link"],
            image=file_name,
            decryption=value_change["decryption"]
        )
        session.add(new_project)
        session.commit()
        return Response({"status": "Success",
                         "updatedAccount": model_to_json(account,
                                                         True, ["candidate", "education", "exp", "project"])})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PUT"])
def save_infor_candidate(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        change_value = request.data.get("valueChange")
        if not change_value:
            return Response({"status": "Not Found", "message": "Không tìm thấy dữ liệu"})

        if account.role != "Candidate":
            return Response({"status": "Not Found", "message": "Tài khoản này không phải là ứng viên!"})

        education_value = change_value.get("education")
        if education_value:
            if education_value.get("id"):
                education = session.query(EducationCandidate).filter(
                    EducationCandidate.id == education_value.get("id")).first()
                if not education:
                    return Response({"status": "Not Found", "message": "Không tìm thấy học vấn của ứng viên!"})
                education.name = education_value.get("name", education.name)
                education.degree = education_value.get("degree", education.degree)
                education.industry = education_value.get("industry", education.industry)
                education.course = education_value.get("course", education.course)
                education.decryption = education_value.get("decryption", education.decryption)
            else:
                new_education = EducationCandidate(
                    id=str(ulid.new()),
                    name=education_value["name"],
                    degree=education_value["degree"],
                    industry=education_value["industry"],
                    course=education_value["course"],
                    decryption=education_value["decryption"],
                    accountId=education_value["accountId"]
                )
                session.add(new_education)
            session.commit()

        exp_value = change_value.get("exp")
        if exp_value:
            if exp_value.get("id"):
                experience = session.query(ExperienceCandidate).filter(
                    ExperienceCandidate.id == exp_value["id"]).first()
                if not experience:
                    return Response({"status": "Not Found", "message": "Không tìm thấy kinh nghiệm của ứng viên!"})

                experience.field = exp_value.get("field", experience.field)
                experience.formOfWork = exp_value.get("formOfWork", experience.formOfWork)
                experience.company = exp_value.get("company", experience.company)
                experience.executionTime = exp_value.get("executionTime", experience.executionTime)
                experience.address = exp_value.get("address", experience.address)
                experience.decryption = exp_value.get("decryption", experience.decryption)
            else:
                new_experience = ExperienceCandidate(
                    id=str(ulid.new()),
                    accountId=exp_value["accountId"],
                    field=exp_value["field"],
                    formOfWork=exp_value["formOfWork"],
                    company=exp_value["company"],
                    executionTime=exp_value["executionTime"],
                    address=exp_value["address"],
                    decryption=exp_value["decryption"]
                )
                session.add(new_experience)
            session.commit()

        candidate_value = change_value.get("candidate")
        if candidate_value:
            exists_candidate = session.query(CandidateProfile).filter(
                CandidateProfile.accountId == account.id).first()
            if not exists_candidate:
                return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng ứng viên"})

            exists_candidate.name = candidate_value.get("name", exists_candidate.name)
            exists_candidate.birthday = datetime.strptime(candidate_value.get("birthday"),
                                                          "%Y-%m-%d").date() if candidate_value.get(
                "birthday") else exists_candidate.birthday
            exists_candidate.decryption = candidate_value.get("decryption", exists_candidate.decryption)
            exists_candidate.address = candidate_value.get("address", exists_candidate.address)
            exists_candidate.skills = candidate_value.get("skills", exists_candidate.skills)
            session.commit()

        return Response({"status": "Success",
                         "updatedAccount": model_to_json(account,
                                                         True, ["candidate", "education", "exp", "project"])})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_info_candidate(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        change_value = request.GET.get("valueChange")
        if not change_value:
            return Response({"status": "Invalid Value", "message": "Không thấy token và dữ liệu!"})
        try:
            change_value = json.loads(change_value)
        except json.JSONDecodeError:
            return Response({"status": "Invalid JSON", "message": "valueChange không phải JSON hợp lệ"})

        if account.role != "Candidate":
            return Response({"status": "Not Found", "message": "Tài khoản này không phải là ứng viên!"})

        if change_value.get("educationId"):
            education = session.query(EducationCandidate).filter(
                EducationCandidate.id == change_value["educationId"]).first()
            if not education:
                return Response({"status": "Not Found", "message": "Không tìm thấy học vấn ứng viên"})
            session.delete(education)
            session.commit()

        if change_value.get("expId"):
            exp = session.query(ExperienceCandidate).filter(ExperienceCandidate.id == change_value["expId"]).first()
            if not exp:
                return Response({"status": "Not Found", "message": "Không tìm thấy kinh nghiệm ứng viên"})
            session.delete(exp)
            session.commit()

        if change_value.get("projectId"):
            project = session.query(ProjectCandidate).filter(ProjectCandidate.id == change_value["projectId"]).first()
            if not project:
                return Response({"status": "Not Found", "message": "Không tìm thấy dự án ứng viên"})

            if project.image:
                delete_image(project.image)
            session.delete(project)
            session.commit()

        return Response({"status": "Success",
                         "updatedAccount": model_to_json(account,
                                                         True, ["candidate", "education", "exp", "project"])})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PUT"])
def save_infor_employer(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        change_value = request.data.get("valueChange")
        if not change_value:
            return Response({"status": "Invalid Value", "message": "Không thấy dữ liệu!"})

        if account.role == "Employer":
            exists_employer = session.query(EmployerProfile).filter(
                EmployerProfile.accountId == account.id).first()
            if not exists_employer:
                return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng ứng viên"})

            exists_employer.name = change_value.get("name", exists_employer.name)
            exists_employer.decryption = change_value.get("decryption", exists_employer.decryption)
            session.commit()
            return Response({"status": "Success", "updatedAccount": model_to_json(account, True, ["employer"])})
        else:
            return Response({"status": "Not Found", "message": "Tài khoản này không phải là nhà tuyển dụng!"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PATCH"])
def change_role(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        role_value = request.data.get("role")
        if not role_value:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        account.role = role_value
        id = str(ulid.new())
        if role_value == "Candidate":
            new_candidate = CandidateProfile(id=id, accountId=account.id)
            session.add(new_candidate)

        if role_value == "Employer":
            company_id = str(ulid.new())
            new_employer = EmployerProfile(id=id, accountId=account.id, companyId=company_id)
            new_company = Company(id=company_id, dateCreate=datetime.now(), isCrawl=False)
            session.add(new_employer)
            session.add(new_company)

        session.commit()
        jwt_payload = {"email": account.email, "role": role_value, "exp": decoded_token["exp"]}
        access_token = jwt.encode(jwt_payload, settings.SECRET_KEY, algorithm="HS256")
        response = Response({"status": "Success"})
        response.set_cookie(
            key="accessToken",
            value=access_token,
            samesite="Lax",
            httponly=True,
            secure=False,
            max_age=decoded_token["exp"]
        )
        return response
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
def save_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        job_id = request.data.get("id")
        if not job_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        new_save_job = SaveJob(id=str(ulid.new()), jobId=job_id, accountId=account.id, dateCreate=datetime.now(),
                               isFavorite=False)
        session.add(new_save_job)
        session.commit()
        return Response({"status": "Success", "saveJobId": new_save_job.id})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def check_save(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        job_id = request.GET.get("id")
        if not job_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        job = session.query(Jobs).filter(Jobs.id == job_id).first()
        if not job:
            return Response({"status": "Not Found", "message": "Không tìm thấy tuyển dụng"})

        save_job_id = ""
        save_company_id = ""

        exists_save_company = session.query(SaveCompany).filter((SaveCompany.companyId == job.companyId) &
                                                                (SaveCompany.accountId == account.id)).first()
        if exists_save_company:
            save_company_id = exists_save_company.id

        exists_save_job = session.query(SaveJob).filter((SaveJob.jobId == job_id) &
                                                        (SaveJob.accountId == account.id)).first()
        if exists_save_job:
            save_job_id = exists_save_job.id

        return Response({"status": "Success", "saveJobValue": {"job": save_job_id, "company": save_company_id}})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_save_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        save_id = request.GET.get("id")
        if not save_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        save_job_value = session.query(SaveJob).filter(SaveJob.jobId == save_id).first()
        if not save_job_value:
            return Response({"status": "Not Found", "message": "Không tìm thấy tuyển dụng đã lưu"})

        session.delete(save_job_value)
        session.commit()
        return Response({"status": "Success", "saveJobId": ""})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
def save_company(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        company_id = request.data.get("id")
        if not company_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        new_save_company = SaveCompany(id=str(ulid.new()), companyId=company_id, accountId=account.id,
                                       dateCreate=datetime.now(), isFavorite=False)
        session.add(new_save_company)
        session.commit()
        return Response({"status": "Success", "saveCompanyId": new_save_company.id})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_save_company(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        save_id = request.GET.get("id")
        if not save_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        save_company_value = session.query(SaveCompany).filter(
            SaveCompany.companyId == save_id).first()
        if not save_company_value:
            return Response({"status": "Not Found", "message": "Không tìm thấy công ty đã lưu"})

        session.delete(save_company_value)
        session.commit()
        return Response({"status": "Success", "saveCompanyId": ""})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_save_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        save_job_value = session.query(SaveJob).filter(SaveJob.accountId == account.id).all()
        list_save_job = model_to_list_json(save_job_value, True, ["job"])
        return Response({"status": "Success", "saveJobs": list_save_job})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_save_company(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        save_company_value = session.query(SaveCompany).filter(SaveCompany.accountId == account.id).all()
        list_save_company = model_to_list_json(save_company_value, True, ["company"])
        return Response({"status": "Success", "saveCompany": list_save_company})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_info_company_employer(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        if account.role != "Employer":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        if account.employer is None:
            return Response({"status": "Not Found", "message": "Không thấy thông tin của nhà tuyển dụng!"})

        exists_company = session.query(Company).filter(Company.id == account.employer.companyId).first()
        if not exists_company:
            return Response({"status": "Not Found", "message": "Không thấy thông tin công ty của nhà tuyển dụng!"})

        company_value = model_to_json(exists_company)
        return Response({"status": "Success", "company": company_value})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PUT"])
def save_company_employer(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        value_change = request.data.get("valueChange")
        if not value_change:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Employer":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        if account.employer is None:
            return Response({"status": "Not Found", "message": "Không thấy thông tin của nhà tuyển dụng!"})

        exists_company = session.query(Company).filter(Company.id == account.employer.companyId).first()
        if not exists_company:
            return Response({"status": "Not Found", "message": "Không thấy thông tin công ty của nhà tuyển dụng!"})

        exists_company.name = value_change.get("name", exists_company.name)
        exists_company.link = value_change.get("link", exists_company.link)
        exists_company.field = value_change.get("field", exists_company.field)
        exists_company.scale = value_change.get("scale", exists_company.scale)
        exists_company.address = value_change.get("address", exists_company.address)
        exists_company.decryption = value_change.get("decryption", exists_company.decryption)
        session.commit()
        return Response({"status": "Success", "updatedCompany": model_to_json(exists_company)})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PATCH"])
@parser_classes([MultiPartParser, FormParser])
def save_image_company_employer(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"status": "Invalid Value", "message": "Không thấy dữ liệu ảnh!"})

        if account.role != "Employer":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        if account.employer is None:
            return Response({"status": "Not Found", "message": "Không thấy thông tin của nhà tuyển dụng!"})

        exists_company = session.query(Company).filter(Company.id == account.employer.companyId).first()
        if not exists_company:
            return Response({"status": "Not Found", "message": "Không thấy thông tin công ty của nhà tuyển dụng!"})

        name_image = save_image(exists_company.id, image_file)
        exists_company.image = name_image if name_image else exists_company.image
        session.commit()
        return Response({"status": "Success", "image": exists_company.image})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
def edit_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        value = request.data.get("valueChange")
        if not value:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Employer":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})
        if account.employer is None:
            return Response({"status": "Not Found", "message": "Không có thông tin nhà tuyển dụng!"})

        job_id = value.get("id")
        if job_id:
            job = session.query(Jobs).filter((Jobs.id == job_id) & (Jobs.employerId == account.employer.id)).first()
            if not job:
                return Response({"status": "Not Found", "message": "Không tìm thấy tuyển dụng!"})

            job.name = value.get("name", job.name)
            job.address = value.get("address", job.address)
            job.sourceLink = value.get("link", job.sourceLink)
            if value.get("dateLimit"):
                job.dateLimit = datetime.strptime(value["dateLimit"], "%Y-%m-%d").date()

            session.query(JobRequire).filter(JobRequire.jobId == job.id).delete()

            for req in value.get("requires", []):
                if req.get("title") and req.get("requestText"):
                    session.add(JobRequire(
                        id=str(ulid.new()),
                        jobId=job.id,
                        title=req["title"],
                        requestText=req["requestText"]
                    ))

            session.query(JobDecryption).filter(JobDecryption.jobId == job.id).delete()

            for desc in value.get("desc", []):
                if desc.get("title") and desc.get("decryption"):
                    session.add(JobDecryption(
                        id=str(ulid.new()),
                        jobId=job.id,
                        title=desc["title"],
                        decryption=desc["decryption"],
                        order=desc["order"]
                    ))

        else:
            new_job = Jobs(
                id=str(ulid.new()),
                companyId=account.employer.companyId,
                employerId=account.employer.id,
                name=value.get("name"),
                sourceName="FUJobs",
                dateCreate=datetime.now(),
                dateLimit=datetime.strptime(value["dateLimit"], "%Y-%m-%d").date() if value.get("dateLimit") else None,
                sourceLink=value.get("link"),
                address=value.get("address"),
                isCrawl=False
            )
            session.add(new_job)

            for req in value.get("requires", []):
                session.add(JobRequire(
                    id=str(ulid.new()),
                    jobId=new_job.id,
                    title=req.get("title"),
                    requestText=req.get("requestText")
                ))

            for desc in value.get("desc", []):
                session.add(JobDecryption(
                    id=str(ulid.new()),
                    jobId=new_job.id,
                    title=desc.get("title"),
                    decryption=desc.get("decryption"),
                    order=desc.get("order")
                ))

        session.commit()
        return Response({"status": "Success"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_employer_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        job_id = request.GET.get("id")
        if not job_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Employer":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        if account.employer is None:
            return Response({"status": "Not Found", "message": "Không có thông tin nhà tuyển dụng!"})

        job_info = session.query(Jobs).filter((Jobs.id == job_id) & (Jobs.employerId == account.employer.id)).first()
        if not job_info:
            return Response({"status": "Not Found", "message": "Không có thông tin tuyển dụng!"})

        job_value = model_to_json(job_info, True, ["requires", "details"])
        return Response({"status": "Success", "job": job_value})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_employer_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        job_id = request.GET.get("id")
        if not job_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role not in ["Employer", "Admin"]:
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        if account.employer is None:
            return Response({"status": "Not Found", "message": "Không có thông tin nhà tuyển dụng!"})

        job = session.query(Jobs)
        if account.role == "Employer":
            job = job.filter((Jobs.id == job_id) & (Jobs.employerId == account.employer.id)).first()

        if account.role == "Admin":
            job = job.filter(Jobs.id == job_id).first()

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
def delete_employer_company(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        company_id = request.GET.get("id")
        if not company_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role not in ["Employer", "Admin"]:
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        if account.employer is None:
            return Response({"status": "Not Found", "message": "Không có thông tin nhà tuyển dụng!"})

        company = session.query(Company)
        if account.role == "Employer":
            company = company.filter(Company.id == account.employer.companyId).first()

        if account.role == "Admin":
            company = company.filter(Company.id == company_id).first()

        if not company:
            return Response({"status": "Not Found", "message": "Không tìm thấy tuyển dụng!"})

        session.delete(company)
        session.commit()
        return Response({"status": "Success"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_all_employer_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        name_job = request.GET.get("name")
        if account.role != "Employer":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        query = session.query(Jobs).filter(Jobs.employerId == account.employer.id)
        if name_job:
            query = query.filter(Jobs.name.ilike(f"%{name_job}%"))
        jobs = query.order_by(Jobs.dateCreate.desc()).all()

        job_value = model_to_list_json(jobs, True, ["requires", "details"])
        return Response({"status": "Success", "jobs": job_value})
    except jwt.ExpiredSignatureError:
        response = Response({"status": "Expired Token", "message": "Token hết hạn"})
        response.delete_cookie(
            key="accessToken",
            samesite="Lax",
        )
        return response
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


def string_model_json(mode_db, relation=False, relations_name=None):
    value_json = {}

    for c in mode_db.__table__.columns:
        val = getattr(mode_db, c.name)

        if hasattr(val, "isoformat"):
            value_json[c.name] = val.isoformat()
        else:
            value_json[c.name] = val

    if relation and relations_name:
        for link_name in relations_name:
            related_obj = getattr(mode_db, link_name, None)

            if related_obj:
                if isinstance(related_obj, list):
                    value_json[link_name] = [
                        string_model_json(obj) for obj in related_obj
                    ]
                else:
                    value_json[link_name] = string_model_json(related_obj)

    return value_json


@api_view(["POST"])
def apply_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        apply_value = request.data.get("applyValue")
        job_id = request.data.get("id")
        if not apply_value or not job_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Candidate":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là ứng viên!"})

        applied_id = apply_value.get("id")
        if applied_id:
            applied = session.query(Applied).filter((Applied.id == applied_id) & (Applied.status == "pending")).first()
            if not applied:
                return Response({"status": "Not Found", "message": "Không tìm thấy đơn ứng tuyển"})
            applied.decryption = apply_value.get("decryption", applied.decryption)
            session.commit()
            return Response({"status": "Success", "apply": model_to_json(applied)})

        target = handle_notify(
            session=session, job_id=job_id,
            title="Đơn ứng tuyển", message="Bạn nhận được một ứng tuyển",
            type="CandidateApply", value={"jobId": job_id}
        )
        if target:
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f"notify_{target.id}", {"type": "notify_send", "account_id": target.id, "message": "Bạn có một thông báo mới"}
            )
            job = session.query(Jobs).filter(Jobs.id == job_id).first()
            if job:
                send_mail_notify(
                    target.email,
                    "notify.html",
                    "Đơn ứng tuyển đến bạn",
                    f"{account.candidate.name} đã ứng tuyển đến tuyển dụng {job.name}")
        new_apply = Applied(
            id=str(ulid.new()),
            jobId=job_id,
            dateCreate=datetime.now(),
            accountId=account.id,
            status="pending",
            decryption=apply_value.get("decryption"),
            profile=json.dumps(string_model_json(account, True, ["candidate", "education", "exp", "project"]))
        )
        session.add(new_apply)
        session.commit()
        return Response({"status": "Success", "newApply": new_model_to_json(new_apply)})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PATCH"])
def handle_apply(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        apply_value = request.data.get("applyValue")
        if not apply_value:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Employer":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        applied = session.query(Applied).filter(Applied.id == apply_value["id"]).first()
        if not applied:
            return Response({"status": "Not Found", "message": "Không tìm thấy đơn ứng tuyển!"})

        applied.status = apply_value.get("status", applied.status)
        target = handle_notify(
            session=session, apply_id=applied.id,
            title="Đơn ứng tuyển", message="Nhà tuyển dụng đã xét duyệt hồ sơ của bạn!",
            type="EmployerApply", value={"jobId": applied.jobId}
        )
        if target:
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                f"notify_{target.id}", {"type": "notify_send", "account_id": target.id, "message": "Bạn có một thông báo mới"}
            )
            job = session.query(Jobs).filter(Jobs.id == applied.jobId).first()
            if job:
                status_name = status_dict.get(apply_value.get("status"), "được nhận xét")
                send_mail_notify(
                    target.email,
                    "notify.html",
                    "Duyệt đơn tuyển dụng",
                    f"Ứng tuyển tại {job.name} {status_name}"
                )
        session.commit()
        return Response({"status": "Success", "appliedUpdate": model_to_json(applied)})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_apply_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        applied_id = request.GET.get("id")
        if not applied_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Candidate":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là ứng viên!"})

        applied = session.query(Applied).filter(Applied.id == applied_id).first()
        if not applied:
            return Response({"status": "Not Found", "message": "Không tìm thấy đơn ứng tuyển"})

        session.delete(applied)
        session.commit()
        return Response({"status": "Success"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def check_apply(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        applied_id = request.GET.get("id")
        if not applied_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Candidate":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là ứng viên!"})

        applied = session.query(Applied).filter(Applied.accountId == account.id).first()

        return Response({"status": "Success", "applied": model_to_json(applied)})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_apply_job(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        if account.role == "Candidate":
            applied_job = session.query(Applied).filter(Applied.accountId == account.id).order_by(
                Applied.dateCreate.desc()).all()
            return Response({"status": "Success", "applies": model_to_list_json(applied_job, True, ["job"])})

        if account.role == "Employer":
            employer = account.employer
            applies = (
                session.query(Applied)
                .join(Jobs, Applied.jobId == Jobs.id)
                .filter(Jobs.employerId == employer.id)
                .order_by(Applied.dateCreate.desc())
                .all()
            )

            apply_value = model_to_list_json(applies, True, ["account", "job"])
            return Response({"status": "Success", "applies": apply_value})
        return Response({"status": "Invalid Role", "message": "Bạn không phải là ứng viên hoặc nhà tuyển dụng"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def preview_candidate(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        apply_id = request.GET.get("id")
        if not apply_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        if account.role != "Employer":
            return Response({"status": "Invalid Role", "message": "Bạn không phải là nhà tuyển dụng!"})

        candidate_profile = session.query(Applied).filter(Applied.id == apply_id).first()
        if not candidate_profile:
            return Response({"status": "Not Found", "message": "Không tìm thấy đơn ứng tuyển!"})

        if candidate_profile.status == "pending":
            candidate_profile.status = "seen"
            target = handle_notify(
                session=session, apply_id=candidate_profile.id,
                title="Đơn ứng tuyển", message="Nhà tuyển dụng đã xem hồ sơ của bạn!",
                type="EmployerApply", value={"jobId": candidate_profile.jobId}
            )
            if target:
                layer = get_channel_layer()
                async_to_sync(layer.group_send)(
                    f"notify_{target.id}", {"type": "notify_send", "account_id": target.id, "message": "Bạn có một thông báo mới"}
                )
                job = session.query(Jobs).filter(Jobs.id == candidate_profile.jobId).first()
                if job:
                    status_name = status_dict.get(candidate_profile.status, "được nhận xét")
                    send_mail_notify(
                        target.email,
                        "notify.html",
                        "Duyệt đơn tuyển dụng",
                        f"Ứng tuyển tại {job.name} {status_name}"
                    )
        session.commit()
        return Response(
            {
                "status": "Success",
                "applied": model_to_json(candidate_profile),
                "candidateProfile": json.loads(candidate_profile.profile)
            }
        )
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()
