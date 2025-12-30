from sqlalchemy import Column, String, Unicode, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship


class JobRequire(Base):
    __tablename__ = "JobRequires"

    id = Column(String(255), primary_key=True, unique=True, index=True)
    jobId = Column(String(255), ForeignKey("Jobs.id"), index=True)
    title = Column(Unicode(255), index=True)
    requestText = Column(Unicode(255), index=True)

    job = relationship("Jobs", back_populates="requires")
