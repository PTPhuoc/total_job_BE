from rest_framework.response import Response
from rest_framework.decorators import api_view
from ..database import SessionLocal
from ..models import Jobs
from ..models import JobRequire
from datetime import datetime
from ..models import Catalogs
from sqlalchemy import func
from calendar import monthrange
from collections import defaultdict


@api_view(["GET"])
def get_catalyst_chart(request):
    session = SessionLocal()
    try:
        job_available = session.query(Jobs).filter(Jobs.dateLimit >= datetime.now()).count()
        stats = (
            session.query(
                JobRequire.requestText.label("requestText"),
                func.count(Jobs.id).label("jobCount")
            )
            .join(Jobs, Jobs.id == JobRequire.jobId)
            .filter(
                JobRequire.title == "Nghề",
                Jobs.dateLimit >= datetime.now()
            )
            .group_by(JobRequire.requestText)
            .all()
        )
        result = [
            {
                "title": row.requestText,
                "jobCount": row.jobCount
            }
            for row in stats
        ]

        return Response({
            "status": "Success",
            "result": result,
            "jobAvailable": job_available
        })
    except Exception as ex:
        return Response({"status": "Server Error", "error": str(ex)})
    finally:
        session.close()

