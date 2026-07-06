"""
agente.py — Agente baseado em LLM (Ollama) que usa o Revisor de regras como ferramenta.

Papéis (o ponto central da questão 3 da lista):
  - o LLM é o AGENTE/CONTROLADOR: interpreta o pedido em linguagem natural, decide
    QUANDO chamar as ferramentas e conversa sobre o resultado;
  - o RACIOCÍNIO de conformidade continua 100% no motor de regras (`revisor.py`).
    O LLM NÃO julga o artigo nem inventa notas — ele orquestra e explica o parecer real.

Comunicação com o Ollama usa apenas a biblioteca padrão (urllib) — sem dependências
pip novas. Configuração por variáveis de ambiente (todas opcionais):
  - OLLAMA_HOST   (padrão http://localhost:11434)
  - OLLAMA_MODEL  (padrão llama3.2 — precisa suportar tool calling)
"""
from __future__ import annotations

import json
import os
import unicodedata
import urllib.request

from revisor import RevisorCientificoLocal


def _sem_acento(texto):
    """Minúsculo e sem acentos, para casar nomes de dimensão de forma tolerante."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower().strip()

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

_TIMEOUT_S = 120.0        # geração pode ser lenta em modelo local
_TIMEOUT_PING_S = 1.5
_MAX_ITERACOES = 5        # teto de idas ao LLM por mensagem (evita loop de tools)

_SYSTEM = (
    "Você é um assistente que ajuda a avaliar a qualidade metodológica de artigos "
    "científicos, conversando em português brasileiro claro.\n"
    "Você NÃO julga o artigo por conta própria. Para qualquer afirmação sobre a "
    "qualidade do artigo, você DEVE primeiro chamar a ferramenta 'revisar_artigo', "
    "que executa um motor de regras determinístico e devolve o parecer real "
    "(pontuação, decisão, achados). Para aprofundar uma dimensão específica, use "
    "'detalhar_dimensao'.\n"
    "REGRAS: (1) nunca invente notas, achados ou trechos — use somente o que as "
    "ferramentas retornarem; (2) fundamente a resposta nos dados do parecer, citando "
    "a pontuação e os achados relevantes; (3) seja conciso e direto."
)

# Esquema das ferramentas expostas ao LLM (formato de tools do Ollama / OpenAI-like).
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "revisar_artigo",
            "description": (
                "Executa o motor de regras sobre o artigo atualmente carregado e "
                "retorna o parecer: pontuação (0-100), decisão sugerida, notas por "
                "dimensão e achados. Use antes de comentar a qualidade do artigo."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detalhar_dimensao",
            "description": (
                "Retorna os achados detalhados de uma dimensão específica do último "
                "parecer (ex.: 'metodologia', 'evidências', 'ética', 'referências')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dimensao": {
                        "type": "string",
                        "description": "Nome ou parte do nome da dimensão desejada.",
                    }
                },
                "required": ["dimensao"],
            },
        },
    },
]


def _http_json(url, body=None, timeout=_TIMEOUT_S):
    """POST (body dict) ou GET (body None) de JSON usando só a biblioteca padrão."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method="POST" if data else "GET",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def disponivel():
    """True se o Ollama está acessível (pré-requisito para o agente funcionar)."""
    try:
        _http_json(OLLAMA_HOST + "/api/tags", timeout=_TIMEOUT_PING_S)
        return True
    except Exception:
        return False


class OllamaIndisponivel(RuntimeError):
    """Levantada quando o agente não consegue falar com o Ollama."""


class AgenteRevisor:
    """
    Agente LLM que mantém o artigo em contexto e expõe o Revisor como ferramentas.

    Uso:
        agente = AgenteRevisor(texto_do_artigo)
        resp = agente.conversar("Esse artigo tem problema de metodologia?")
        print(resp["resposta"])        # texto em linguagem natural
        print(resp["ferramentas"])     # tools chamadas nesta rodada (para a UI)
    """

    def __init__(self, texto_artigo, modelo=OLLAMA_MODEL):
        self.texto_artigo = (texto_artigo or "").strip()
        self.modelo = modelo
        self.revisor = RevisorCientificoLocal()
        self.ultimo_parecer = None
        self.mensagens = [{"role": "system", "content": _SYSTEM}]

    # ------------------------------------------------------------------ tools --
    def _tool_revisar_artigo(self):
        if not self.texto_artigo:
            return {"erro": "Nenhum artigo foi carregado."}
        self.ultimo_parecer = self.revisor.revisar(self.texto_artigo)
        p = self.ultimo_parecer
        return {
            "pontuacao": p["pontuacao"],
            "decisao": p["decisao"],
            "dimensoes": [
                {"nome": d["nome"], "nota": d["nota"], "achados": len(d["achados"])}
                for d in p["dimensoes"]
            ],
            "achados_graves": [
                {"dimensao": a.dimensao, "mensagem": a.mensagem}
                for a in p["achados"] if a.nivel == "grave"
            ],
            "citacoes": p["citacoes"],
            "palavras": p["palavras"],
            "secoes_detectadas": p["secoes"],
        }

    def _tool_detalhar_dimensao(self, dimensao):
        if self.ultimo_parecer is None:
            self._tool_revisar_artigo()
        if self.ultimo_parecer is None:
            return {"erro": "Nenhum artigo foi carregado."}
        alvo = _sem_acento(dimensao)
        disponiveis = [d["nome"] for d in self.ultimo_parecer["dimensoes"]]
        if not alvo:
            return {"erro": "Informe o nome da dimensão.", "dimensoes": disponiveis}
        tokens = [t for t in alvo.split() if len(t) >= 3]
        for d in self.ultimo_parecer["dimensoes"]:
            nome_norm = _sem_acento(d["nome"])
            # casa por substring OU por prefixo de palavra (ex.: "metodologia"
            # -> "rigor metodologico"; "referencias" -> "referencial ...").
            if alvo in nome_norm or any(t[:5] in nome_norm for t in tokens):
                return {
                    "dimensao": d["nome"],
                    "nota": d["nota"],
                    "achados": [
                        {
                            "nivel": a.nivel,
                            "mensagem": a.mensagem,
                            "trecho": a.trecho,
                            "recomendacao": a.recomendacao,
                        }
                        for a in d["achados"]
                    ],
                }
        return {"erro": f"Dimensão '{dimensao}' não encontrada.", "dimensoes": disponiveis}

    def _executar_tool(self, nome, argumentos):
        if nome == "revisar_artigo":
            return self._tool_revisar_artigo()
        if nome == "detalhar_dimensao":
            return self._tool_detalhar_dimensao((argumentos or {}).get("dimensao", ""))
        return {"erro": f"Ferramenta desconhecida: {nome}"}

    # ------------------------------------------------------------- loop do LLM --
    def _chamar_ollama(self):
        body = {
            "model": self.modelo,
            "messages": self.mensagens,
            "tools": TOOLS,
            "stream": False,
        }
        try:
            data = _http_json(OLLAMA_HOST + "/api/chat", body=body)
        except Exception as e:
            # rede caiu, timeout, corpo não-JSON, modelo inexistente, etc.
            raise OllamaIndisponivel(
                f"Falha ao falar com o Ollama em {OLLAMA_HOST}: {e}. "
                f"Verifique se o Ollama está aberto e se o modelo '{self.modelo}' "
                f"foi baixado (ollama pull {self.modelo})."
            ) from e
        return data.get("message") or {}

    def conversar(self, mensagem_usuario):
        """Processa uma mensagem do usuário, usando ferramentas quando necessário.

        Levanta OllamaIndisponivel em qualquer falha de comunicação com o Ollama
        (a interface captura e degrada com uma mensagem clara).
        """
        self.mensagens.append({"role": "user", "content": mensagem_usuario})
        ferramentas_usadas = []

        for _ in range(_MAX_ITERACOES):
            msg = self._chamar_ollama()
            tool_calls = msg.get("tool_calls") or []

            # Registra a fala do assistente (com ou sem tool_calls) no histórico.
            self.mensagens.append(msg)

            if not tool_calls:
                resposta = (msg.get("content") or "").strip()
                if not resposta:
                    resposta = ("(O modelo não retornou texto. Tente reformular a "
                                "pergunta ou trocar o modelo do Ollama.)")
                return {"resposta": resposta, "ferramentas": ferramentas_usadas}

            # Executa cada ferramenta pedida e devolve o resultado ao modelo.
            for chamada in tool_calls:
                fn = chamada.get("function", {})
                nome = fn.get("name", "")
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                ferramentas_usadas.append(nome)
                resultado = self._executar_tool(nome, args)
                self.mensagens.append({
                    "role": "tool",
                    "tool_name": nome,
                    "content": json.dumps(resultado, ensure_ascii=False),
                })

        return {"resposta": "Não consegui concluir a resposta (limite de iterações "
                            "de ferramentas atingido).",
                "ferramentas": ferramentas_usadas}
