from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "hackgpt_chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String, unique=True, index=True)

Base.metadata.create_all(bind=engine)
