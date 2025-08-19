# app.py
import streamlit as st
import requests
import datetime
from langchain_community.llms import Ollama
from difflib import get_close_matches

# ================= CONFIGURAÇÃO =================
API_URL = "http://localhost:8000/projetos"
MODEL_NAME = "qwen2:4b"
OLLAMA_URL = "http://localhost:11434"

# ================= FUNÇÕES =================
def carregar_dados_api():
    try:
        resp = requests.get(API_URL, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao carregar dados da API: {e}")
        return []

# Exemplo de mapa de intenções (vindo do PDF)
mapa_perguntas = [
    {"exemplo": "quais modelos vão sair um novo modelo",
     "campos": ["laPia", "marketModelName", "plmDevModelName"]},
    {"exemplo": "quais projetos estão atrasados",
     "campos": ["overallStatus", "laPra"]}
]

def identificar_campos(pergunta):
    exemplos = [m["exemplo"] for m in mapa_perguntas]
    match = get_close_matches(pergunta.lower(), exemplos, n=1, cutoff=0.4)
    if match:
        for m in mapa_perguntas:
            if m["exemplo"] == match[0]:
                return m["campos"]
    return []

def filtrar_dados(pergunta, dados_api):
    campos = identificar_campos(pergunta)
    hoje = str(datetime.date.today())

    if "laPia" in campos:
        resultados = [p for p in dados_api if p.get("laPia") and p["laPia"] >= hoje]
        return resultados
    elif "overallStatus" in campos:
        resultados = [p for p in dados_api if p.get("overallStatus") in ["Atrasado", "atrasado"]]
        return resultados
    else:
        return dados_api

def gerar_texto_projetos(projetos, campos):
    linhas = []
    for p in projetos:
        itens = []
        for c in campos:
            if c in p:
                itens.append(f"{c}: {p[c]}")
        linhas.append(" | ".join(itens))
    return "\n".join(linhas) if linhas else "Não encontrei essa informação."

# ================= CARREGA DADOS =================
dados_api = carregar_dados_api()

# ================= INICIALIZA LLM =================
llm = Ollama(model=MODEL_NAME, temperature=0, base_url=OLLAMA_URL)

# ================= STREAMLIT UI =================
st.set_page_config(page_title="Chat de Projetos", layout="wide")
st.title("💬 Chat de Projetos")

if "history" not in st.session_state:
    st.session_state.history = []

# Caixa de input
with st.form("chat_form", clear_on_submit=True):
    pergunta = st.text_input("Digite sua pergunta")
    enviar = st.form_submit_button("Enviar")

if enviar and pergunta:
    # Filtra dados
    campos = identificar_campos(pergunta)
    resultados = filtrar_dados(pergunta, dados_api)
    subset_texto = gerar_texto_projetos(resultados, campos) if campos else ""

    # Monta prompt
    prompt = f"""
Pergunta: {pergunta}

Dados relevantes:
{subset_texto}

Responda em linguagem natural, clara e resumida.
Se não houver informação, diga: "Não encontrei essa informação."
    """

    # Chama LLM
    resposta = llm.invoke(prompt)

    # Salva no histórico
    st.session_state.history.append({"user": pergunta, "ai": resposta})

# ================= EXIBE HISTÓRICO ESTILO CHAT =================
for chat in st.session_state.history[::-1]:
    st.markdown(
        f"<div style='text-align:right; background-color:#DCF8C6; padding:8px; border-radius:10px; margin:5px 0;'>{chat['user']}</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div style='text-align:left; background-color:#F1F0F0; padding:8px; border-radius:10px; margin:5px 0;'>{chat['ai']}</div>",
        unsafe_allow_html=True
    )
