from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from typing import Optional


app = FastAPI()

meus_livros = {}

class Livro(BaseModel):
    nome_livro: str
    ano_lancamento: int
    nome_autor: str

# 1. Criar um get para ver os livros que estao cadastrados
@app.get('/livros')
def get_meus_livros():
    if not meus_livros:
        return {'message':'Ainda nao ha nada cadastrado'}
    else:
        return {'livros':meus_livros}

# 2. Criar um post para adicionar um livro
@app.post('/adicionar_livro')
def post_meus_livros(id_livro:int,livro: Livro):
    if id_livro in meus_livros:
        raise HTTPException(status_code=400,detail='Esse livro ja esta cadastrado')
    else:
        meus_livros[id_livro] = livro.model_dump()
        return {'message':f'Livro {livro.nome_livro} cadastrado com sucesso'}

# 3. Criar um put para atualizar um livro ja existente
@app.put('/atualizar_livro/{id_livro}')
def put_meus_livros(id_livro:int,livro: Livro):
    meu_livro = meus_livros.get(id_livro)
    if id_livro not in meus_livros or not meus_livros:
        raise HTTPException(status_code=404,detail='Esse livro nao existe')
    else:
        meu_livro[id_livro] = livro.model_dump()
        return {'message':f'Livro atualizado com sucesso'}

# 4. Criar um delete
@app.delete('/deletar_livro/{id_livro}')
def delete_meus_livros(id_livro:int):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404,detail='Nao foi possivel encontrar esse livro')
    else:
        del(meus_livros[id_livro])
        return{'message':'Livro deletado com sucesso'}

