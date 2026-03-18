from fastapi import FastAPI

##### Implement Authentication Dependency

from fastapi import Request, Depends, HTTPException, status
# ... (import your actual auth logic)

def get_current_user_email(request: Request) -> str:
    # In a real application, this would validate a JWT token,
    # API key, or session cookie and return the user's email.
    # For this example, we'll assume the email is passed in a custom header for testing.
    # Replace this with your actual authentication logic.
    user_email = request.headers.get("x-user-email", "anonymous@example.com")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User email not found in headers"
        )
    return user_email

### Create the Logging Middleware

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from database import get_db
from models import RequestLog

app = FastAPI()

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    # This part gets executed on the way in
    user_email = request.headers.get("x-user-email", "anonymous@example.com") # Using the mock auth header

    # Proceed with the request
    response = await call_next(request)

    # This part gets executed on the way out, but we have access to the request data
    if user_email != "anonymous@example.com": # Only log authenticated users
        try:
            db = next(get_db())
            log_entry = RequestLog(
                user_email=user_email,
                method=request.method,
                url=str(request.url),
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
        except Exception as e:
            # Log the database error but don't stop the main request flow
            print(f"Database logging error: {e}")
        finally:
            # Ensure the session is closed
            db.close()

    return response

# Example endpoint that you can test with
@app.get("/items/")
def read_items(user_email: str = Depends(get_current_user_email)):
    return {"message": f"Hello {user_email}, items returned"}



### Run: 
### curl -X GET "http://127.0.0.1:8000/items/" -H "X-User-Email: testuser@example.com"
### Check your PostgreSQL database's request_logs table. A new entry associated with testuser@example.com should be present.

    