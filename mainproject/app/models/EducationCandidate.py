from sqlalchemy import Column, Unicode, String, UnicodeText, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class EducationCandidate(Base):
    __tablename__ = "EducationCandidate"

    id = Column(String(255), primary_key=True, index=True)
    accountId = Column(String(255), ForeignKey("Account.id"), index=True)
    name = Column(Unicode(255), index=True)
    degree = Column(Unicode(255), index=True)
    industry = Column(Unicode(255), index=True)
    course = Column(String(255), index=True)
    decryption = Column(UnicodeText, index=False)

    account = relationship("Account", back_populates="education")