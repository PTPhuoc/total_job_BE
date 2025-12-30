import json
import math
from datetime import datetime
import pytz
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..database import SessionLocal
from sqlalchemy import and_
from ..models.SaveCompany import SaveCompany
from ..models.Company import Company


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
def get_company(request):
    session = SessionLocal()
    try:
        search_value = request.GET.get("searchValue")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 10))
        skip = (page - 1) * limit

        query = session.query(Company)
        if search_value:
            if isinstance(search_value, str):
                search_value = json.loads(search_value)
            filters = []
            if search_value.get("name"):
                filters.append(Company.name.ilike(f"%{search_value['name']}%"))

            if search_value.get("field"):
                filters.append(Company.field.ilike(f"%{search_value['field']}%"))

            if search_value.get("scale"):
                filters.append(Company.scale.ilike(f"%{search_value['scale']}%"))

            if filters:
                query = query.filter(and_(*filters))
        query = query.distinct()
        total = query.count()
        company = query.order_by(Company.dateCreate.desc()).offset(skip).limit(limit).all()

        list_job = model_to_list_json(company)
        return Response({
            "status": "Success",
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": math.ceil(total / limit),
            "listCompany": list_job
        })
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


@api_view(["GET"])
def get_one_company(request):
    session = SessionLocal()
    try:
        company_id = request.GET.get("id")
        if not company_id:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        exists_company = session.query(Company).filter(Company.id == company_id).first()
        if exists_company:
            company_infor = model_to_json(exists_company)
            return Response({"status": "Success", "company": company_infor})
        else:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()




