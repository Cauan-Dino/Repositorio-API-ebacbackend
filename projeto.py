from fastapi import FastAPI,HTTPException

app = FastAPI()

meus_livros = {}

# 1. Criar um get para ver os livros que estao cadastrados
@app.get('/livros')
def get_meus_livros():
    if not meus_livros:
        return {'message':'Ainda nao ha nada cadastrado'}
    else:
        return {'livros':meus_livros}

# 2. Criar um post para adicionar um livro
@app.post('/adicionar_livro')
def post_meus_livros(nome:str,autor:str,ano_lancamento:int,id_livro:int):
    if id_livro in meus_livros:
        raise HTTPException(status_code=400,detail='Esse livro ja esta cadastrado')
    else:
        meus_livros[id_livro] = {'nome':nome,'autor':autor,'ano_lancamento':ano_lancamento}
        return {'message':f'Livro {nome} cadastrado com sucesso'}

# 3. Criar um put para atualizar um livro ja existente
@app.put('/atualizar_livro/{id_livro}')
def put_meus_livros(nome:str,autor:str,ano_lancamento:int,id_livro:int):
    meu_livro = meus_livros.get(id_livro)
    if id_livro not in meus_livros or not meus_livros:
        raise HTTPException(status_code=404,detail='Esse livro nao existe')
    else:
        meu_livro['nome'] = nome
        meu_livro['autor'] = autor
        meu_livro['ano_lancamento'] = ano_lancamento
        return {'message':f'Livro atualizado com sucesso'}

# 4. Criar um delete
@app.delete('/deletar_livro/{id_livro}')
def delete_meus_livros(id_livro:int):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404,detail='Nao foi possivel encontrar esse livro')
    else:
        del(meus_livros[id_livro])
        return{'message':'Livro deletado com sucesso'}

