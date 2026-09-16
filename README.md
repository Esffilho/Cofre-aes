# Cofre AES

API FastAPI para cofres de senhas com PBKDF2-HMAC-SHA256 (210.000 iterações) e AES-256-GCM. A senha-mestra só trafega no cabeçalho `X-Senha-Mestra`; não é armazenada, registrada ou retornada.

## Executar
1. Python 3.10+ e um projeto Supabase/PostgreSQL.
2. `python -m venv .venv` e `\.venv\Scripts\pip install -r requirements.txt`.
3. Copie `.env.exemplo` para `.env` e preencha credenciais reais localmente.
4. Crie as tabelas executando `schema/001_init.sql` no SQL Editor do Supabase.
5. `\.venv\Scripts\uvicorn app.main:app --reload` e abra `http://127.0.0.1:8000/`.

## API
`POST /cofres` cria; `POST /cofres/{id}/abrir` valida; `GET/POST /cofres/{id}/segredos` lista/cria; `GET/PUT/DELETE /cofres/{id}/segredos/{segredo}` faz CRUD. Operações protegidas exigem `X-Senha-Mestra`. Listagem nunca inclui material criptográfico.

Erros: 422 entrada inválida, 401 senha incorreta, 404 recurso inexistente e 500 registro adulterado/estrutura criptográfica inválida.

## Segurança
Cada cifragem usa nonce aleatório de 12 bytes, AAD vinculada ao cofre e segredo e etiqueta GCM de 16 bytes. O banco guarda somente salt, parâmetros e Base64 de dados cifrados. Nunca versione `.env`, chaves, senhas ou plaintext.

## Testes
Execute `\.venv\Scripts\python -m pytest testes -q` e `\.venv\Scripts\python -m compileall app`. Resultados e evidências ficam em `testes/resultados.md`.
