import json
import re
import requests
from typing import Dict

from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import InMemoryChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithHistory

# === CONFIG ===
API_URL = "http://localhost:8000/projetos"
MODEL_NAME = "qwen2:4b"  # ou o modelo que estiver usando
OLLAMA_URL = "http://localhost:11434"
# O ID da sessão agora é passado como um argumento, tornando o app mais flexível
DEFAULT_SESSION_ID = "sessao_padrao_1"

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
    """Carrega os dados da API com tratamento de erros."""
    try:
        # Adicionado um timeout para evitar que o programa trave indefinidamente
        resp = requests.get(API_URL, timeout=10)
        resp.raise_for_status()  # Lança um erro para status HTTP 4xx/5xx
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API: {e}")
        # Retorna uma lista vazia para que o resto do script não quebre
        return []

dados_api = carregar_dados_api()
# Garante que mesmo com dados vazios, o JSON seja uma lista vazia '[]'
dados_json = json.dumps(dados_api, ensure_ascii=False, indent=2) if dados_api else "[]"

# === Catálogo de modelos (para identificar 'last_model') ===
def build_model_catalog(dados):
    """Constrói um catálogo de nomes de modelo e uma regex para encontrá-los."""
    if not dados:
        return set(), None
    nomes = set()
    for r in dados:
        for k in ("plmDevModelName", "marketModelName"):
            v = (r.get(k) or "").strip()
            if v:
                nomes.add(v)
    
    # Ordena por comprimento para garantir que nomes mais longos (ex: "Galaxy S25 Ultra")
    # sejam encontrados antes de nomes mais curtos (ex: "Galaxy S25")
    nomes_ordenados = sorted(list(nomes), key=len, reverse=True)
    
    if not nomes_ordenados:
        return set(), None
        
    # Escapa caracteres especiais para a regex
    pattern = re.compile("|".join(map(re.escape, nomes_ordenados)), flags=re.IGNORECASE)
    return set(nomes_ordenados), pattern

CATALOGO_MODELOS, REGEX_MODELOS = build_model_catalog(dados_api)

# === GERENCIAMENTO DE ESTADO POR SESSÃO (A GRANDE MELHORIA) ===
# Em vez de variáveis globais, usamos dicionários para armazenar o estado de cada sessão.
# Isso permite que múltiplas conversas ocorram simultaneamente sem interferência.
store: Dict[str, BaseChatMessageHistory] = {}
last_model_store: Dict[str, str] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Cria ou recupera um histórico de chat para a sessão informada."""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

def get_last_model(session_id: str) -> str:
    """Recupera o último modelo consultado para a sessão."""
    return last_model_store.get(session_id, "Nenhum")

def set_last_model(session_id: str, model_name: str):
    """Define o último modelo consultado para a sessão."""
    if REGEX_MODELOS and model_name:
        # Normaliza o nome do modelo para o nome exato do catálogo para consistência
        match = REGEX_MODELOS.search(model_name)
        if match:
            last_model_store[session_id] = match.group(0)

# === LLM ===
llm = Ollama(model=MODEL_NAME, temperature=0, base_url=OLLAMA_URL)
output_parser = StrOutputParser()

# === Prompt (Modernizado) ===
# Usamos MessagesPlaceholder para indicar onde o histórico da conversa deve ser inserido.
# O RunnableWithHistory irá preencher isso automaticamente.
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
    """),
    # Este placeholder será preenchido pelo RunnableWithHistory
    MessagesPlaceholder(variable_name="history"),
    # A lógica de last_model é personalizada, então a mantemos
    ("system", "Contexto Adicional: O último modelo que estávamos discutindo é: {last_model}"),
    ("human", "{input}")
])

# === Chain (Simplificada) ===
# Removemos a atribuição manual de 'history'. A chain agora só precisa
# saber como obter o 'last_model' para a sessão atual.
chain = (
    RunnablePassthrough.assign(
        # O session_id é acessado a partir do 'config' passado para a chain.
        last_model=lambda x: get_last_model(x["config"]["configurable"]["session_id"])
    )
    | prompt_template
    | llm
    | output_parser
)

# Encapsula com histórico usando o novo padrão
chain_with_history = RunnableWithHistory(
    chain,
    get_session_history,
    input_messages_key="input",       # A chave da pergunta do usuário
    history_messages_key="history",   # A chave do placeholder no prompt
)

# === Função de atualização ===
def atualizar_last_model(session_id: str, pergunta: str, resposta: str):
    """Busca por nomes de modelo na pergunta e resposta para atualizar o contexto da sessão."""
    if REGEX_MODELOS:
        # Busca primeiro na pergunta, que tem maior probabilidade de ser explícita
        match = REGEX_MODELOS.search(pergunta)
        if match:
            set_last_model(session_id, match.group(0))
            return # Encontrou na pergunta, não precisa olhar a resposta
        
        # Se não encontrou na pergunta, busca na resposta do LLM
        match = REGEX_MODELOS.search(resposta)
        if match:
            set_last_model(session_id, match.group(0))

# === Função principal de chat ===
def chat(pergunta: str, session_id: str):
    """Executa a chain de conversação para uma dada sessão."""
    print(f"\n--- [Sessão: {session_id}] ---")
    print(f"👤 Usuário: {pergunta}")
    
    # O config é essencial para o RunnableWithHistory saber qual histórico usar.
    config = {"configurable": {"session_id": session_id}}
    
    resposta_completa = ""
    print("🤖 Assistente: ", end="", flush=True)
    for token in chain_with_history.stream({"input": pergunta}, config=config):
        print(token, end="", flush=True)
        resposta_completa += token
    print() # Nova linha no final

    # Atualiza o último modelo consultado para esta sessão
    atualizar_last_model(session_id, pergunta, resposta_completa)
    
    # Opcional: imprimir o estado atual para depuração
    # print(f"DEBUG: Histórico da sessão '{session_id}': {get_session_history(session_id).messages}")
    # print(f"DEBUG: Último modelo da sessão '{session_id}': {get_last_model(session_id)}")


# === Exemplo de uso ===
if __name__ == "__main__":
    print("Iniciando o chatbot. Os dados da API foram carregados.")
    if not dados_api:
        print("AVISO: Não foi possível carregar dados da API. O chatbot responderá com base em dados vazios.")
    
    # Exemplo de conversa com a sessão 1
    chat("Qual a data LA PIA do modelo Galaxy S25 Ultra?", session_id="sessao1")
    chat("E qual a versão do sistema operacional dele?", session_id="sessao1") # Pergunta de acompanhamento
    
    # Exemplo de conversa com a sessão 2, totalmente independente
    chat("Me liste os modelos da categoria smartphone", session_id="sessao2")
    chat("Qual o status do Vision Pro?", session_id="sessao2")
    chat("e o PRA dele?", session_id="sessao2") # Pergunta de acompanhamento sobre Vision Pro

    # Voltando para a sessão 1 para mostrar que a memória foi mantida
    chat("Obrigado pelas informações sobre o S25 Ultra.", session_id="sessao1")

