import os
from dotenv import load_dotenv
from typing import Optional
from fastapi import FastAPI, Query, Response
import libs_zunoo as lb
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from models import Location
import random

## SECURITY
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel


# Carrega as variáveis do arquivo .env
load_dotenv()

# Substitua as constantes fixas por os.getenv
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

# Exemplo no Engine do SQLAlchemy
# engine = create_engine(DATABASE_URL)


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "02ae59db0070cae95c58ba60a941a57503609cb807c4f696a88ce413c51de985"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db = {
    "zunoo_auth": {
        "username": "zunoo_auth",
        "full_name": "Zunoo Inc.",
        "email": "zuno-infra@gmail.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("dummypassword")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

##
app = FastAPI(title="Zunoo API", version="0.1")
##
app = FastAPI(title="Zunoo API", version="0.1",
              docs_url="/docs" if os.getenv("ENV") == "development" else None,
              redoc_url="/redoc" if os.getenv("ENV") == "development" else None,
              openapi_url="/openapi.json" if os.getenv("ENV") == "development" else None
              )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desenvolvimento, permite qualquer origem. Para produção, coloque o domínio do seu frontend.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScoreResponse(BaseModel):
    endereco: str
    score: int
    insights: dict

#
def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        verify_password(password, DUMMY_HASH)
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/")
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]

#
@app.get("/score", response_model=ScoreResponse)
def calcular_score(endereco: str = Query(..., description="Endereço a ser avaliado")):
    # Aqui é só um MOCK. Depois você conecta em dados reais.
    score = random.randint(0, 100)
    insights = {
        "seguranca": f"{random.randint(0, 10)}/100",
        "comercio": f"{random.randint(0, 10)}/100",
        "educacao": f"{random.randint(0, 10)}/100"
    }
    return ScoreResponse(endereco=endereco, score=score, insights=insights)

@app.get("/get-score")
def get_score(endereco: str,  
              current_user: Annotated[User, Depends(get_current_active_user)],):
    sql_query = f"""
              select nome_completo as endereco, 
                     random(30,100) as score,
                     random(1,33)  as commercial,
                     random(1,33) education,
                     random(1,30) public_transport
              from (select distinct nome_completo 
                    from zunoo_prd.rj_logradouro_refined) as x
              where x.nome_completo = '{endereco}'
    """

    df = lb.get_postgres_data(sql_query)
    json_string = df.to_json(orient='records', indent=4)
    return Response(content=json_string, media_type="application/json")
    
    
@app.get("/get-score-location")
def get_score_location(latitude: float, longitude: float):
                       ### current_user: Annotated[User, Depends(get_current_active_user)],):
    sql_query = f"""
              SELECT 
                    sr.id,
                    sr.street_name,
                    sr.score_commerce,
                    sr.score_education,
                    sr.score_health,
                    sr.score_leisure,
                    sr.score_mobility,
                    sr.score_final,
                    sr.geom_segmento,
                    -- Opcional: retornar a distância real em metros para a API
                    ST_Distance(
                        sr.geom_segmento::geography, 
                        ST_SetSRID(ST_Point({longitude}, {latitude}), 4674)::geography
                    ) as distancia_metros
                FROM gold.score sr
                WHERE ST_DWithin(
                    sr.geom_segmento::geography, 
                    ST_SetSRID(ST_Point({longitude}, {latitude}), 4674)::geography,
                    400 -- Limite de 400 metros
                )
                ORDER BY sr.geom_segmento <-> ST_SetSRID(ST_Point({longitude}, {latitude}), 4674)
                LIMIT 1
    """

    df = lb.get_postgres_data(sql_query)
    json_string = df.to_json(orient='records', indent=4)
    return Response(content=json_string, media_type="application/json")



@app.get("/get-score-location_v1")
def get_score_location(latitude: float, longitude: float,
                        current_user: Annotated[User, Depends(get_current_active_user)],):
    sql_query = f"""
              SELECT 
                    sr.id,
                    sr.street_name,
                    sr.score_commerce,
                    sr.score_education,
                    sr.score_health,
                    sr.score_leisure,
                    sr.score_mobility,
                    sr.score_final,
                    sr.geom_segmento,
                    -- Opcional: retornar a distância real em metros para a API
                    ST_Distance(
                        sr.geom_segmento::geography, 
                        ST_SetSRID(ST_Point({longitude}, {latitude}), 4674)::geography
                    ) as distancia_metros
                FROM gold.score sr
                WHERE ST_DWithin(
                    sr.geom_segmento::geography, 
                    ST_SetSRID(ST_Point({longitude}, {latitude}), 4674)::geography,
                    400 -- Limite de 400 metros
                )
                ORDER BY sr.geom_segmento <-> ST_SetSRID(ST_Point({longitude}, {latitude}), 4674)
                LIMIT 1
    """

    df = lb.get_postgres_data(sql_query)
    json_string = df.to_json(orient='records', indent=4)
    return Response(content=json_string, media_type="application/json")
    

    
