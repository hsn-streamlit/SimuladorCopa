# Roteiro da Aula — Simulador da Copa do Mundo 2026 (Streamlit + Supabase)

Projeto **educacional**: construir, do zero, um app web em Python que coleta um cadastro e
um palpite da Copa do Mundo, salvando o resultado em um banco de dados na nuvem.

- **Duração sugerida:** ~2h30 (ajustável)
- **Resultado final:** app rodando localmente e pronto para deploy gratuito no Streamlit Cloud
- **Stack:** Python • Streamlit (interface) • Supabase/Postgres (banco)

---

## 1. Objetivos de aprendizagem

Ao final, o aluno será capaz de:

1. Estruturar um app Streamlit com **navegação em etapas** usando `st.session_state`.
2. Modelar **dados locais** (seleções, grupos) em Python, sem depender de serviços externos.
3. Conectar o app a um **banco Postgres na nuvem** (Supabase) e gravar dados.
4. Entender **RLS (Row Level Security)** e por que um INSERT pode falhar na leitura de volta.
5. Derivar um **chaveamento de mata-mata** a partir dos palpites da fase de grupos.

---

## 2. Pré-requisitos e ambiente (10 min)

- Python 3.11+ instalado e uma conta gratuita no [Supabase](https://supabase.com).
- Criar o ambiente virtual e instalar dependências:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install streamlit supabase pandas
```

- Congelar as dependências no `requirements.txt` (necessário para o deploy):

```
streamlit
supabase
pandas
```

**Conceito-chave:** o `requirements.txt` na raiz é o que o Streamlit Cloud usa para montar o
ambiente no deploy.

---

## 3. O produto: ler o PRD (10 min)

Abrir `.llm/prd.md` e a imagem de referência `picture/picture.png` e extrair os requisitos:

- App em Python + Streamlit, deploy no Streamlit Cloud.
- Usuário informa **nome, telefone e e-mail** e depois faz o **palpite**.
- Reproduzir o layout do simulador (cards de grupos + bracket), **sem** o cabeçalho do site
  e **sem** a seção de notícias.
- Bandeiras e dados podem ficar **locais** no projeto.

**Decisões de simplificação** (deixar explícito que é um projeto didático):

- Bandeiras por **emoji** (zero arquivos de imagem).
- Bracket de **32 seleções** (Round of 32 → Final).
- Na fase de grupos o usuário escolhe só **1º e 2º**; os 8 últimos lugares do bracket são
  preenchidos automaticamente.
- **Só o resultado do mata-mata** é gravado no banco.

---

## 4. Modelando os dados das seleções — `data.py` (20 min)

Conceitos: dicionários/listas em Python, e o truque dos **emojis de bandeira**.

```python
GRUPOS = {
    "A": [{"nome": "Brasil", "iso2": "BR"}, {"nome": "Suíça", "iso2": "CH"}, ...],
    # ... 12 grupos (A–L), 4 seleções cada = 48
}

def flag_emoji(iso2: str) -> str:
    # Cada letra do código do país vira um "regional indicator symbol".
    # Ex.: "BR" -> 🇧🇷
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())
```

**Demonstração ao vivo:** `python -c "from data import flag_emoji; print(flag_emoji('BR'))"`.

> Curiosidade para a turma: Inglaterra/Escócia/País de Gales não têm código ISO-2 simples e
> usam uma sequência especial de emoji — por isso há um pequeno mapa de exceções.

---

## 5. Configurando o Supabase (20 min)

1. Criar um projeto no Supabase; anotar a **Project URL** e a **publishable key**
   (em *Project Settings → API*).
2. Criar as duas tabelas (SQL Editor):

```sql
create table participants (
  id uuid primary key default gen_random_uuid(),
  nome text, telefone text, email text,
  created_at timestamptz default now()
);
create table predictions (
  id uuid primary key default gen_random_uuid(),
  participant_id uuid references participants(id),
  palpite jsonb,
  created_at timestamptz default now()
);
```

3. **Ligar o RLS e liberar INSERT público** (o app não usa login):

```sql
alter table participants enable row level security;
alter table predictions enable row level security;
create policy "public insert participants" on participants for insert to public with check (true);
create policy "public insert predictions"  on predictions  for insert to public with check (true);
```

4. Guardar as credenciais em `.streamlit/secrets.toml` (e adicionar ao `.gitignore`):

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "sb_publishable_xxx"
```

**Conceito-chave (RLS):** as tabelas começam fechadas; nada entra sem uma *policy*. Aqui
liberamos só o INSERT — ninguém consegue **ler** os dados de cadastro pela chave pública.

---

## 6. Camada de banco — `db.py` (20 min)

```python
import uuid
import streamlit as st
from postgrest.types import ReturnMethod
from supabase import create_client, Client

@st.cache_resource
def get_client() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def salvar_palpite(nome, telefone, email, palpite: dict) -> None:
    client = get_client()
    participant_id = str(uuid.uuid4())                 # geramos o id no cliente
    client.table("participants").insert(
        {"id": participant_id, "nome": nome, "telefone": telefone, "email": email},
        returning=ReturnMethod.minimal,
    ).execute()
    client.table("predictions").insert(
        {"participant_id": participant_id, "palpite": palpite},
        returning=ReturnMethod.minimal,
    ).execute()
```

**⚠️ Momento "armadilha didática" (muito importante):**
Por padrão o `supabase-py` faz o INSERT e **lê a linha de volta** (`return=representation`).
Como liberamos só INSERT (sem policy de SELECT), essa leitura falha com
`new row violates row-level security policy`. **Duas lições:**

1. O erro de RLS nem sempre é no INSERT — pode ser na **leitura de retorno**.
2. Solução elegante: gerar o `id` no próprio Python (`uuid4`) e usar
   `returning="minimal"`. Assim não precisamos ler de volta e **mantemos os dados privados**
   (não expomos telefone/e-mail com uma policy de SELECT pública).

`@st.cache_resource` evita recriar a conexão a cada interação.

---

## 7. O app e a navegação em etapas — `streamlit_app.py` (45 min)

Conceito central: o Streamlit **re-executa o script inteiro** a cada interação. Para ter
"telas", guardamos a etapa atual em `st.session_state` e roteamos para uma função.

```python
if "etapa" not in st.session_state:
    st.session_state.etapa = "cadastro"

ETAPAS = {"cadastro": etapa_cadastro, "grupos": etapa_grupos,
          "mata-mata": etapa_mata_mata, "salvo": etapa_salvo}
ETAPAS[st.session_state.etapa]()      # chama a função da etapa atual
```

### 7.1 Cadastro
- `st.form` com nome/telefone/e-mail; valida preenchimento; salva em
  `st.session_state.dados` e avança para `"grupos"` com `st.rerun()`.
- **Armadilha:** a *key* do widget não pode ter o mesmo nome da variável de estado que você
  escreve (por isso `form_cadastro` ≠ `dados`).

### 7.2 Fase de grupos (só 1º e 2º)
- `st.columns(3)` → grade de 3 colunas para os 12 cards (igual à imagem).
- Em cada card: cabeçalho "Grupo X", lista dos 4 times com bandeira, e dois `st.selectbox`
  (1º e 2º; o 2º exclui o time já escolhido).
- Botão "Montar chaveamento" só habilita quando os 12 grupos estão completos.

### 7.3 Montando o bracket de 32 automaticamente
```python
def montar_bracket(grupos: dict) -> list:
    primeiros = [grupos[l]["1"] for l in GRUPOS]   # 12
    segundos  = [grupos[l]["2"] for l in GRUPOS]   # 12
    terceiros = []                                  # 8 (grupos A–H)
    for l in list(GRUPOS)[:8]:
        escolhidos = {grupos[l]["1"], grupos[l]["2"]}
        restantes = [t["nome"] for t in GRUPOS[l] if t["nome"] not in escolhidos]
        terceiros.append(restantes[0])
    return primeiros + terceiros + segundos        # 32 slots
```
**Sacada matemática (explicar no quadro):** pareando o slot `i` com o slot `i+16`, dois times
do mesmo grupo nunca se enfrentam na 1ª rodada — porque suas posições no vetor diferem de
12, 20 ou 8, nunca de 16.

### 7.4 Mata-mata
- Rodadas: Round of 32 → Oitavas → Quartas → Semis → Final.
- Cada jogo é um `st.radio` com as duas seleções; a próxima rodada só aparece quando a atual
  está completa; os vencedores alimentam a rodada seguinte.
- **Armadilha:** se o usuário muda um palpite anterior, o confronto seguinte muda — então,
  antes de renderizar, descartamos do `session_state` qualquer escolha que não esteja mais
  entre os dois times do jogo (evita travar o app).

### 7.5 Salvar e tela final
- Monta o dicionário `palpite` (apenas o mata-mata) e chama `db.salvar_palpite`.
- Formato gravado em `predictions.palpite` (jsonb):

```json
{ "rodadas": { "round_of_32": [...], "oitavas": [...], "quartas": [...],
               "semis": [...], "final": {"a": "...", "b": "...", "vencedor": "..."} },
  "campeao": "Brasil" }
```

---

## 8. Rodar e testar localmente (15 min)

```bash
streamlit run streamlit_app.py
```

Percorrer o fluxo completo: cadastro → 12 grupos → bracket até o campeão → salvar.
Conferir no Supabase (SQL Editor) que o palpite chegou:

```sql
select p.nome, pr.palpite->>'campeao' as campeao
from participants p join predictions pr on pr.participant_id = p.id;
```

---

## 9. Deploy no Streamlit Community Cloud (15 min)

1. Subir o projeto para um repositório no GitHub (com `requirements.txt`, **sem** o
   `secrets.toml`).
2. Em [share.streamlit.io](https://share.streamlit.io): *New app* → escolher o repo e o
   entrypoint `streamlit_app.py`.
3. Em *Advanced settings → Secrets*, colar o mesmo conteúdo do `secrets.toml`
   (`SUPABASE_URL` e `SUPABASE_KEY`).
4. Deploy → compartilhar o link.

**Conceito-chave:** o sistema de arquivos do Streamlit Cloud é **efêmero** — por isso os
dados vão para o Supabase, e não para um arquivo local.

---

## 10. Encerramento e extensões (10 min)

Ideias para os alunos evoluírem o projeto:

- Validar formato de e-mail/telefone.
- Mostrar um **ranking** dos campeões mais escolhidos (exige uma policy de SELECT agregada).
- Substituir emojis por imagens de bandeira em `assets/`.
- Desenhar o bracket no formato simétrico de chave (como na imagem original).
- Permitir **editar** um palpite já enviado (introduz o conceito de identidade/sessão).

---

## Mapa dos arquivos do projeto

| Arquivo | Papel |
|---|---|
| `streamlit_app.py` | Entrypoint; navegação em etapas e telas |
| `data.py` | 48 seleções em 12 grupos + emoji de bandeira |
| `db.py` | Conexão com o Supabase e gravação do palpite |
| `requirements.txt` | Dependências (usado no deploy) |
| `.streamlit/secrets.toml` | Credenciais do Supabase (não versionar) |
| `.streamlit/config.toml` | Tema verde da interface |
