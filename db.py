"""Acesso ao Supabase: cliente e gravação do palpite.

O `id` do participante é gerado no cliente (uuid) e os inserts usam
`returning="minimal"`. Assim não é preciso ler a linha de volta (o que exigiria
uma política de SELECT pública e exporia telefone/e-mail de todos).
"""

import os
import uuid

import streamlit as st
from dotenv import load_dotenv
from postgrest.types import ReturnMethod
from supabase import create_client, Client

load_dotenv()


def _config(chave: str) -> str:
    """Lê a credencial do ambiente (.env) e cai para st.secrets (Streamlit Cloud)."""
    valor = os.getenv(chave)
    if valor:
        return valor
    return st.secrets[chave]


@st.cache_resource
def get_client() -> Client:
    """Cliente Supabase criado a partir do .env/secrets (cacheado entre reruns)."""
    return create_client(_config("SUPABASE_URL"), _config("SUPABASE_KEY"))


def salvar_palpite(nome: str, telefone: str, email: str, palpite: dict) -> None:
    """Grava o cadastro em `participants` e o resultado do mata-mata em `predictions`."""
    client = get_client()
    participant_id = str(uuid.uuid4())
    client.table("participants").insert(
        {"id": participant_id, "nome": nome, "telefone": telefone, "email": email},
        returning=ReturnMethod.minimal,
    ).execute()
    client.table("predictions").insert(
        {"participant_id": participant_id, "palpite": palpite},
        returning=ReturnMethod.minimal,
    ).execute()


def resultado_campeoes() -> list[dict]:
    """Retorna a agregação de palpites por campeão: [{'campeao': str, 'total': int}, ...].

    Usa a RPC `resultado_campeoes` (SECURITY DEFINER), que expõe só a contagem
    agregada ao público — sem política de SELECT na tabela nem leitura de PII.
    """
    client = get_client()
    resposta = client.rpc("resultado_campeoes").execute()
    return resposta.data or []
