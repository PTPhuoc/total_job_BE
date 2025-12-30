import json
import time
from threading import Thread
import jwt
import ulid
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..crawl import topCV
from ..crawl import carryViet
from django.core.cache import cache
from ..models.Catalog import Catalogs
import re
from datetime import datetime
from ..database import SessionLocal
from ..models.Company import Company
from ..models.JobDecryption import JobDecryption
from ..models.Jobs import Jobs
from ..models.JobRequire import JobRequire
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import os
import requests
from django.conf import settings
from ..models import Account


def model_to_json(model_db, relation=False, relations_name=None):
    list_job = []
    for item in model_db:
        job_json = {c.name: getattr(item, c.name) for c in item.__table__.columns}

        if relation and relations_name:
            for link_name in relations_name:
                related_obj = getattr(item, link_name, None)
                if related_obj:
                    if isinstance(related_obj, list):
                        job_json[link_name] = [
                            {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
                            for obj in related_obj
                        ]
                    else:
                        job_json[link_name] = {
                            c.name: getattr(related_obj, c.name) for c in related_obj.__table__.columns
                        }
        list_job.append(job_json)
    return list_job


def save_image(link_image, name_image):
    try:
        if "logo_default.png" in link_image.lower():
            return "noImage"

        response = requests.get(link_image, stream=True, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            ext = {
                "image/jpeg": "jpg",
                "image/png": "png",
                "image/gif": "gif",
                "image/webp": "webp"
            }.get(content_type, "jpg")
            filename = f"{name_image}.{ext}"
            save_path = os.path.join(settings.MEDIA_ROOT, filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            return filename
        else:
            print(f"Lỗi tải ảnh {link_image}: {response.status_code}")
            return "noImage"
    except Exception as e:
        print(f"Lỗi lưu ảnh: {e}")
    return "noImage"


def string_to_date(text):
    match = re.search(r"\d{2}/\d{2}/\d{4}", text)
    if match:
        date_obj = datetime.strptime(match.group(), "%d/%m/%Y").date()
        return date_obj
    else:
        return datetime.now()


def progress_report(layer, task_id, state, message):
    try:
        print(f"[REPORT] Sending to task_{task_id}: {state}, {message}")
        async_to_sync(layer.group_send)(
            f"task_{task_id}", {"type": "task_send", "state": state, "message": message}
        )
    except Exception as e:
        print("[ERROR] Không thể gửi WebSocket:", e)


def change_title(key):
    title = key
    if key.lower() in ["mức lương", "thu nhập"]:
        title = "Lương"
    return title


def change_field(value, list_catalog, title):
    if title.lower() in "nghề":
        if list_catalog:
            value = value.lower()
            for catalog in list_catalog:
                if value in catalog["name"].lower():
                    return catalog["name"]

                for sub in catalog.get("subcatalogs", []):
                    if value in sub["name"].lower():
                        return sub["name"]
            return ""
    else:
        return value


def insert_data_topcv(list_job, task_id):
    layer = get_channel_layer()
    session = SessionLocal()
    list_catalog = []
    catalogs = session.query(Catalogs).all()
    if catalogs:
        list_catalog = model_to_json(catalogs, True, ["subcatalogs"])
    for item in list_job:
        try:
            progress_report(layer, task_id, "on",
                            f"Đang kiểm tra tuyển dụng {item.job.name} của công ty {item.company.name}")
            exists_job = session.query(Jobs).filter(Jobs.name == item.job.name).first()
            exists_company = session.query(Company).filter(Company.name == item.company.name).first()
            if exists_job is None:
                company_id = item.company.id
                date_limit = string_to_date(item.job.date_create)
                if exists_company:
                    company_id = exists_company.id
                    progress_report(layer, task_id, "on", f"Công ty {item.company.name} đã tồn tại!")
                else:
                    path_image = save_image(item.company.image, item.company.id)
                    new_company = Company(id=item.company.id, name=item.company.name, link=item.company.link,
                                          address=item.company.address, image=path_image, scale=item.company.scale,
                                          field=item.company.field, decryption=item.company.decryption, isCrawl=True,
                                          dateCreate=datetime.now())
                    session.add(new_company)
                    progress_report(layer, task_id, "on", "Thêm thành công thông tin công ty!")
                new_job = Jobs(id=item.job.id, companyId=company_id, name=item.job.name.strip(), sourceName="TopCV",
                               dateCreate=datetime.now(), dateLimit=date_limit, sourceLink=item.job.link,
                               address=item.job.address, isCrawl=True)
                session.add(new_job)
                progress_report(layer, task_id, "on", "Thêm thành công thông tin tuyển dụng!")
                if len(item.job_req) > 0:
                    for req in item.job_req:
                        text_title = change_title(req.name)
                        text_field = change_field(req.field, list_catalog, text_title)
                        if text_field:
                            new_job_req = JobRequire(id=req.id, jobId=item.job.id, title=text_title,
                                                     requestText=text_field)
                            session.add(new_job_req)
                    progress_report(layer, task_id, "on", "Thêm thành công yêu cầu công việc!")
                else:
                    progress_report(layer, task_id, "on", "Yêu cầu công việc không có dữ liệu!")
                if len(item.job_desc) > 0:
                    index = 0
                    for desc in item.job_desc:
                        new_job_desc = JobDecryption(id=desc.id, jobId=item.job.id, title=desc.title,
                                                     decryption=desc.decryption, order=index)
                        index += 1
                        session.add(new_job_desc)
                    progress_report(layer, task_id, "on", "Thêm thành công mô tả công việc!")
                else:
                    progress_report(layer, task_id, "on", "Mô tả công việc không có dữ liệu!")
            else:
                progress_report(layer, task_id, "on", "Tuyển dụng này đã tồn tại!")
        except Exception as ex:
            progress_report(layer, task_id, "off", f"Không thể thêm dữ liệu từ link: {item.job.link}\nLỗi: {str(ex)}")
    session.commit()
    session.close()


def handle_crawl(task_id):
    for _ in range(10):
        state_client = cache.get(f"state_{task_id}")
        if state_client:
            layer = get_channel_layer()
            cache.set("stateCrawl", json.dumps({"state": "on", "taskId": task_id}), timeout=None)
            progress_report(layer, task_id, "on", "Đang lấy dữ liệu...")
            try:
                list_detail_infor = topCV.start_crawl(layer, task_id)
                if not list_detail_infor:
                    raise ValueError("Danh sách trống")

                progress_report(layer, task_id, "on", "Bắt đầu lưu dữ liệu...")
                insert_data_topcv(list_detail_infor, task_id)
                progress_report(layer, task_id, "off", "Hoàn tất crawl dữ liệu!")
            except Exception as e:
                progress_report(layer, task_id, "off", f"Lỗi crawl: {e}")
            finally:
                break

        time.sleep(1)
    cache.set("stateCrawl", json.dumps({"state": "off", "taskId": ""}), timeout=300)


@api_view(["GET"])
def active_craw_topcv(request):
    session = SessionLocal()
    try:
        encoded_jwt = request.COOKIES.get("accessToken")

        if not encoded_jwt:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        decoded = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=["HS256"])
        account = session.query(Account).filter(Account.email == decoded.get("email")).first()

        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy tài khoản"})
        if account.role != "Admin":
            return Response({"status": "Invalid Role", "message": "Thiếu quyền truy cập!"})

        task_id = str(ulid.new())
        cache.set("stateCrawl", json.dumps({"state": "on", "taskId": task_id}), timeout=None)
        thread_crawl = Thread(target=handle_crawl, args=(task_id,))
        thread_crawl.start()
        return Response({"status": "Success", "taskId": task_id})
    except Exception as ex:
        print(ex)
        return Response({"message": "Server Error", "error": str(ex)})


@api_view(["GET"])
def check_crawl(request):
    try:
        check_state = cache.get("stateCrawl")
        task_id = ""
        if check_state:
            check_state = json.loads(check_state)
            if check_state["state"] == "on":
                task_id = check_state["taskId"]

        return Response({"status": "Success", "taskId": task_id})
    except Exception as ex:
        print(ex)
        return Response({"message": "Server Error", "error": str(ex)})
