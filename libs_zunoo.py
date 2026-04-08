from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd


def get_connection():

    conn_str = f"postgresql://neondb_owner:npg_C7KATHVa1FIy@ep-spring-lake-acedndob-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    engine = create_engine(conn_str,
                           pool_size=10,          # Keep 10 connections
                           max_overflow=20,       # Allow 20 extra
                           pool_pre_ping=True,    # Verify connections
                           pool_recycle=3600      # Recycle after 1 hour
    )
    return engine

engine = get_connection()
SessionLocal = sessionmaker(bind=engine)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # Returns to pool, doesn't close!

def get_postgres_data(sqlstmt):
    # engine = get_connection()
	
    # Session = sessionmaker(bind=engine)

    session = SessionLocal()
    
    df = pd.DataFrame()
    try:
        df = pd.read_sql(sqlstmt, engine)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()    
    return df
