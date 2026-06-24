import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from projeto_API_Backend import Base, LivroDB, app
from fastapi.testclient import TestClient
import os

DATABASE_URL_TEST = 'sqlite:///:memory:'
engine = create_engine(DATABASE_URL_TEST,connect_args={'check_same_thread':False})
TestingSessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

client = TestClient(app)

os.environ['MINHA_SENHA'] = 'admin'
os.environ['MEU_USUARIO'] = 'admin'

@pytest.fixture(autouse=True)
def mock_redis(mocker):
    mock_redis_client = mocker.patch("projeto_API_Backend.redis_client",autospec=True)
    mock_redis_client.get.return_value = None

@pytest.fixture(scope='function')
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_books(db, mocker):
    response = client.get('/livros',auth=('admin','admin'))
    assert response.status_code == 200

    data = response.json()
    
    assert len(data['livros']) == 2
    assert data['livros'][0]['nome_livro'] == 'tata'
    assert data['livros'][0]['nome_autor'] == 'tawr'
    assert data['livros'][0]['ano_lancamento'] == 2000