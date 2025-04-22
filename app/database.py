from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from fastapi import Depends

engine = create_engine('sqlite:///./transcription.db') #local db

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()