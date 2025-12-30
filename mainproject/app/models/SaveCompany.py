from sqlalchemy import Column, Boolean, String, Unicode, Date, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship


class SaveCompany(Base):
    __tablename__ = "SaveCompany"

    id = Column(String(255), primary_key=True, index=True)
    companyId = Column(String(255), ForeignKey("Company.id"), index=True)
    accountId = Column(String(255), ForeignKey("Account.id"), index=True)
    dateCreate = Column(Date, index=True)
    isFavorite = Column(Boolean, index=True)

    company = relationship("Company", back_populates="save_company")
    account = relationship("Account", back_populates="save_company")
