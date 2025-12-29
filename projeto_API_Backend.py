from fastapi import FastAPI,HTTPException,Depends
from fastapi.security import HTTPBasicCredentials,HTTPBasic
from pydantic import BaseModel
from typing import Optional
import secrets

# 1. Criacao de objetos/ Variaveis

app = FastAPI(
    title= 'API De livros',
    description= 'API de catálogos de livros do curso da ebac Back-end',
    version='1.0.0',
    contact={
        'email':'cauanppenha@gmail.com',
        'name': 'cauan dino penha'
        }
)

security = HTTPBasic()

meus_livros = {}

# 2. Criacao de body model 

class Livro(BaseModel):
    nome_livro: str
    ano_lancamento: int 
    nome_autor: str

# 3. Classes

# 3.1 Classe para metodos HTTP e autenticacao
class MetodosHTTP_e_Autenticacao:
    # Funcao para permitir que o usuario consiga colocar a senha e o usuario
    def autenticar_meu_usuario(self,crenditials: HTTPBasicCredentials = Depends(security)):
        MINHA_SENHA = 'admin'
        MEU_USUARIO = 'admin'
        
        is_username_correct = secrets.compare_digest(crenditials.username,MEU_USUARIO)
        is_password_correct = secrets.compare_digest(crenditials.password,MINHA_SENHA)

        if not (is_password_correct and is_username_correct):
            raise HTTPException(
                status_code=401,
                detail='Usuario ou senha incorretos',
                headers={'WWW-Authenticate':'Basic'}
            )

# 3.2 Classe para metodos HTTP POST
class POST_metodohttp:
    # 3.2.1 Metodo POST para adicionar um livro
    def post_meus_livros(self,id_livro:int,livro: Livro):
        if id_livro in meus_livros:
            raise HTTPException(status_code=400,detail='Esse livro ja esta cadastrado')
        else:
            meus_livros[id_livro] = livro
            return {'message':f'Livro {livro.nome_livro} cadastrado com sucesso'}


# 3.3 Classe para metodos HTTP PUT
class PUT_metodohttp:
    # 3.3.1 Metodo PUT para atualizar um livro ja existente
    def put_meus_livros(self,id_livro:int,livro: Livro):
        if id_livro not in meus_livros:
            raise HTTPException(status_code=404,detail='Esse livro nao existe')
        else:
            meus_livros[id_livro] = livro
            return {'message':f'Livro atualizado com sucesso'}
 


# 3.4 Classe para metodos HTTP DELETE
class DEL_metodohttp:
    # 3.4.1 Metodo DELETE para excluir um livro
    def delete_meus_livros(self,id_livro:int):
        if id_livro not in meus_livros:
            raise HTTPException(status_code=404,detail='Nao foi possivel encontrar esse livro')
        else:
            del(meus_livros[id_livro])
            return{'message':'Livro deletado com sucesso'}


# 3.5 Classe para retornar livros cadastrados
class GET_metodohttp:
    # 3.5.1 Metodo GET para listar os livros cadastrados com paginação
    def get_meus_livros(self,page: int = 1,limit: int = 10):
        if page < 1 or limit < 1:
            raise HTTPException(status_code=400,detail='Page ou limit invalidos')
        
        if not meus_livros:
            return {'message':'Ainda nao ha nada castrado'}
        
        start = (page-1) * limit
        end = start + limit

        livros_ordenados = sorted(meus_livros.items(),key=lambda x: x[0])

        paginacao = [
            {'id':id_livro,'nome_autor':objeto.nome_autor,'nome_livro':objeto.nome_livro,'ano_lancamento':objeto.ano_lancamento}
            for id_livro, objeto in livros_ordenados[start:end]
        ]

        return {
            'pagina': page,
            'limite': limit,
            'total': len(meus_livros),
            'livros': paginacao
                }


# Declaracao dos objetos das classes
objeto_post_metodohttp = POST_metodohttp()
objeto_put_metodohttp = PUT_metodohttp()
objeto_del_metodohttp = DEL_metodohttp()
objeto_get_metodohttp = GET_metodohttp()
objeto_autorizacao = MetodosHTTP_e_Autenticacao()



# Criacao dos endpoints

# 4. Metodo GET

# 4.1 Criar um get para ver os livros que estao cadastrados
@app.get('/livros')
def get_livros(page: int = 1,limit: int =10,_: None = Depends(objeto_autorizacao.autenticar_meu_usuario)):
    return objeto_get_metodohttp.get_meus_livros(page,limit)


# 5. Metodo POST

# 5.1 Criar um post para adicionar um livro
@app.post('/livros/{id_livro}')
def post_livros(id_livro:int,livro: Livro,_: None = Depends(objeto_autorizacao.autenticar_meu_usuario)):
    return objeto_post_metodohttp.post_meus_livros(id_livro,livro)


# 6. Metodo PUT

# 6.1 Criar um put para atualizar um livro ja existente
@app.put('/livros/{id_livro}')
def put_livros(id_livro:int,livro: Livro,_: None = Depends(objeto_autorizacao.autenticar_meu_usuario)):
    return objeto_put_metodohttp.put_meus_livros(id_livro,livro)


# 7. Metodo DELETE

# 7.1 Criar um delete
@app.delete('/livros/{id_livro}')
def delete_livros(id_livro:int, _: None = Depends(objeto_autorizacao.autenticar_meu_usuario)):
    return objeto_del_metodohttp.delete_meus_livros(id_livro)
