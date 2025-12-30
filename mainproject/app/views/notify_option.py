from rest_framework.response import Response
from rest_framework.decorators import api_view
from sqlalchemy import exists
from ..database import SessionLocal
from ..models import Account
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


@api_view(["GET"])
def check_notify(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = session.query(Account).filter(Account.email == decoded_token["email"]).first()
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        notify = (
            session.query(Notify)
            .filter(Notify.status == False, Notify.accountId == account.id)
            .count()
        )

        return Response({"status": "Success", "notifyAvailable": notify})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})


@api_view(["GET"])
def get_notify(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = (
            session.query(Account)
            .filter(Account.email == decoded_token["email"])
            .first()
        )
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        notify = (
            session.query(Notify)
            .filter(Notify.accountId == account.id)
            .order_by(Notify.dateCreate.desc())
            .all()
        )

        return Response({
            "status": "Success",
            "notify": model_to_list_json(notify)
        })

    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()


@api_view(["PATCH"])
def seen_notify(request):
    session = SessionLocal()
    try:
        decoded_token = request.decode_token
        account = (
            session.query(Account)
            .filter(Account.email == decoded_token["email"])
            .first()
        )
        if not account:
            return Response({"status": "Not Found", "message": "Không tìm thấy đối tượng!"})

        id_notify = request.data.get("id")
        if not id_notify:
            return Response({"status": "Empty Value", "message": "Thiếu dữ liệu!"})

        notify = session.query(Notify).filter(Notify.id == id_notify).first()
        if not notify:
            return Response({"status": "Not Found", "message": "Không tìm thấy thông báo!"})

        notify.status = True

        notify_available = (
            session.query(Notify)
            .filter(Notify.status == False, Notify.accountId == account.id)
            .count()
        )
        session.commit()
        return Response({"status": "Success", "notifyAvailable": notify_available})
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()