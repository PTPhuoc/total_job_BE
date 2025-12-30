from sqlalchemy import Column, Unicode, String, UnicodeText, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.database import Base


class ExperienceCandidate(Base):
    __tablename__ = "ExperienceCandidate"

    id = Column(String(255), primary_key=True, index=True)
    accountId = Column(String(255), ForeignKey("Account.id"), index=True)
    field = Column(Unicode(255), index=True)
    formOfWork = Column(Unicode(255), index=True)
    company = Column(Unicode(255), index=True)
    executionTime = Column(String(255), index=True)
    address = Column(Unicode(255), index=True)
    decryption = Column(UnicodeText, index=False)

    account = relationship("Account", back_populates="exp")
