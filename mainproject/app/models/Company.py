from sqlalchemy import Column, Unicode, UnicodeText, String, Boolean, Date
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    __tablename__ = "Company"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(Unicode(255), index=True, unique=True)
    link = Column(Unicode(255), index=True)
    address = Column(Unicode(255), index=True)
    image = Column(UnicodeText, index=False)
    scale = Column(Unicode(255), index=True)
    field = Column(Unicode(255), index=True)
    decryption = Column(UnicodeText, index=False)
    isCrawl = Column(Boolean, index=True)
    dateCreate = Column(Date, index=True)

    job = relationship("Jobs", back_populates="company", cascade="all, delete-orphan")
    save_company = relationship("SaveCompany", back_populates="company", cascade="all, delete-orphan")
    employer = relationship("EmployerProfile", back_populates="company")

