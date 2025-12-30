from sqlalchemy import Column, String, Unicode, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship


class Subcatalogs(Base):
    __tablename__ = "Subcatalogs"

    id = Column(String(255), primary_key=True, unique=True, index=True)
    catalogId = Column(String(255), ForeignKey("Catalogs.id"), index=True)
    name = Column(Unicode(255), index=True)

    catalogs = relationship("Catalogs", back_populates="subcatalogs")