from typing import Optional
from fastapi import FastAPI, Query, Response
import libs_zunoo as lb
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from models import Location
import random

app = FastAPI(title="Zunoo API", version="0.1")


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
def get_score(endereco: str):
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
                        ST_SetSRID(ST_Point(-43.6356, -22.9327), 4674)::geography
                    ) as distancia_metros
                FROM gold.score sr
                WHERE ST_DWithin(
                    sr.geom_segmento::geography, 
                    ST_SetSRID(ST_Point(-43.6356, -22.9327), 4674)::geography,
                    400 -- Limite de 400 metros
                )
                ORDER BY sr.geom_segmento <-> ST_SetSRID(ST_Point({longitude}, {latitude}), 4674)
                LIMIT 1
    """

    df = lb.get_postgres_data(sql_query)
    json_string = df.to_json(orient='records', indent=4)
    return Response(content=json_string, media_type="application/json")
    
