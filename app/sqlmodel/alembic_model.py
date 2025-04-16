from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    body = Column(String, nullable=False)
    published = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, onupdate=func.now())