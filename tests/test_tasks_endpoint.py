from fastapi.testclient import TestClient
from projeto_API_Backend import app,sessao_db,autenticar_meu_usuario
import pytest
from fastapi.security import HTTPBasicCredentials
import os

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock_redis_client = mocker.patch("projeto_API_Backend.redis_client",autospec=True)
    mock_redis_client.get.return_value = None

def test_calcular_soma(mocker):
    mocker_somar_delay = mocker.patch("tasks.somar.delay")
    mocker_redis_lpush = mocker.patch("projeto_API_Backend.redis_client.lpush")
    mocker_redis_ltrim = mocker.patch("projeto_API_Backend.redis_client.ltrim")

    mocker_somar_delay.return_value.id = 'fake-task-id'

    response = client.post("/calcular/soma",params={'a':1,'b':2})
    assert response.status_code == 200
    assert response.json() == {
        'task_id': 'fake-task-id',
        'message': 'tarefa de soma enviada para execucao'
    }

    mocker_somar_delay.assert_called_once()
    mocker_somar_delay.assert_called_once()

def test_calcular_fatorial(mocker):
    mock_fatorial_delay = mocker.patch("tasks.fatorial.delay")
    mocker_redis_lpush = mocker.patch("projeto_API_Backend.redis_client.lpush")
    mocker_redis_ltrim = mocker.patch("projeto_API_Backend.redis_client.ltrim")
    
    mock_fatorial_delay.return_value.id = 'fake-task-id' 

    response = client.post("/calcular/fatorial",params={'n':5})
    assert response.status_code == 200
    assert response.json() == {
        'task_id': 'fake-task-id',
        'message': 'tarefa de fatorial enviada para execucao'
    }

    mock_fatorial_delay.assert_called_once()
    mock_fatorial_delay.assert_called_once()

@pytest.fixture(autouse=True)
def redis(mocker):
    mock_redis = mocker.patch('projeto_API_Backend.redis_client')
    mock_redis.get.return_value = None

os.environ['MEU_USUARIO'] = 'admin'
os.environ['MINHA_SENHA'] = 'admin'

def test_get_livros():
    reponse = client.get('/livros',auth=('admin','admin'))
    assert reponse.status_code == 200

def test_post_livros(mocker):
    mock_db = mocker.MagicMock()
    mock_atributos = mocker.MagicMock()

    mock_atributos.nome_livro = 'harry poter'
    mock_atributos.nome_autor = 'dwad'
    mock_atributos.ano_lancamento = 2016

    mock_db.query.return_value.filter.return_value.first.return_value = None

    mock_redis = mocker.patch('projeto_API_Backend.salvar_livro_redis',autospec=True)
    mock_enviar_evento = mocker.patch('projeto_API_Backend.enviar_evento',autospec=True)

    app.dependency_overrides[sessao_db] = lambda: mock_db
    
    payload = {
        'nome_livro':'harry poter',
        'nome_autor':'dwad',
        'ano_lancamento': 2016
    }
    
    response = client.post('/livros',json=payload,auth=('admin','admin'))
    assert response.status_code == 200
    assert response.json() == {'message':'O livro foi adicionado com sucesso'}

    app.dependency_overrides.clear()

    mock_redis.assert_called_once()
    mock_enviar_evento.assert_called_once()
    