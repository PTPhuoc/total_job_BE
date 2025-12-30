from sqlalchemy import Column, Unicode, String, UnicodeText, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from app.database import Base


class CandidateProfile(Base):
    __tablename__ = "CandidateProfile"

    id = Column(String(255), primary_key=True, index=True)
    accountId = Column(String(255), ForeignKey("Account.id"), unique=True, primary_key=True, index=True)
    name = Column(Unicode(255), index=True)
    birthday = Column(Date, index=True)
    decryption = Column(UnicodeText, index=False)
    address = Column(Unicode(255), index=True)
    skills = Column(Unicode(255), index=True)
    image = Column(UnicodeText, index=False)

    account = relationship("Account", back_populates="candidate")
