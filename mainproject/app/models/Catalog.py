from sqlalchemy import Column, String, Unicode, Date, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship


class Catalogs(Base):
    __tablename__ = "Catalogs"

    id = Column(String(255), primary_key=True, unique=True, index=True)
    name = Column(Unicode(255), index=True)
    type = Column(Unicode(255), index=True)

    subcatalogs = relationship("Subcatalogs", back_populates="catalogs", cascade="all, delete")
