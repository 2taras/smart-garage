from sqlalchemy import create_engine, Column, Integer, Boolean, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///garage.db"
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    is_auth = Column(Boolean, default=False)
    current_itern = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_owner = Column(Boolean, default=False)

class SystemConfig(Base):
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Log(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    user = Column(String)  # "web" or telegram user name
    action = Column(String)
    timestamp = Column(Integer)

# Initialize database
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()