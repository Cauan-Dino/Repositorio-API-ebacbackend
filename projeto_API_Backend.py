from fastapi import FastAPI,HTTPException,Depends
from fastapi.security import HTTPBasicCredentials,HTTPBasic
from pydantic import BaseModel
from typing import Optional
import secrets


app = FastAPI(
    title= 'API De livros',
    description= 'API de catálogos de livros do curso da ebac Back-end',
    version='1.0.0',
    contact={
        'email':'cauanppenha@gmail.com',
        'name': 'cauan dino penha'
        }
)

meus_livros = {}

class Livro(BaseModel):
    nome_livro: str
    ano_lancamento: int 
    nome_autor: str

# Senha e Usuario para fazer login
MINHA_SENHA = 'admin'
MEU_USUARIO = 'admin'

# security eh um objeto da class HTTPBasic que permite com que o usuario consiga digitar sua senha e login no http basic
security = HTTPBasic()

# Funcao para permitir que o usuario consiga colocar a senha e o usuario
def autenticar_meu_usuario(crenditials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(crenditials.username,MEU_USUARIO)
    is_password_correct = secrets.compare_digest(crenditials.password,MINHA_SENHA)

    if not (is_password_correct and is_username_correct):
        raise HTTPException(
            status_code=401,
            detail='Usuario ou senha incorretos',
            headers={'WWW-Authenticate':'Basic'}
        )


# 1. Criar um get para ver os livros que estao cadastrados
@app.get('/livros')
def get_meus_livros(page: int = 1,limit: int = 10,credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400,detail='Page ou limit invalidos')
    
    if not meus_livros:
        return {'message':'Ainda nao ha nada castrado'}
    
    start = (page-1) * limit
    end = start + limit

    paginacao = [
        {'id':id_livro,'nome_autor':objeto.nome_autor,'nome_livro':objeto.nome_livro,'ano_lancamento':objeto.ano_lancamento}
        for id_livro, objeto in list(meus_livros.items())[start:end]
    ]

    return {
        'pagina': page,
        'limite': limit,
        'total': len(meus_livros),
        'livros': paginacao
            }

# 2. Criar um post para adicionar um livro
@app.post('/adicionar_livro')
def post_meus_livros(id_livro:int,livro: Livro,credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    if id_livro in meus_livros:
        raise HTTPException(status_code=400,detail='Esse livro ja esta cadastrado')
    else:
        meus_livros[id_livro] = livro
        return {'message':f'Livro {livro.nome_livro} cadastrado com sucesso'}


# 3. Criar um put para atualizar um livro ja existente
@app.put('/atualizar_livro/{id_livro}')
def put_meus_livros(id_livro:int,livro: Livro,credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404,detail='Esse livro nao existe')
    else:
        meus_livros[id_livro] = livro
        return {'message':f'Livro atualizado com sucesso'}


# 4. Criar um delete
@app.delete('/deletar_livro/{id_livro}')
def delete_meus_livros(id_livro:int):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404,detail='Nao foi possivel encontrar esse livro')
    else:
        del(meus_livros[id_livro])
        return{'message':'Livro deletado com sucesso'}

