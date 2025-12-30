from sqlalchemy import Column, Boolean, String, Date, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship


class SaveJob(Base):
    __tablename__ = "SaveJob"

    id = Column(String(255), primary_key=True, index=True)
    jobId = Column(String(255), ForeignKey("Jobs.id"), index=True)
    accountId = Column(String(255), ForeignKey("Account.id"), index=True)
    dateCreate = Column(Date, index=True)
    isFavorite = Column(Boolean, index=True)

    job = relationship("Jobs", back_populates="save_job")
    account = relationship("Account", back_populates="save_job")
