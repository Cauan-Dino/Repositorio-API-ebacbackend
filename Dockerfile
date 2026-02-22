FROM python:3.13-slim

# define a pasta (diretório) onde o container vai “ficar trabalhando”.
WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && poetry install --no-root

# COPY . . Ela copia arquivos do seu projeto para dentro da imagem Docker.
    # primeiro . → a pasta atual do seu projeto (no seu PC)
    # segundo . → a pasta atual dentro do container (geralmente definida pelo WORKDIR)
COPY . .

EXPOSE 8000

CMD ["poetry","run","uvicorn","projeto_API_Backend:app","--host","0.0.0.0","--port","8000"]
