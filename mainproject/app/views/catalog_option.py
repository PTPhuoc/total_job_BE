from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings
from ..database import SessionLocal
from ..models.Catalog import Catalogs
from ..models.Subcatalog import Subcatalogs
import ulid


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
def get_catalogs(request):
    session = SessionLocal()
    try:
        catalogs = session.query(Catalogs).all()
        if catalogs:
            list_catalog = model_to_list_json(catalogs, True, ["subcatalogs"])
            return Response({"status": "Success", "catalogs": list_catalog})
        else:
            return Response({"status": "Success", "catalogs": []})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["GET"])
def get_one_catalog(request):
    session = SessionLocal()
    try:
        type_catalog = request.GET.get("type")
        if not type_catalog:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        catalogs = session.query(Catalogs).filter(Catalogs.type == type_catalog).all()
        list_catalog = model_to_list_json(catalogs, True, ["subcatalogs"])
        return Response({"status": "Success", "catalogs": list_catalog})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
def add_catalog(request):
    name_catalog = request.data.get("name", "").strip()
    type_catalog = request.data.get("type", "").strip()
    if not name_catalog or not type_catalog:
        return Response({"status": "Empty Value", "message": "Thông tin trống!"})

    session = SessionLocal()
    try:
        exists = session.query(Catalogs).filter(
            (Catalogs.name == name_catalog) & (Catalogs.type == type_catalog)
        ).first()
        if exists:
            return Response({"status": "Exists Value", "message": "Tên này đã tồn tại!"})
        else:
            new_id = str(ulid.new())
            new_catalog = Catalogs(id=new_id, name=name_catalog, type=type_catalog)
            session.add(new_catalog)
            session.commit()
            return Response({"status": "Success", "newCatalog": {
                "id": new_catalog.id,
                "name": new_catalog.name,
                "type": new_catalog.type
            }})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
def change_catalog(request):
    id_catalog = request.data.get("id")
    name_catalog = request.data.get("name", "").strip()
    type_catalog = request.data.get("type", "").strip()
    if not name_catalog or not type_catalog or not id_catalog:
        return Response({"status": "Empty Value", "message": "Thông tin trống!"})

    session = SessionLocal()
    try:
        exists_catalog = session.query(Catalogs).filter(Catalogs.id == id_catalog).first()
        if exists_catalog:
            same_catalog = session.query(Catalogs).filter(
                (Catalogs.name == name_catalog) & (Catalogs.type == type_catalog), Catalogs.id != id_catalog).first()
            if same_catalog:
                return Response({"status": "Exists Value", "message": "Tên này đã tồn tại!"})
            else:
                exists_catalog.name = name_catalog
                exists_catalog.type = type_catalog
                session.commit()
                return Response({"status": "Success", "newCatalog": {
                    "id": exists_catalog.id,
                    "name": exists_catalog.name,
                    "type": exists_catalog.type
                }})
        else:
            return Response({"status": "Empty Value", "message": "Không tìm thấy đối tượng cần chỉnh sửa!"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_catalog(request):
    id_catalog = request.GET.get("id")

    if not id_catalog:
        return Response({"status": "Empty Value", "message": "Thiếu id!"})

    session = SessionLocal()
    try:
        catalog = session.query(Catalogs).filter(Catalogs.id == id_catalog).first()
        if not catalog:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        session.delete(catalog)
        session.commit()
        return Response({"status": "Success", "deletedId": id_catalog})

    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["POST"])
def add_subcatalog(request):
    session = SessionLocal()
    try:
        catalog_id = request.data.get("id")
        name = request.data.get("subName")
        if name and catalog_id:
            id = str(ulid.new())
            new_subcatalog = Subcatalogs(id=id, catalogId=catalog_id, name=name)
            session.add(new_subcatalog)
            session.commit()
            return Response({"status": "Success",
                             "newSubcatalog": {
                                 "id": new_subcatalog.id,
                                 "catalogId": new_subcatalog.catalogId,
                                 "name": new_subcatalog.name}
                             })
        else:
            return Response({"status": "Empty Value", "message": "Trường dữ liệu trống!"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PATCH"])
def change_subcatalog(request):
    session = SessionLocal()
    try:
        id = request.data.get("subId")
        name = request.data.get("subName")
        if id and name:
            exists_subcatalog = session.query(Subcatalogs).filter(Subcatalogs.id == id).first()
            if exists_subcatalog:
                same_subcatalog = session.query(Subcatalogs).filter(Subcatalogs.name == name,
                                                                    Subcatalogs.id != id).first()
                if same_subcatalog:
                    return Response({"status": "Exists Value", "message": "Đối tượng này đã tồn tại!"})

                exists_subcatalog.name = name
                session.commit()
                return Response({"status": "Success",
                                 "subcatalog": {
                                     "id": exists_subcatalog.id,
                                     "catalogId": exists_subcatalog.catalogId,
                                     "name": exists_subcatalog.name}
                                 })
            else:
                return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["DELETE"])
def delete_subcatalog(request):
    session = SessionLocal()
    try:
        id = request.GET.get("subId")
        exists_subcatalog = session.query(Subcatalogs).filter(Subcatalogs.id == id).first()
        if exists_subcatalog:
            session.delete(exists_subcatalog)
            session.commit()
            return Response({"status": "Success", "message": "Xóa thành công"})
        else:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()
