from sqlalchemy import Column, UnicodeText, Unicode, Date, ForeignKey, String, Boolean
from app.database import Base
from sqlalchemy.orm import relationship


class Jobs(Base):
    __tablename__ = "Jobs"

    id = Column(String(255), primary_key=True, unique=True, index=True)
    companyId = Column(String(255), ForeignKey("Company.id"), index=True)
    name = Column(Unicode(255), index=True)
    sourceName = Column(Unicode(255), index=True)
    dateCreate = Column(Date, index=True)
    dateLimit = Column(Date, index=True)
    sourceLink = Column(UnicodeText, index=False)
    address = Column(Unicode(255), index=True)
    isCrawl = Column(Boolean, index=True)
    employerId = Column(String(255), ForeignKey("EmployerProfile.id"), index=True, nullable=True)

    company = relationship("Company", back_populates="job")
    details = relationship("JobDecryption", back_populates="job", cascade="all, delete")
    requires = relationship("JobRequire", back_populates="job", cascade="all, delete")
    save_job = relationship("SaveJob", back_populates="job", cascade="all, delete-orphan")
    employer = relationship("EmployerProfile", back_populates="job")
    applied = relationship("Applied", back_populates="job", cascade="all, delete-orphan")



