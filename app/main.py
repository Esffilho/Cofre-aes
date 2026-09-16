from uuid import uuid4

from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone
from app import banco
from app.cripto import (
    ITERACOES_PADRAO,
    derivar_chave,
    gerar_sal,
    para_b64,
    de_b64,
    cifrar,
    decifrar,
    criar_verificador,
    senha_mestra_correta,
)
from app.modelos import NovoCofre, NovoSegredo


app = FastAPI(title="Cofre de Senhas", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(STATIC_DIR / "index.html")


def montar_aad_segredo(cofre_id: str, segredo_id: str) -> bytes:
    """
    Monta o AAD de um segredo.

    O formato obrigatório é:
    cofre_id|segredo_id
    """
    return f"{cofre_id}|{segredo_id}".encode("utf-8")


def obter_chave_validada(
    cofre_id: str,
    senha_mestra: str,
):
    """
    Busca o cofre, deriva a chave usando PBKDF2
    e verifica a senha-mestra através do verificador.

    Retorna:
        (cofre, chave)

    Erros:
        404 -> cofre inexistente
        401 -> senha-mestra incorreta
    """

    cofre = banco.buscar_cofre(cofre_id)

    if cofre is None:
        raise HTTPException(
            status_code=404,
            detail="cofre não encontrado",
        )

    try:
        sal = de_b64(cofre["kdf_sal"])
        if len(sal) != 16:
            raise ValueError("sal inválido")
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=500, detail="registro adulterado")

    chave = derivar_chave(
        senha_mestra,
        sal,
        cofre["kdf_iteracoes"],
    )

    try:
        campos = (
            cofre["verificador_nonce"],
            cofre["verificador_criptograma"],
            cofre["verificador_etiqueta"],
        )
        # Estrutura inválida é corrupção; uma etiqueta válida que não confere
        # apenas indica uma senha-mestra diferente.
        for campo in campos:
            de_b64(campo)
        if len(de_b64(campos[0])) != 12 or len(de_b64(campos[2])) != 16:
            raise ValueError("verificador inválido")
        senha_correta = senha_mestra_correta(chave, *campos, cofre_id)
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=500, detail="registro adulterado")

    if not senha_correta:
        raise HTTPException(
            status_code=401,
            detail="senha-mestra incorreta",
        )

    return cofre, chave


@app.post("/cofres", status_code=201)
def criar_cofre(dados: NovoCofre):
    """
    Cria um novo cofre.

    Fluxo:
    1. Gera identificador.
    2. Gera sal aleatório.
    3. Deriva chave com PBKDF2.
    4. Cria o verificador "cofre-ok".
    5. Salva os dados no banco.
    """

    cofre_id = str(uuid4())

    sal = gerar_sal()

    chave = derivar_chave(
        dados.senha_mestra,
        sal,
        ITERACOES_PADRAO,
    )

    (
        verificador_nonce,
        verificador_criptograma,
        verificador_etiqueta,
    ) = criar_verificador(
        chave,
        cofre_id,
    )

    registro = {
        "id": cofre_id,
        "nome": dados.nome,
        "kdf_sal": para_b64(sal),
        "kdf_iteracoes": ITERACOES_PADRAO,
        "verificador_nonce": verificador_nonce,
        "verificador_criptograma": verificador_criptograma,
        "verificador_etiqueta": verificador_etiqueta,
    }

    banco.inserir_cofre(registro)

    return {
        "id": cofre_id,
    }


@app.post("/cofres/{cofre_id}/abrir")
def abrir_cofre(
    cofre_id: str,
    x_senha_mestra: str = Header(..., min_length=8, max_length=256),
):
    """
    Confere se a senha-mestra está correta.
    """

    obter_chave_validada(
        cofre_id,
        x_senha_mestra,
    )

    return {
        "mensagem": "cofre aberto",
    }


@app.post("/cofres/{cofre_id}/segredos", status_code=201)
def criar_segredo(
    cofre_id: str,
    dados: NovoSegredo,
    x_senha_mestra: str = Header(..., min_length=8, max_length=256),
):
    """
    Cria um novo segredo no cofre.
    """

    _, chave = obter_chave_validada(
        cofre_id,
        x_senha_mestra,
    )

    segredo_id = str(uuid4())

    aad = montar_aad_segredo(
        cofre_id,
        segredo_id,
    )

    (
        nonce,
        criptograma,
        etiqueta,
    ) = cifrar(
        chave,
        dados.senha,
        aad,
    )

    registro = {
        "id": segredo_id,
        "cofre_id": cofre_id,
        "titulo": dados.titulo,
        "usuario": dados.usuario,
        "url": dados.url,
        "nonce": nonce,
        "criptograma": criptograma,
        "etiqueta": etiqueta,
    }

    banco.inserir_segredo(registro)

    return {
        "id": segredo_id,
    }


@app.get("/cofres/{cofre_id}/segredos")
def listar_segredos(
    cofre_id: str,
    x_senha_mestra: str = Header(..., min_length=8, max_length=256),
):
    """
    Lista os metadados dos segredos.

    Nunca devolve:
    - nonce
    - criptograma
    - etiqueta
    - senha
    """

    obter_chave_validada(
        cofre_id,
        x_senha_mestra,
    )

    return banco.listar_segredos(cofre_id)


@app.get("/cofres/{cofre_id}/segredos/{segredo_id}")
def ler_segredo(
    cofre_id: str,
    segredo_id: str,
    x_senha_mestra: str = Header(..., min_length=8, max_length=256),
):
    """
    Recupera e decifra um segredo.
    """

    _, chave = obter_chave_validada(
        cofre_id,
        x_senha_mestra,
    )

    segredo = banco.buscar_segredo(segredo_id)

    if segredo is None or segredo["cofre_id"] != cofre_id:
        raise HTTPException(
            status_code=404,
            detail="segredo não encontrado",
        )

    aad = montar_aad_segredo(
        cofre_id,
        segredo_id,
    )

    try:
        senha = decifrar(
            chave,
            segredo["nonce"],
            segredo["criptograma"],
            segredo["etiqueta"],
            aad,
        )

    except (ValueError, KeyError, TypeError, UnicodeError):
        raise HTTPException(
            status_code=500,
            detail="registro adulterado",
        )

    return {
        "id": segredo["id"],
        "titulo": segredo["titulo"],
        "usuario": segredo["usuario"],
        "url": segredo["url"],
        "senha": senha,
    }


@app.put("/cofres/{cofre_id}/segredos/{segredo_id}")
def atualizar_segredo(
    cofre_id: str,
    segredo_id: str,
    dados: NovoSegredo,
    x_senha_mestra: str = Header(..., min_length=8, max_length=256),
):
    """
    Substitui a senha de um segredo.

    A nova cifragem obrigatoriamente gera
    um novo nonce.
    """

    _, chave = obter_chave_validada(
        cofre_id,
        x_senha_mestra,
    )

    segredo = banco.buscar_segredo(segredo_id)

    if segredo is None or segredo["cofre_id"] != cofre_id:
        raise HTTPException(
            status_code=404,
            detail="segredo não encontrado",
        )

    aad = montar_aad_segredo(
        cofre_id,
        segredo_id,
    )

    (
        nonce,
        criptograma,
        etiqueta,
    ) = cifrar(
        chave,
        dados.senha,
        aad,
    )

    atualizacao = {
        "titulo": dados.titulo,
        "usuario": dados.usuario,
        "url": dados.url,
        "nonce": nonce,
        "criptograma": criptograma,
        "etiqueta": etiqueta,
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    }

    banco.atualizar_segredo(
        segredo_id,
        atualizacao,
    )

    return {
        "id": segredo_id,
        "mensagem": "segredo atualizado",
    }


@app.delete("/cofres/{cofre_id}/segredos/{segredo_id}")
def remover_segredo(
    cofre_id: str,
    segredo_id: str,
    x_senha_mestra: str = Header(..., min_length=8, max_length=256),
):
    """
    Remove um segredo.
    """

    obter_chave_validada(
        cofre_id,
        x_senha_mestra,
    )

    segredo = banco.buscar_segredo(segredo_id)

    if segredo is None or segredo["cofre_id"] != cofre_id:
        raise HTTPException(
            status_code=404,
            detail="segredo não encontrado",
        )

    banco.remover_segredo(segredo_id)

    return {
        "mensagem": "segredo removido",
    }
