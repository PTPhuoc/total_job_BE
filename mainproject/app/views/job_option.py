import json
from sqlalchemy import or_
from rest_framework.response import Response
from rest_framework.decorators import api_view
from sqlalchemy import func, and_
import pandas as pd
from ..database import SessionLocal
from ..models.Jobs import Jobs
from ..models.JobDecryption import JobDecryption
from ..models.JobRequire import JobRequire
from ..models.Account import Account
from ..models.SaveJob import SaveJob
import re
from sentence_transformers import SentenceTransformer, util
import joblib
import torch
from ..data_ml.linking_word import advanced_phrase_linking, load_linking_patterns, clean_text
from underthesea import word_tokenize
from datetime import datetime
import pytz
import math


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
def get_job(request):
    session = SessionLocal()
    try:
        search_value = request.GET.get("searchValue")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))
        skip = (page - 1) * limit

        query = session.query(Jobs).join(JobRequire, isouter=True).filter(Jobs.dateLimit >= datetime.now())
        if search_value:
            if isinstance(search_value, str):
                search_value = json.loads(search_value)
            filters = []
            if search_value.get("job"):
                filters.append(Jobs.name.ilike(f"%{search_value['job']}%"))
            if search_value.get("address"):
                filters.append(Jobs.address.ilike(f"%{search_value['address']}%"))

            for key in ["career", "salary", "exp", "formOfWork"]:
                if search_value.get(key):
                    filters.append(JobRequire.requestText.ilike(f"%{search_value[key]}%"))
            if filters:
                query = query.filter(and_(*filters))
        query = query.distinct()
        total = query.count()
        jobs = query.order_by(Jobs.dateCreate.desc()).offset(skip).limit(limit).all()
        list_job = model_to_list_json(jobs, True, ["company", "requires"])
        return Response({
            "status": "Success",
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": math.ceil(total / limit),
            "listJob": list_job
        })

    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_one_job(request):
    session = SessionLocal()
    try:
        job_id = request.GET.get("id")
        if job_id:
            job = session.query(Jobs).filter(Jobs.id == job_id).first()
            if job:
                job_data = model_to_json(job, True, ["company", "requires", "employer"])
                return Response({"status": "Success", "job": job_data})
            else:
                return Response({"status": "Success", "job": {}})
        else:
            return Response({"status": "Not Found", "message": "Mã công việc không hợp lệ!"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_job_desc(request):
    session = SessionLocal()
    try:
        jobId = request.GET.get("id")
        if jobId:
            job_detail = session.query(JobDecryption).filter(JobDecryption.jobId == jobId).all()
            if job_detail:
                list_job_detail = model_to_list_json(job_detail)
                return Response({"status": "Success", "jobDesc": list_job_detail})
            else:
                return Response({"status": "Success", "jobDetail": []})
        else:
            return Response({"status": "Invalid Value", "message": "Mã tuyển dụng trống"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def check_content(request):
    session = SessionLocal()
    try:
        job_id = request.GET.get("id")
        if not job_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        job_desc = session.query(JobDecryption).filter(JobDecryption.jobId == job_id).all()
        if not job_desc:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        model = joblib.load("app/data_ml/model_detect.pkl")
        vectorizer = joblib.load("app/data_ml/vectorizer_model_detect.pkl")
        st_model = SentenceTransformer("app/data_ml/sentence_finetuned")
        data_scam_template = joblib.load("app/data_ml/scam_encode.pkl")
        scam_embeddings = data_scam_template["embeddings"]
        threshold = joblib.load("app/data_ml/scam_threshold.pkl")
        threshold_point = threshold["threshold"]

        pattern_type0, pattern_type1, pattern_type2 = load_linking_patterns()

        text = "\n".join(desc.decryption for desc in job_desc if desc.decryption)

        sentences = re.split(r'(?<=[.!?;])\s+(?=[A-ZÀ-Ỹ\-\(])|\n+', text)

        processed_sentences = []
        for s in sentences:
            s_clean = clean_text(s.strip())
            s_linked = advanced_phrase_linking(s_clean, pattern_type0, pattern_type1, pattern_type2)
            if s_linked:
                processed_sentences.append(s_linked)

        if not processed_sentences:
            return Response({"status": "Success", "score": 100})

        X = vectorizer.transform(processed_sentences)
        predictions = model.predict(X)

        embeddings = st_model.encode(processed_sentences, convert_to_tensor=True)
        score = 0

        for i, label in enumerate(predictions):
            if label == 1:
                sims = util.cos_sim(embeddings[i], scam_embeddings)[0]
                max_sim = float(torch.max(sims))
                if max_sim >= threshold_point:
                    score += 1

        trust_score = (1 - (score / len(processed_sentences))) * 100
        return Response({"status": "Success", "score": trust_score})

    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_require_job(request):
    try:
        job_id = request.GET.get("jobId")
        if job_id:
            session = SessionLocal()
            job_require = session.query(JobRequire).filter(JobRequire.jobId == job_id).first()
            if job_require:
                job_data = {
                    "jobId": job_require.jobId,
                    "level": job_require.level,
                    "education": job_require.education,
                    "quantity": job_require.quantity,
                    "formOfWork": job_require.formOfWork,
                    "gender": job_require.gender
                }
                session.close()
                return Response({"status": "Success", "jobRequire": job_data})
            else:
                session.close()
                return Response({"status": "Success", "jobRequire": {}})
        else:
            return Response({"status": "Success", "jobRequire": {}})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


def handle_address_string(series_df):
    list_catalysis = []
    if series_df is not None:
        for value in series_df:
            words = value.strip().split()
            capitalized = " ".join([word.capitalize() for word in words])
            list_catalysis.append(capitalized)
    return list_catalysis


def handle_field_string(series_df):
    list_catalysis = []
    if series_df is not None:
        for value in series_df:
            if value:  # kiểm tra nếu value không phải None hoặc rỗng
                words = value.strip().split(",")
                for word in words:
                    word = word.strip()
                    if word:
                        list_catalysis.append(word)
    return list_catalysis


@api_view(["GET"])
def get_catalysis(request):
    try:
        session = SessionLocal()
        all_job = session.query(Jobs).all()
        if all_job:
            catalysis_address_list = [job.address for job in all_job]
            catalysis_field_list = [job.field for job in all_job]
            catalysis_salary_list = [job.salary for job in all_job]
            df = pd.DataFrame({
                "address": catalysis_address_list,
                "field": catalysis_field_list,
                "salary": catalysis_salary_list
            })
            address_series = df["address"].str.lower().str.split("&").str[0].str.strip().unique()
            field_series = df["field"].unique()
            salary_series = df["salary"].unique()
            result_address = list(set(handle_address_string(address_series)))
            result_field = list(set(handle_field_string(field_series)))
            result_salary = sorted(salary_series.tolist())
            result_address.sort()
            result_field.sort()
            result_salary.sort()
            session.close()
            return Response(
                {"status": "Success", "address": result_address, "field": result_field, "salary": result_salary})
        else:
            session.close()
            return Response(
                {"status": "Success", "address": [], "field": [], "salary": []})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


def parse_salary(salary_str):
    if "thỏa thuận" in salary_str.lower():
        return 0
    digits = ''.join([c for c in salary_str if c.isdigit()])
    return int(digits) if digits else 0


@api_view(["GET"])
def search_job(request):
    try:
        # --- Lấy thông tin lọc từ query parameters ---
        job_name = request.GET.get("job", "")
        address_name = request.GET.get("address", "")
        field_name = request.GET.get("field", "")
        salary_name = request.GET.get("salary", "")
        page = int(request.GET.get("page", 1))
        page_size = 10
        offset = (page - 1) * page_size

        # --- Ngày hiện tại (giới hạn công việc còn hạn nộp) ---
        vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
        today = datetime.now(vn_tz).date()

        session = SessionLocal()
        query = session.query(Jobs).filter(Jobs.dateLimit >= today)  # 👈 Giới hạn theo ngày

        # --- Lọc thêm theo job, address, field, salary ---
        filters = []
        if job_name:
            filters.append(func.lower(Jobs.name).like(f"%{job_name.lower()}%"))
        if address_name:
            filters.append(func.lower(Jobs.address).like(f"%{address_name.lower()}%"))
        if field_name:
            filters.append(func.lower(Jobs.field).like(f"%{field_name.lower()}%"))
        if salary_name != "":
            salary_value = parse_salary(salary_name)
            if salary_value == 0:
                filters.append(Jobs.salary == 0)
            else:
                filters.append(Jobs.salary >= salary_value)

        if filters:
            query = query.filter(and_(*filters))

        # --- Tổng số job và phân trang ---
        total_jobs = query.count()
        total_pages = math.ceil(total_jobs / page_size)

        jobs = query.order_by(Jobs.name).offset(offset).limit(page_size).all()

        # --- Xử lý dữ liệu ---
        list_job = []
        for i in jobs:
            job_data = {
                "id": i.id,
                "companyName": i.companyName,
                "name": i.name,
                "sourceName": i.sourceName,
                "dateCreate": i.dateCreate,
                "dateLimit": i.dateLimit,
                "sourceLink": i.sourceLink,
                "address": i.address,
                "salary": i.salary,
                "exp": i.exp,
                "field": i.field,
                "company": {
                    "name": i.company.name if i.company else None,
                    "link": i.company.link if i.company else None,
                    "address": i.company.address if i.company else None,
                    "image": i.company.image if i.company else None,
                }
            }
            list_job.append(job_data)

        session.close()

        return Response({
            "status": "Success",
            "page": page,
            "pageSize": page_size,
            "total": total_jobs,
            "totalPages": total_pages,
            "jobs": list_job
        })

    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


def join_chars_to_word(text):
    fix = text.replace('_', " ")
    parts = fix.split("   ")
    words = [''.join(p.split()) for p in parts]
    return ' '.join(words)


def clean_content(text):
    text_fix = text.replace(" .", ".")
    text_fix = text_fix.replace(" ,", ",")
    text_fix = text_fix.replace(" / ", "/")
    text_fix = text_fix.replace(" - ", "-")
    text_fix = text_fix.replace(". 0 ", ".0")
    text_fix = text_fix.replace(" :", ":")
    text_fix = text_fix.replace("!", "")
    return text_fix


def preprocess_vietnamese(text):
    # Tách từ tiếng Việt
    return " ".join(word_tokenize(text, format="text"))


@api_view(["POST"])
def save_job(request):
    try:
        email_value = request.data.get("email")
        job_value = request.data.get("jobId")
        save_job_id = request.data.get("saveJobId")
        if email_value and job_value:
            session = SessionLocal()
            if save_job_id:
                exists_save_job = session.query(SaveJob).filter(SaveJob.id == save_job_id).first()
                if exists_save_job:
                    session.delete(exists_save_job)
                    session.commit()
                    session.close()
                    return Response({"status": "Success", "saveJobId": ""})
                else:
                    session.close()
                    return Response({"status": "Not Found", "message": "Không tìm thấy tuyển dụng được lưu"})
            else:
                exists_acc = session.query(Account).filter(Account.email == email_value).first()
                exists_job = session.query(Jobs).filter(Jobs.id == job_value).first()
                if exists_acc and exists_job:
                    new_save_job = SaveJob(jobId=job_value, accountId=email_value)
                    session.add(new_save_job)
                    session.commit()
                    get_id = new_save_job.id
                    session.close()
                    return Response({"status": "Success", "saveJobId": get_id})
                else:
                    session.close()
                    return Response({"status": "Not Found", "message": "Không tìm thấy email hoặc mã tuyển dụng"})
        else:
            return Response({"status": "Invalid Value", "message": "Trường email hoặc mã tuyển dụng trống"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


@api_view(["GET"])
def check_save_job(request):
    try:
        email_value = request.GET.get("email")
        job_value = request.GET.get("jobId")
        if email_value and job_value:
            session = SessionLocal()
            exists_save_job = session.query(SaveJob).filter(
                (SaveJob.jobId == job_value) & (SaveJob.accountId == email_value)).first()
            if exists_save_job:
                session.close()
                return Response({"status": "Success", "saveJobId": exists_save_job.id})
            else:
                session.close()
                return Response({"status": "Success", "saveJobId": ""})
        else:
            return Response({"status": "Invalid Value", "message": "Trường email hoặc mã tuyển dụng trống"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


@api_view(["GET"])
def get_save_job(request):
    try:
        email_value = request.GET.get("email")
        if email_value:
            session = SessionLocal()
            all_save_job = session.query(SaveJob).join(Jobs).filter(SaveJob.accountId == email_value).all()
            if all_save_job:
                data = []
                for save_job_item in all_save_job:
                    job_item = save_job_item.job
                    data.append({
                        "id": job_item.id,
                        "saveJobId": save_job_item.id,
                        "companyName": job_item.companyName,
                        "name": job_item.name,
                        "sourceName": job_item.sourceName,
                        "dateCreate": job_item.dateCreate,
                        "dateLimit": job_item.dateLimit,
                        "sourceLink": job_item.sourceLink,
                        "address": job_item.address,
                        "salary": job_item.salary,
                        "exp": job_item.exp,
                        "field": job_item.field,
                        "company": {
                            "name": job_item.company.name if job_item.company else None,
                            "link": job_item.company.link if job_item.company else None,
                            "address": job_item.company.address if job_item.company else None,
                            "image": job_item.company.image if job_item.company else None,
                        }
                    })
                session.close()
                return Response({"status": "Success", "jobs": data})
            else:
                session.close()
                return Response({"status": "Success", "jobs": []})
        else:
            return Response({"status": "Invalid Value", "message": "Trường email trống"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
