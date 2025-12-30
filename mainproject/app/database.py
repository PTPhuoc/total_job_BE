from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from django.conf import settings

DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

from .models import (Jobs, JobDecryption, JobRequire, Company, Account, SaveJob, SaveCompany, Catalog, Subcatalog,
                     CandidateProfile, EmployerProfile, Applied, EducationCandidate, ExperienceCandidate,
                     ProjectCandidate, Notify)

Base.metadata.create_all(bind=engine)
