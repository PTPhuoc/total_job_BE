from sqlalchemy import Column, UnicodeText, Unicode, Date, String, ForeignKey, Boolean
from app.database import Base
from sqlalchemy.orm import relationship


class Notify(Base):
    __tablename__ = "Notify"

    id = Column(String(255), primary_key=True)
    accountId = Column(String(255), ForeignKey("Account.id"), index=True)
    title = Column(Unicode(255), index=True)
    message = Column(UnicodeText, index=False)
    dateCreate = Column(Date, index=True)
    type = Column(String(255), index=True)
    status = Column(Boolean, index=True)
    value = Column(UnicodeText, index=False)

    account = relationship("Account", back_populates="notify")