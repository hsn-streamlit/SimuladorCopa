"""Simulador da Copa do Mundo 2026 — Streamlit + Supabase.

Fluxo em etapas: cadastro → fase de grupos (1º e 2º) → mata-mata → salvo.
O usuário escolhe só 1º e 2º de cada grupo; os 8 "melhores terceiros" que
completam o bracket de 32 são SORTEADOS aleatoriamente entre os 12 grupos
(1 terceiro por grupo). Só o resultado do mata-mata é gravado.
"""

import random

import pandas as pd
import streamlit as st

import db
from data import GRUPOS, flag_emoji, rotulo

st.set_page_config(page_title="Simulador da Copa do Mundo 2026", page_icon="🏆", layout="wide")

# Mapa nome -> time, para renderizar bandeira/rótulo a partir do nome guardado nos palpites.
TIME_POR_NOME = {t["nome"]: t for grupo in GRUPOS.values() for t in grupo}


def rotulo_nome(nome: str) -> str:
    # Palpites antigos podem ter seleções que não estão mais nos grupos atuais.
    time = TIME_POR_NOME.get(nome)
    return rotulo(time) if time else nome


# ---------------------------------------------------------------------------
# Visual (verde estilo da referência)
# ---------------------------------------------------------------------------
VERDE = "#00a651"

st.markdown(
    f"""
    <style>
      .bloco-titulo {{
        background:{VERDE}; color:#fff; font-weight:700; text-align:center;
        padding:.55rem; border-radius:8px; margin:.2rem 0 1rem;
        letter-spacing:.5px; text-transform:uppercase; font-size:.9rem;
      }}
      .grupo-cabecalho {{
        background:{VERDE}; color:#fff; font-weight:700; text-align:center;
        padding:.35rem; border-radius:6px 6px 0 0; margin:-1rem -1rem .6rem;
      }}
      .time-linha {{
        padding:.18rem .25rem; border-bottom:1px solid #eef1f2; font-size:.95rem;
      }}
      .campeao-box {{
        background:{VERDE}; color:#fff; text-align:center; font-size:1.4rem;
        font-weight:800; padding:1rem; border-radius:12px; margin:.5rem 0;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Estado inicial
# ---------------------------------------------------------------------------
if "etapa" not in st.session_state:
    st.session_state.etapa = "cadastro"

st.markdown("<div class='bloco-titulo'>Copa do Mundo da FIFA 2026</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Etapa 1 — Cadastro
# ---------------------------------------------------------------------------
def etapa_cadastro() -> None:
    st.subheader("1. Seus dados")
    with st.form("form_cadastro"):
        nome = st.text_input("Nome")
        telefone = st.text_input("Telefone")
        email = st.text_input("E-mail")
        enviar = st.form_submit_button("Começar palpite", type="primary")
    if enviar:
        if not (nome.strip() and telefone.strip() and email.strip()):
            st.error("Preencha nome, telefone e e-mail.")
            return
        st.session_state.dados = {
            "nome": nome.strip(),
            "telefone": telefone.strip(),
            "email": email.strip(),
        }
        st.session_state.etapa = "grupos"
        st.rerun()


# ---------------------------------------------------------------------------
# Etapa 2 — Fase de grupos (só 1º e 2º)
# ---------------------------------------------------------------------------
def etapa_grupos() -> None:
    st.subheader("2. Fase de grupos")
    st.write("Em cada grupo, escolha o **1º** e o **2º** colocados (os classificados ao mata-mata).")

    resultado = {}
    colunas = st.columns(3)
    for i, (letra, times) in enumerate(GRUPOS.items()):
        with colunas[i % 3].container(border=True):
            st.markdown(f"<div class='grupo-cabecalho'>Grupo {letra}</div>", unsafe_allow_html=True)
            for t in times:
                st.markdown(
                    f"<div class='time-linha'>{flag_emoji(t['iso2'])} {t['nome']}</div>",
                    unsafe_allow_html=True,
                )
            nomes = [t["nome"] for t in times]
            primeiro = st.selectbox(
                "1º colocado", nomes, index=None, placeholder="Escolha",
                format_func=rotulo_nome, key=f"g{letra}_1",
            )
            segundo = st.selectbox(
                "2º colocado", [n for n in nomes if n != primeiro], index=None,
                placeholder="Escolha", format_func=rotulo_nome, key=f"g{letra}_2",
            )
        if primeiro and segundo:
            resultado[letra] = {"1": primeiro, "2": segundo}

    faltando = len(GRUPOS) - len(resultado)
    st.divider()
    if st.button("Sortear terceiros e montar chaveamento", type="primary", disabled=faltando > 0):
        st.session_state.bracket, st.session_state.repescados = montar_bracket(resultado)
        st.session_state.etapa = "mata-mata"
        st.rerun()
    if faltando > 0:
        st.info(f"Defina 1º e 2º em todos os grupos ({faltando} faltando).")


def montar_bracket(grupos: dict) -> tuple[list, list]:
    """Monta os 32 classificados e sorteia os 8 melhores terceiros.

    No formato da Copa 2026 avançam os 2 primeiros de cada grupo (24) + os 8
    melhores terceiros (32 ao todo). Como este é um app educacional, em vez do
    desempate oficial da FIFA, os 8 terceiros são SORTEADOS aleatoriamente entre
    os 12 grupos (o 3º de cada grupo é a seleção de maior posição entre as duas
    não escolhidas pelo usuário).

    Retorna (slots, repescados): 32 slots na ordem 12 primeiros + 8 terceiros +
    12 segundos (pareando slot i com i+16), e a lista dos nomes sorteados.
    """
    primeiros = [grupos[l]["1"] for l in GRUPOS]   # 12
    segundos = [grupos[l]["2"] for l in GRUPOS]     # 12

    # 3º de cada grupo: melhor posicionado entre os dois não escolhidos.
    terceiro_por_grupo = {}
    for l in GRUPOS:
        escolhidos = {grupos[l]["1"], grupos[l]["2"]}
        restantes = [t["nome"] for t in GRUPOS[l] if t["nome"] not in escolhidos]
        terceiro_por_grupo[l] = restantes[0]

    grupos_sorteados = random.sample(list(GRUPOS), 8)   # 8 dos 12 grupos
    terceiros = [terceiro_por_grupo[l] for l in grupos_sorteados]

    slots = primeiros + terceiros + segundos             # 12 + 8 + 12 = 32
    return slots, terceiros


# ---------------------------------------------------------------------------
# Etapa 3 — Mata-mata
# ---------------------------------------------------------------------------
RODADAS = [
    ("Round of 32", "round_of_32"),
    ("Oitavas de final", "oitavas"),
    ("Quartas de final", "quartas"),
    ("Semifinais", "semis"),
    ("Final", "final"),
]


def etapa_mata_mata() -> None:
    st.subheader("3. Mata-mata")
    st.write("Escolha o vencedor de cada jogo. A próxima rodada aparece quando a atual estiver completa.")

    repescados = st.session_state.get("repescados", [])
    if repescados:
        st.info(
            "🎲 **Melhores terceiros sorteados** (entram no Round of 32): "
            + ", ".join(rotulo_nome(n) for n in repescados)
        )

    slots = st.session_state.bracket
    jogos = [[slots[i], slots[i + 16]] for i in range(16)]

    rodadas_registro = {}
    campeao = None
    completo = True

    for titulo, chave in RODADAS:
        st.markdown(f"<div class='bloco-titulo'>{titulo}</div>", unsafe_allow_html=True)
        colunas = st.columns(4)
        vencedores = []
        registro = []
        for idx, (a, b) in enumerate(jogos):
            key = f"{chave}_{idx}"
            # Evita crash caso uma escolha anterior tenha mudado os participantes do jogo.
            if st.session_state.get(key) not in (a, b):
                st.session_state.pop(key, None)
            with colunas[idx % 4].container(border=True):
                escolha = st.radio(
                    f"Jogo {idx + 1}", [a, b], index=None,
                    format_func=rotulo_nome, key=key,
                )
            vencedores.append(escolha)
            registro.append({"a": a, "b": b, "vencedor": escolha})

        if chave == "final":
            rodadas_registro[chave] = registro[0]
            campeao = vencedores[0]
        else:
            rodadas_registro[chave] = registro

        if any(v is None for v in vencedores):
            completo = False
            break
        if chave != "final":
            jogos = [[vencedores[i], vencedores[i + 1]] for i in range(0, len(vencedores), 2)]

    st.divider()
    if completo and campeao:
        st.markdown(f"<div class='campeao-box'>🏆 Campeão: {rotulo_nome(campeao)}</div>", unsafe_allow_html=True)
        if st.button("Salvar palpite", type="primary"):
            palpite = {"rodadas": rodadas_registro, "campeao": campeao}
            try:
                db.salvar_palpite(palpite=palpite, **st.session_state.dados)
            except Exception as exc:  # noqa: BLE001 - mostra o erro pro usuário educacional
                st.error(f"Erro ao salvar: {exc}")
            else:
                st.session_state.campeao = campeao
                st.session_state.etapa = "salvo"
                st.rerun()
    else:
        st.info("Complete todas as rodadas para salvar seu palpite.")


# ---------------------------------------------------------------------------
# Etapa 4 — Salvo
# ---------------------------------------------------------------------------
def etapa_salvo() -> None:
    st.balloons()
    st.success("Palpite salvo com sucesso! ✅")
    st.markdown(
        f"<div class='campeao-box'>🏆 Seu campeão: {rotulo_nome(st.session_state.campeao)}</div>",
        unsafe_allow_html=True,
    )
    if st.button("Fazer novo palpite"):
        st.session_state.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# Aba Resultado — agregação dos palpites por campeão
# ---------------------------------------------------------------------------
# O total exibido é multiplicado por este fator (regra do produto).
FATOR_PARTICIPANTES = 6


def aba_resultado() -> None:
    st.subheader("📊 Resultado dos palpites")
    col_botao, _ = st.columns([1, 4])
    if col_botao.button("🔄 Atualizar"):
        st.rerun()

    try:
        dados = db.resultado_campeoes()
    except Exception as exc:  # noqa: BLE001 - app educacional, mostra o erro
        st.error(f"Erro ao carregar resultados: {exc}")
        return

    if not dados:
        st.info("Ainda não há palpites salvos.")
        return

    total_real = sum(d["total"] for d in dados)
    total_exibido = total_real * FATOR_PARTICIPANTES

    st.metric("Total de participantes", f"{total_exibido:,}".replace(",", "."))

    linhas = [
        {
            "País": rotulo_nome(d["campeao"]),
            "Participantes": d["total"] * FATOR_PARTICIPANTES,
            "%": round(d["total"] / total_real * 100, 1),
        }
        for d in sorted(dados, key=lambda d: d["total"], reverse=True)
    ]
    df = pd.DataFrame(linhas)

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Participantes": st.column_config.NumberColumn(format="%d"),
            "%": st.column_config.ProgressColumn(
                "% dos palpites", format="%.1f%%", min_value=0, max_value=100
            ),
        },
    )
    st.bar_chart(df.set_index("País")["%"], height=320)


# ---------------------------------------------------------------------------
# Roteamento (abas)
# ---------------------------------------------------------------------------
ETAPAS = {
    "cadastro": etapa_cadastro,
    "grupos": etapa_grupos,
    "mata-mata": etapa_mata_mata,
    "salvo": etapa_salvo,
}

aba_simulador, aba_res = st.tabs(["🎮 Simulador", "📊 Resultado"])

with aba_simulador:
    st.title("🏆 Simulador da Copa do Mundo 2026")
    st.caption("Cadastre-se, defina os classificados de cada grupo e preencha o chaveamento até o campeão.")
    ETAPAS[st.session_state.etapa]()

with aba_res:
    aba_resultado()
