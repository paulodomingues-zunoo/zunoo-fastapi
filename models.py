from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base, engine
from pydantic import BaseModel
# Optional: Import Field for more control over validation and documentation
from pydantic import Field 

class RequestLog(Base):
    __tablename__ = "request_logs"
    __table_args__ = {"schema": "zunoo_prd"}  # Specify schema here
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True, nullable=False)
    method = Column(String, nullable=False)
    url = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    # Add other fields as needed (e.g., request body, response status)

# Create tables in the database
Base.metadata.create_all(bind=engine)


#### Models
class Location(BaseModel):
    latitude: float = Field(..., gt=-90, lt=90, example=12.91415)
    longitude: float = Field(..., gt=-180, lt=180, example=77.60028)