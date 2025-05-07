from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from datetime import datetime
from app.database import Base,relationship

class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String,unique=True,nullable=False)
    password = Column(String,nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String,unique=True,nullable=False)
    password = Column(String,nullable=False)

class IWord(Base):
    __tablename__ = 'iwords'
    id = Column(Integer,primary_key=True,index=True)
    word = Column(String,unique=True,nullable=False)
    count = Column(Integer, default=0)
    lastDetectedAt = Column(DateTime,default=datetime.now)
    lastDetectedBy = Column(Integer,ForeignKey("users.username"),default=0)
    transcriptionType = Column(String,default="upload")

    user = relationship("User", backref="last_detection")

class WordDetectionLog(Base):
    __tablename__ = "word_detection_log"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String,ForeignKey("iwords.word"))
    detectedAt = Column(DateTime, default=datetime.now)
    detectedBy = Column(String,ForeignKey("users.username"))
    transcriptionType = Column(String,default="upload")

    wordD = relationship("IWord", backref="word_detections")
    user = relationship("User", backref="user_detections")
