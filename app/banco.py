from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

supabase: Client | None = None


def _cliente() -> Client:
    global supabase
    if supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL e SUPABASE_KEY são obrigatórios")
        supabase = create_client(url, key)
    return supabase


def buscar_cofre(cofre_id: str):
    resposta = (
        _cliente()
        .table("cofres")
        .select("*")
        .eq("id", cofre_id)
        .execute()
    )

    registros = resposta.data

    return registros[0] if registros else None


def inserir_cofre(dados: dict):
    resposta = (
        _cliente()
        .table("cofres")
        .insert(dados)
        .execute()
    )

    return resposta.data[0]


def inserir_segredo(dados: dict):
    resposta = (
        _cliente()
        .table("segredos")
        .insert(dados)
        .execute()
    )

    return resposta.data[0]


def buscar_segredo(segredo_id: str):
    resposta = (
        _cliente()
        .table("segredos")
        .select("*")
        .eq("id", segredo_id)
        .execute()
    )

    registros = resposta.data

    return registros[0] if registros else None


def listar_segredos(cofre_id: str):
    resposta = (
        _cliente()
        .table("segredos")
        .select(
            "id, titulo, usuario, url, criado_em"
        )
        .eq("cofre_id", cofre_id)
        .execute()
    )

    return resposta.data


def remover_segredo(segredo_id: str):
    (
        _cliente()
        .table("segredos")
        .delete()
        .eq("id", segredo_id)
        .execute()
    )

def atualizar_segredo(segredo_id: str, dados: dict):
    resposta = (
        _cliente()
        .table("segredos")
        .update(dados)
        .eq("id", segredo_id)
        .execute()
    )

    return resposta.data[0] if resposta.data else None