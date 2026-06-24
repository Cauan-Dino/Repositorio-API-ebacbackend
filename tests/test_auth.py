from fastapi.testclient import TestClient
from projeto_API_Backend import app
import os
import pytest

client = TestClient(app)

os.environ["MEU_USUARIO"] = 'admin'
os.environ["MINHA_SENHA"] = 'admin'

def test_autenticacao_usuario_esperando_erro_por_parto_do_usuario():
    response = client.get(
        '/',
        auth=('usuario-incorreto','admin')
    )

    assert response.status_code == 401

def test_autenticacao_usuario_esperando_erro_por_parto_da_senha():
    response = client.get(
        '/',
        auth=('admin','senha-incorreta')
    )

    assert response.status_code == 401


def test_autenticacao_usuario_com_sucesso():
    response = client.get(
        '/',
        auth=('admin','admin')
    )

    assert response.status_code == 200