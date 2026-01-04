from fastapi import FastAPI,HTTPException,Depends
from fastapi.security import HTTPBasicCredentials,HTTPBasic
from pydantic import BaseModel
from typing import Optional
import secrets

from sqlalchemy import create_engine,Column ,Integer,String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session,sessionmaker

# 1. Criacao de objetos/ Variaveis

# 1.1 Criacao do objeto da classe FastAPI que permite a gente a conseguir utilizar os endpoints
app = FastAPI(
    title= 'API De livros',
    description= 'API de catálogos de livros do curso da ebac Back-end',
    version='1.0.0',
    contact={
        'email':'cauanppenha@gmail.com',
        'name': 'cauan dino penha'
        }
)

# 1.2 Criacao do objeto da classe HTTPBasic que nos permite colocar senhas e usuarios e utilizar a autenticacao do  HTTP Basic
security = HTTPBasic()

# 1.3 Criacao da variavel para criar um banco de dados

DATABASE_URL = 'sqlite:///./livros.db'

engine = create_engine(DATABASE_URL,connect_args={'check_same_thread': False})
Sessionlocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()


meus_livros = {}

# 2. Criacao de body model 

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
    def post_meus_livros(self,livro: Livro,db: Session):
        db_livro = db.query(LivroDB).filter(LivroDB.nome_livro == livro.nome_livro,LivroDB.nome_autor == livro.nome_autor).first()
        if db_livro:
            raise HTTPException(
                status_code=400,
                detail='Esse livro ja existe'
            )
        
        novo_livro = LivroDB(nome_livro = livro.nome_livro, nome_autor = livro.nome_autor,ano_lancamento = livro.ano_lancamento)
        db.add(novo_livro)
        db.commit()
        db.refresh(novo_livro)
        

        return {'message':'O livro foi adicionado com sucesso'}
    

# 3.3 Classe para metodos HTTP PUT
class PUT_metodohttp:
    # 3.3.1 Metodo PUT para atualizar um livro ja existente
    def put_meus_livros(self,id_livro:int,livro: Livro,db: Session):
        db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
        if not db_livro:
            raise HTTPException(
                status_code=404,
                detail='Esse livro nao existe'
            )

        db_livro.nome_livro = livro.nome_livro
        db_livro.ano_lancamento = livro.ano_lancamento
        db_livro.nome_autor = livro.nome_autor
        
        db.commit()
        db.refresh(db_livro)

        return {'message':'Seu livro foi atualizado com sucesso'}

# 3.4 Classe para metodos HTTP DELETE
class DEL_metodohttp:
    # 3.4.1 Metodo DELETE para excluir um livro
    def delete_meus_livros(self,id_livro:int,db: Session):
        db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()

        if not db_livro:
            raise HTTPException(
                status_code=404,
                detail='Esse livro nao existe'
        
            )
        db.delete(db_livro)
        db.commit()
        
        return {'message':'Seu livro foi deletado com sucesso'}

# 3.5 Classe para retornar livros cadastrados
class GET_metodohttp:
    # 3.5.1 Metodo GET para listar os livros cadastrados com paginação
    def get_meus_livros(self,db: Session ,page: int = 1, limit: int = 10):
        if page < 1 or limit < 1:
            raise HTTPException(status_code=400,detail='Page ou limit invalidos')
        
        livros = db.query(LivroDB).offset((page-1)*limit).limit(limit).all()

        if not livros:
            return {'message':'Ainda nao ha nada castrado'}
        
        total_livros = db.query(LivroDB).count()

        return {
            'pagina': page,
            'limite': limit,
            'total': total_livros,
            'livros': [
                {'id':livro.id,'nome_livro':livro.nome_livro,'nome_autor':livro.nome_autor,'ano_lancamento':livro.ano_lancamento}
                for livro in livros
                       ]
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
def get_livros(db: Session = Depends(sessao_db),page: int = 1,limit: int =10,_: None = Depends(objeto_autorizacao.autenticar_meu_usuario)):
    return objeto_get_metodohttp.get_meus_livros(db,page,limit)


# 5. Metodo POST

# 5.1 Criar um post para adicionar um livro
@app.post('/livros')
def post_livros(livro: Livro,db: Session = Depends(sessao_db),_: None = Depends(objeto_autorizacao.autenticar_meu_usuario)):
    return objeto_post_metodohttp.post_meus_livros(livro,db)


# 6. Metodo PUT

# 6.1 Criar um put para atualizar um livro ja existente
@app.put('/livros/{id_livro}')
def put_livros(id_livro:int,livro: Livro,db: Session = Depends(sessao_db),_: None = Depends(objeto_autorizacao.autenticar_meu_usuario)):
    return objeto_put_metodohttp.put_meus_livros(id_livro,livro,db)


# 7. Metodo DELETE

# 7.1 Criar um delete
@app.delete('/livros/{id_livro}')
def delete_livros(id_livro:int, _: None = Depends(objeto_autorizacao.autenticar_meu_usuario),db: Session = Depends(sessao_db)):
    return objeto_del_metodohttp.delete_meus_livros(id_livro,db)