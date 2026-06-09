# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado atual

App implementado em **Python + Streamlit** com persistência no **Supabase**. Arquivos principais:

- `streamlit_app.py` — entrypoint; fluxo em etapas (cadastro → grupos → terceiros → mata-mata → salvo) via `st.session_state`.
- `data.py` — 48 seleções em 12 grupos (A–L) com `iso2`; `flag_emoji()`/`rotulo()` derivam a bandeira por emoji (sem arquivos de imagem).
- `db.py` — cliente Supabase (`get_client`) e `salvar_palpite()`; gera `id` no cliente e usa `returning="minimal"` (não há política de SELECT pública, então não há readback de PII).
- `.streamlit/secrets.toml` — `SUPABASE_URL` e `SUPABASE_KEY` (gitignored).
- `.llm/prd.md` — PRD; `picture/picture.png` — design de referência.

Supabase: tabelas `participants` (nome/telefone/email) e `predictions` (`palpite` jsonb), ambas com RLS e política de **INSERT público**. Só o resultado do mata-mata é gravado em `predictions.palpite`.

## O produto (a partir do PRD)

Simulador da Copa do Mundo em **Python + Streamlit**, com **deploy no Streamlit Community Cloud**.

Fluxo do usuário:
1. Usuário informa **nome, telefone e e-mail**.
2. Em seguida faz seu **palpite da Copa do Mundo** (fase de grupos + chaveamento mata-mata até o campeão).

Diretrizes de design (ver `picture/picture.png`):
- Reproduzir o layout do simulador da imagem: cards de grupos com bandeiras e o bracket (chaveamento) do mata-mata.
- **Remover** todo o cabeçalho do site e a seção de notícias da referência — manter **somente o simulador**.
- As **bandeiras dos times, posições e demais dados** podem ser gravados localmente em uma pasta do projeto (assets locais), em vez de depender de serviços externos.

## Stack e comandos

Streamlit é o framework; dependências em `requirements.txt` (`streamlit`, `supabase`, `pandas`).

```bash
# Ambiente (o .venv já existe no repo, com as deps instaladas)
source .venv/bin/activate
pip install -r requirements.txt   # se precisar reinstalar

# Rodar localmente
streamlit run streamlit_app.py
```

- Deploy no Streamlit Community Cloud: entrypoint `streamlit_app.py`; configurar `SUPABASE_URL` e `SUPABASE_KEY` em *Secrets* do painel (mesmos valores de `.streamlit/secrets.toml`).

## Notas de arquitetura

- **Persistência**: Supabase (projeto `wtrgnyofhagwjllhymel`). `db.salvar_palpite()` insere em `participants` e `predictions`. Como as tabelas têm RLS com política só de **INSERT público**, o `id` é gerado no cliente e os inserts usam `returning="minimal"` — não há readback (evita expor PII via SELECT público).
- **Dados/bandeiras**: definidos em `data.py` (sem assets externos); bandeiras por emoji derivado do `iso2`. O bracket do mata-mata é derivado dos classificados da fase de grupos (`montar_bracket` em `streamlit_app.py`).
- **Simplificações educacionais**: usuário escolhe manualmente os 8 melhores terceiros (sem o desempate oficial da FIFA); só o resultado do mata-mata é persistido.
