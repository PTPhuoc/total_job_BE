from sqlalchemy import Column, Unicode, String, UnicodeText, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ProjectCandidate(Base):
    __tablename__ = "ProjectCandidate"

    id = Column(String(255), primary_key=True)
    accountId = Column(String(255), ForeignKey("Account.id"))
    name = Column(Unicode(255), index=True)
    executionTime = Column(String(255), index=True)
    field = Column(Unicode(255), index=True)
    link = Column(UnicodeText, index=False)
    image = Column(UnicodeText, index=False)
    decryption = Column(UnicodeText, index=False)

    account = relationship("Account", back_populates="project")