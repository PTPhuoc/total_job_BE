from sqlalchemy import Column, Unicode, String, Date
from sqlalchemy.orm import relationship
from app.database import Base


class Account(Base):
    __tablename__ = "Account"

    id = Column(String(255), primary_key=True, index=True)
    email = Column(String(255), index=True)
    phoneNumber = Column(String(10), index=True)
    password = Column(Unicode(255), index=True)
    role = Column(String(255), index=True)
    dateCreate = Column(Date, index=True)

    save_job = relationship("SaveJob", back_populates="account", cascade="all, delete")
    save_company = relationship("SaveCompany", back_populates="account", cascade="all, delete")
    candidate = relationship("CandidateProfile", back_populates="account", cascade="all, delete", uselist=False)
    employer = relationship("EmployerProfile", back_populates="account", cascade="all, delete", uselist=False)
    applied = relationship("Applied", back_populates="account", cascade="all, delete-orphan")
    education = relationship("EducationCandidate", back_populates="account", cascade="all, delete-orphan")
    exp = relationship("ExperienceCandidate", back_populates="account", cascade="all, delete-orphan")
    project = relationship("ProjectCandidate", back_populates="account", cascade="all, delete-orphan")
    notify = relationship("Notify", back_populates="account", cascade="all, delete-orphan")

