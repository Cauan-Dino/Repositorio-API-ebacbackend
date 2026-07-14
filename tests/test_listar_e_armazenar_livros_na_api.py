import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from projeto_API_Backend import app, sessao_db, autenticar_meu_usuario  # ← depois
import pytest
from fastapi.security import HTTPBasicCredentials
from pytest_mock import MockerFixture


client = TestClient(app)

@pytest.fixture(autouse=True)
def autenticacao_do_usuario_redis_e_banco_de_dados(mocker: MockerFixture):
    # Mocka a autenticacao de usuario e senha
    app.dependency_overrides[autenticar_meu_usuario] = lambda: None

    # Mocka o Redis
    redis_mockado = mocker.patch('projeto_API_Backend.redis_client',autospec=True)
    redis_mockado.get.return_value = None

    # Mocka o banco de dados
    mock_db = mocker.MagicMock()
    app.dependency_overrides[sessao_db] = lambda: mock_db

    yield mock_db

    app.dependency_overrides.clear()

def test_listar_livros(autenticacao_do_usuario_redis_e_banco_de_dados,mocker: MockerFixture):
    mock_db = autenticacao_do_usuario_redis_e_banco_de_dados
    
    # Inserir informacoes falsas no banco de dados
    livro_falso = mocker.MagicMock()
    livro_falso.id = 1
    livro_falso.nome_livro = 'livro-falso'
    livro_falso.nome_autor = 'autor-falso'
    livro_falso.ano_lancamento = 2000

    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [livro_falso]
    mock_db.query.return_value.count.return_value = 1

    response = client.get('/livros?page=1&limit=10')
    assert response.status_code == 200
    
    dados = response.json()
    assert dados['livros'][0]['livro_id'] == 1
    assert dados['livros'][0]['nome_livro'] == 'livro-falso'
    assert dados['livros'][0]['nome_autor'] == 'autor-falso'
    assert dados['livros'][0]['ano_lancamento'] == 2000

def test_adicionar_livro(autenticacao_do_usuario_redis_e_banco_de_dados,mocker: MockerFixture):
    mock_db = autenticacao_do_usuario_redis_e_banco_de_dados
    
    mock_db.query.return_value.filter.return_value.first = lambda: None

    payload = {
        'nome_livro':'livro-falso',
        'nome_autor': 'autor-falso',
        'ano_lancamento':2000,
        'id':1
    }

    mock_salvar_redis = mocker.patch('projeto_API_Backend.salvar_livro_redis')
    mock_enviar_evento = mocker.patch('projeto_API_Backend.enviar_evento')

    response = client.post('/livros',json=payload)
    assert response.status_code == 200
    assert response.json() == {'message':'O livro foi adicionado com sucesso'}

    mock_salvar_redis.assert_called_once()
    mock_enviar_evento.assert_called_once()
