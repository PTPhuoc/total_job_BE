from sqlalchemy import Column, String, Unicode, UnicodeText, ForeignKey, Integer
from app.database import Base
from sqlalchemy.orm import relationship


class JobDecryption(Base):
    __tablename__ = "JobDecryption"

    id = Column(String(255), primary_key=True, unique=True, index=True)
    jobId = Column(String(255), ForeignKey("Jobs.id"), index=True)
    title = Column(Unicode(255), index=True)
    decryption = Column(UnicodeText, index=False)
    order = Column(Integer, index=True)

    job = relationship("Jobs", back_populates="details")




