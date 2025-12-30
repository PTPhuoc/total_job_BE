from sqlalchemy import Column, String, Date, ForeignKey, UnicodeText
from sqlalchemy.orm import relationship
from app.database import Base


class Applied(Base):
    __tablename__ = "Applied"

    id = Column(String(255), primary_key=True, index=True)
    dateCreate = Column(Date, index=True)
    status = Column(String(255), index=True)
    decryption = Column(UnicodeText, index=False)
    profile = Column(UnicodeText, index=False)
    jobId = Column(String(255), ForeignKey("Jobs.id"), index=True)
    accountId = Column(String(255), ForeignKey("Account.id"), index=True)

    job = relationship("Jobs", back_populates="applied")
    account = relationship("Account", back_populates="applied")
