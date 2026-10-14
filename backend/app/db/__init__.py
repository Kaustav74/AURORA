from app.db.session import Base, SessionLocal, engine, get_db
from app.db import models

def init_db():
    Base.metadata.create_all(bind=engine)
