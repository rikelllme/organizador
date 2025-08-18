# chatbot.py
import json
import re
import requests

from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate
from langchain.memory import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithHistory

# === CONFIG ===
API_URL = "http://localhost:8000/projetos"
MODEL_NAME = "qwen2:4b"
OLLAMA_URL = "http://localhost:11434"
SESSION_ID = "sessao1"

# === Documentação da API ===
API_DOC = """
A API retorna uma lista de registros no formato:
[
  {
    "id": número identificador do registro,
    "overallStatus": status geral do projeto,
    "modelCategory": categoria do modelo (ex: smartphone, tablet),
    "plmDevModelName": nome do modelo no sistema PLM,
    "marketModelName": nome do modelo para o mercado,
    "laPia": data do evento LA PIA (AAAA-MM-DD),
    "laPra": data do evento LA PRA (AAAA-MM-DD),
    "laSra": data do evento LA SRA (AAAA-MM-DD),
    "laPsa": data do evento LA PSA (AAAA-MM-DD),
    "bbModelName": nome do modelo Backbone relacionado,
    "osversion": versão do sistema operacional
  }
]
"""

# === Função para carregar dados reais da API ===
def carregar_dados_api():
    try:
        resp = requests.get(API_URL, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        return []

dados_api = carregar_dados_api()
dados_json = json.dumps(dados_api, ensure_ascii=False, indent=2)

# === Catálogo de modelos (para identificar 'last_model') ===
def build_model_catalog(dados):
    nomes = set()
    for r in dados:
        for k in ("plmDevModelName", "marketModelName"):
            v = (r.get(k) or "").strip()
            if v:
                nomes.add(v)
    nomes_ordenados = sorted(nomes, key=lambda x: len(x), reverse=True)
    if nomes_ordenados:
        pattern = re.compile("|".join(map(re.escape, nomes_ordenados)), flags=re.IGNORECASE)
    else:
        pattern = None
    return nomes_ordenados, pattern

CATALOGO_MODELOS, REGEX_MODELOS = build_model_catalog(dados_api)

# === Inicialização ===
chat_history = InMemoryChatMessageHistory()
last_model = {"value": None}

# === LLM ===
llm = Ollama(model=MODEL_NAME, temperature=0, base_url=OLLAMA_URL)
output_parser = StrOutputParser()

# === Prompt ===
prompt_template = ChatPromptTemplate.from_messages([
    ("system", f"""
Você é um assistente que responde perguntas sobre registros de uma API.
Responda SOMENTE com base nos dados fornecidos abaixo.
Se a informação não estiver nos dados, responda exatamente: "Não encontrei essa informação."
Sempre que possível, formate a resposta de forma clara (listas, tabelas).

📖 Documentação da API:
{API_DOC}

📊 Dados disponíveis:
{dados_json}

IMPORTANTE:
- Se a pergunta não mencionar um modelo, mas houver um 'last_model' armazenado no histórico,
  continue respondendo sobre esse modelo.
    """),
    ("system", "Histórico da conversa anterior:\n{history}"),
    ("system", "Último modelo consultado: {last_model}"),
    ("human", "{input}")
])

# === Atualiza last_model ===
def atualizar_last_model(pergunta, resposta):
    if REGEX_MODELOS:
        match = REGEX_MODELOS.search(pergunta + " " + resposta)
        if match:
            last_model["value"] = match.group(0)

# === Cria a chain ===
chain = (
    RunnablePassthrough.assign(
        history=lambda x: "\n".join([m.content for m in chat_history.messages]),
        last_model=lambda x: last_model["value"] if last_model["value"] else "Nenhum"
    )
    | prompt_template
    | llm
    | output_parser
)

# Encapsula com histórico (novo padrão)
chain_with_history = RunnableWithHistory(
    chain,
    lambda session_id: chat_history
)

# === Função principal de chat ===
def chat(pergunta: str):
    resposta_completa = ""
    for token in chain_with_history.stream(
        {"input": pergunta},
        config={"configurable": {"session_id": SESSION_ID}}
    ):
        resposta_completa += token

    # Atualiza memória
    atualizar_last_model(pergunta, resposta_completa)
    return resposta_completa
