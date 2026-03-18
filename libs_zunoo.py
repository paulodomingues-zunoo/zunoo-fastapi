from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd


def get_connection():

    conn_str = f"postgresql://neondb_owner:npg_C7KATHVa1FIy@ep-spring-lake-acedndob-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    engine = create_engine(conn_str)
    return engine

def get_postgres_data(sqlstmt):
    engine = get_connection()
	
    Session = sessionmaker(bind=engine)

    session = Session()
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