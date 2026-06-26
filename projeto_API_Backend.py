from dotenv import load_dotenv
load_dotenv(dotenv_path="variaveis_ambientes.env")
from fastapi import FastAPI,HTTPException,Depends,BackgroundTasks
from tasks import fatorial,somar
from celery_app import celery_app
from celery.result import AsyncResult
from fastapi.security import HTTPBasicCredentials,HTTPBasic
from pydantic import BaseModel
from typing import Optional
import secrets
import os
from sqlalchemy import create_engine,Column ,Integer,String
from sqlalchemy.orm import Session,sessionmaker,declarative_base
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import redis
import json
from kafka_producer import enviar_evento

# 1. Criacao de objetos/ Variaveis

# 1.1 Criacao do objeto da classe FastAPI que permite a gente a conseguir utilizar os endpoints
# app = FastAPI(
#     title= 'API De livros',
#     description= 'API de catálogos de livros do curso da ebac Back-end',
#     version='1.0.0',
#     contact={
#         'email':'cauanppenha@gmail.com',
#         'name': 'cauan dino penha'
#         }
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # deixa qualquer front acessar
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1.2 Criacao do objeto da classe HTTPBasic que nos permite colocar senhas e usuarios e utilizar a autenticacao do  HTTP Basic
security = HTTPBasic()

# 1.3 Criacao da variavel para criar um banco de dados

# DATABASE_URL = os.getenv("DATABASE_URL")


# REDIS_HOST = os.getenv("REDIS_HOST","locahost")
# REDIS_PORT = os.getenv("REDIS_PORT","6379")

engine = create_engine(DATABASE_URL,connect_args={'check_same_thread': False})
Sessionlocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()
redis_client = redis.Redis(host=REDIS_HOST,port=REDIS_PORT,db=0,decode_responses=True)
# 2. Criacao de body model e das colunas do banco de dados

class LivroDB(Base):
    __tablename__ = 'Livros'
    id = Column(Integer,primary_key=True,index=True)
    nome_livro = Column(String,index=True)
    nome_autor = Column(String,index=True)
    ano_lancamento = Column(Integer)

class Livro(BaseModel):
    nome_livro: str
    nome_autor: str
    ano_lancamento: int
    
def sessao_db():
    db = Sessionlocal() 
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)

# 3. Funcoes


# 3.1 Funcao para permitir que o usuario consiga colocar a senha e o usuario
def autenticar_meu_usuario(crenditials: HTTPBasicCredentials = Depends(security)):
    MEU_USUARIO = os.getenv("MEU_USUARIO")
    MINHA_SENHA = os.getenv("MINHA_SENHA")
    
    is_username_correct = secrets.compare_digest(crenditials.username,MEU_USUARIO)
    is_password_correct = secrets.compare_digest(crenditials.password,MINHA_SENHA)

    if not (is_password_correct and is_username_correct):
        raise HTTPException(
            status_code=401,
            detail='Usuario ou senha incorretos',
            headers={'WWW-Authenticate':'Basic'}
        )

def salvar_livro_redis(livro_id: int, body: Livro):
    redis_client.set(f'livro:{livro_id}',json.dumps(body.model_dump()))

def delatar_livro_redis(livro_id: int):
    redis_client.delete(f'livro:{livro_id}')


# Criacao dos endpoints

# 4. Metodo GET

@app.get('/debug/redis')
async def ver_livros_redis():
    chaves = redis_client.keys('livros:*')
    livros = []

    for chave in chaves:
        valor = redis_client.get(chave)
        ttl = redis_client.ttl(chave)

        livros.append({'chave':chave,'valor':json.loads(valor),'ttl': ttl})

    return livros

# 4.1 Criar um get para ver os livros que estao cadastrados
@app.get('/livros')
async def get_livros(db: Session = Depends(sessao_db),page: int = 1,limit: int =10,_: None = Depends(autenticar_meu_usuario)):
    if page < 1 or limit < 1:
        raise HTTPException(
            status_code=400,
            detail='Page ou limit estao com valores invalidos'
        )
    
    cache_key = f'livros:page={page}&limit={limit}'
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    livros = db.query(LivroDB).offset((page-1)*limit).limit(limit).all()

    if not livros:
        raise HTTPException(
            status_code=400,
            detail='Nao existe nenhum livro'
        )
    
    total_livros = db.query(LivroDB).count()

    resposta = {
        'page': page,
        'limit': limit,
        'quantidade': total_livros,
        'livros': [{
            'livro_id': valor.id,
            'nome_livro': valor.nome_livro,
            'nome_autor': valor.nome_autor,
            'ano_lancamento': valor.ano_lancamento
        }
        for valor in livros
        ]
    }

    redis_client.setex(cache_key,30,json.dumps(resposta))

    return resposta



@app.get('/tarefas/recentes')
def listar_tarefas_recentes():
    ids = redis_client.lrange('tarefas_ids',0,-1)
    tarefas = []

    for task_id in ids:
        resultado = AsyncResult(task_id,app=celery_app)
        tarefas.append({
            'task_id': task_id,
            'status': resultado.status,
            'resultado': resultado.result if resultado.successful() else None
        })

    return {
        'tarefas': tarefas
    }

@app.get('/')
def hello_world(_:None = Depends(autenticar_meu_usuario)):
    return {'hello':'world'}

async def resultado_1():
    await asyncio.sleep(2)
    return 'Resultado 1 foi executado'

async def resultado_2():
    await asyncio.sleep(2)
    return 'Resultado 2 foi executado'

async def resultado_3():
    await asyncio.sleep(2)
    return 'Resultado 3 foi executado'

@app.get('/mostra-resultados')
async def mostrar_resultados():
    resultado1 = asyncio.create_task(resultado_1())
    resultado2 = asyncio.create_task(resultado_2())
    resultado3 = asyncio.create_task(resultado_3())

    r1 = await resultado1
    r2 = await resultado2
    r3 = await resultado3

    return [r1,r2,r3]

# 5. Metodo POST

# 5.1 Criar um post para adicionar um livro
@app.post('/livros')
async def post_livros(
    livro: Livro,
    db: Session = Depends(sessao_db),
    _: None = Depends(autenticar_meu_usuario)
    ):
    db_livro = db.query(LivroDB).filter(
        LivroDB.nome_livro == livro.nome_livro,
        LivroDB.nome_autor == livro.nome_autor
    ).first()

    if db_livro:
        raise HTTPException(
            status_code=400,
            detail='Esse livro ja existe'
        )

    novo_livro = LivroDB(
        nome_livro=livro.nome_livro,
        nome_autor=livro.nome_autor,
        ano_lancamento=livro.ano_lancamento
    )

    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)

    salvar_livro_redis(novo_livro.id, livro)

    enviar_evento(
        'livros_evento',
        {
            'acao': 'criar',
            'livro': livro.model_dump()
        }
    )

    return {'message':'O livro foi adicionado com sucesso'}

@app.post('/calcular/soma')
def calcular_soma(a: int, b: int):
    tarefa = somar.delay(a, b)
    redis_client.lpush("tarefas_ids",tarefa.id)
    redis_client.ltrim("tarefas_ids",0,49)
    return {
        'task_id': tarefa.id,
        'message': 'tarefa de soma enviada para execucao'
    }

@app.post('/calcular/fatorial')
def calcular_fatorial(n: int):
    tarefa = fatorial.delay(n)
    redis_client.lpush("tarefas_ids",tarefa.id)
    redis_client.ltrim("tarefas_ids",0,49)
    return {
        'task_id': tarefa.id,
        'message': 'tarefa de fatorial enviada para execucao'
    }

# 6. Metodo PUT

# 6.1 Criar um put para atualizar um livro ja existente
@app.put('/livros/{id_livro}')
async def put_livros(id_livro:int,livro: Livro,db: Session = Depends(sessao_db),_: None = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(
            status_code=404,
            detail='Esse livro nao existe'
        )

    db_livro.nome_livro = livro.nome_livro
    db_livro.ano_lancamento = livro.ano_lancamento
    db_livro.nome_autor = livro.nome_autor

    # Deleta a informacao no cache
    delatar_livro_redis(id_livro)
    # Muda as informacoes existentes do livro
    salvar_livro_redis(id_livro,livro)

    db.commit()
    db.refresh(db_livro)

    return {'message':'Seu livro foi atualizado com sucesso'}

# 7. Metodo DELETE

# 7.1 Criar um delete
@app.delete('/livros/{id_livro}')
async def delete_livros(id_livro:int, _: None = Depends(autenticar_meu_usuario),db: Session = Depends(sessao_db)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()

    if not db_livro:
        raise HTTPException(
            status_code=404,
            detail='Esse livro nao existe'
    
        )
    db.delete(db_livro)
    db.commit()

    return {'message':'Seu livro foi deletado com sucesso'}

@app.delete('/deletar/cache')
async def limpar_cache_lista():
    chaves = redis_client.keys('livros:*')
    for chave in chaves:
        redis_client.delete(chave)
