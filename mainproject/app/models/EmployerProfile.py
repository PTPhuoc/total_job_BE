from sqlalchemy import Column, Unicode, String, UnicodeText, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class EmployerProfile(Base):
    __tablename__ = "EmployerProfile"

    id = Column(String(255), primary_key=True, index=True)
    accountId = Column(String(255), ForeignKey("Account.id"), index=True, unique=True)
    companyId = Column(String(255), ForeignKey("Company.id"), index=True, unique=True, nullable=True)
    name = Column(Unicode(255), index=True)
    decryption = Column(UnicodeText, index=False)
    image = Column(UnicodeText, index=False)

    account = relationship("Account", back_populates="employer")
    job = relationship("Jobs", back_populates="employer", cascade="all, delete-orphan")
    company = relationship("Company", back_populates="employer", cascade="all, delete", uselist=False)