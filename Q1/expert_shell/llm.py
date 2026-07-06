"""
llm.py
======
Camada OPCIONAL de IA generativa: reescreve as explicações simbólicas
(Por quê? / Como?) produzidas pelo `Explicador` num texto em PT-BR mais natural,
usando um modelo de linguagem LOCAL via Ollama (https://ollama.com).

Princípio do enunciado (regra de ouro): o RACIOCÍNIO continua sendo feito pelo
motor baseado em regras. O LLM NÃO infere nada — ele apenas REFORMULA um texto
que já foi gerado pelo sistema especialista. Por isso esta camada vive nas bordas
de saída e não toca o motor.

Por que Ollama: roda 100% local, é gratuito, offline e não exige chave de API —
mantém o espírito "sem dependências externas" do projeto (a comunicação usa
apenas a biblioteca padrão; nenhum pacote pip é necessário para este recurso).

Degradação graciosa: se o Ollama não estiver rodando (ou EXPERT_SHELL_LLM=off),
`disponivel()` retorna False e a shell funciona exatamente como antes. Qualquer
erro durante a chamada cai no texto simbólico (fonte='fallback').

Configuração (variáveis de ambiente, todas opcionais):
  - EXPERT_SHELL_LLM=off   -> desativa o recurso de IA.
  - OLLAMA_MODEL           -> modelo a usar (padrão 'llama3.2').
  - OLLAMA_HOST            -> endpoint do Ollama (padrão 'http://localhost:11434').
"""

from __future__ import annotations

import json
import logging
import os
import threading
import urllib.request
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

OLLAMA_HOST_PADRAO = "http://localhost:11434"
OLLAMA_MODELO_PADRAO = "llama3.2"

_MAX_TOKENS = 1500
_TIMEOUT_S = 60.0          # teto da chamada de geração (modelo local pode ser lento)
_TIMEOUT_PING_S = 1.5      # teto da checagem "Ollama está rodando?"

_SYSTEM = (
    "Você reescreve explicações de um sistema especialista (baseado em regras) "
    "para um português brasileiro claro e natural, voltado ao usuário final.\n"
    "REGRAS ABSOLUTAS:\n"
    "1. NÃO adicione, infira nem invente qualquer raciocínio, regra, fato, valor "
    "ou conclusão. Use SOMENTE o que está no texto recebido.\n"
    "2. Preserve EXATAMENTE os identificadores de regra (ex.: R3, R7) e os pares "
    "'variável = valor' mencionados.\n"
    "3. Não acrescente recomendações médicas/técnicas próprias.\n"
    "4. Responda apenas com a explicação reescrita, sem Markdown, sem títulos, "
    "sem comentários sobre a tarefa.\n"
    "Seja fiel e conciso: o objetivo é só deixar o mesmo conteúdo mais legível."
)

_ROTULOS = {"por_que": "Por quê?", "como": "Como?"}

# Cache em memória: (tipo, texto_simbolico) -> texto natural já gerado.
_cache: Dict[Tuple[str, str], str] = {}

# Lock + disponibilidade do Ollama, checada uma vez por sessão do servidor.
# (Abra o Ollama ANTES de subir o run_web; reinicie o servidor se ligar depois.)
_lock = threading.Lock()
_ollama_ok: Optional[bool] = None


# --------------------------------------------------------------------------- #
# Configuração                                                                 #
# --------------------------------------------------------------------------- #
def _desligado() -> bool:
    return os.environ.get("EXPERT_SHELL_LLM", "").strip().lower() == "off"


def _ollama_host() -> str:
    return os.environ.get("OLLAMA_HOST", OLLAMA_HOST_PADRAO).rstrip("/")


def _ollama_modelo() -> str:
    return os.environ.get("OLLAMA_MODEL", OLLAMA_MODELO_PADRAO)


def _prompt(rotulo: str, texto: str) -> str:
    return f"Reescreva esta explicação do tipo '{rotulo}' de forma natural:\n\n{texto}"


# --------------------------------------------------------------------------- #
# Comunicação HTTP (só biblioteca padrão)                                      #
# --------------------------------------------------------------------------- #
def _http_json(url: str, body: Optional[dict] = None, timeout: float = _TIMEOUT_S) -> dict:
    """GET (body=None) ou POST de JSON usando só a biblioteca padrão."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data, method="POST" if data else "GET",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# --------------------------------------------------------------------------- #
# Disponibilidade                                                              #
# --------------------------------------------------------------------------- #
def _ollama_disponivel() -> bool:
    global _ollama_ok
    if _ollama_ok is None:
        with _lock:  # evita dois pings concorrentes (Flask roda threaded=True)
            if _ollama_ok is None:
                try:
                    _http_json(_ollama_host() + "/api/tags", timeout=_TIMEOUT_PING_S)
                    _ollama_ok = True
                except Exception:
                    _ollama_ok = False
    return _ollama_ok


def disponivel() -> bool:
    """True se a IA pode ser usada: não desligada e com Ollama rodando."""
    return (not _desligado()) and _ollama_disponivel()


def info() -> dict:
    """Resumo para o front (/api/llm)."""
    if disponivel():
        return {"disponivel": True, "provedor": "ollama", "modelo": _ollama_modelo()}
    return {"disponivel": False, "provedor": None, "modelo": None}


# --------------------------------------------------------------------------- #
# Chamada ao Ollama -> (texto_natural, truncado)                               #
# --------------------------------------------------------------------------- #
def _via_ollama(rotulo: str, texto: str) -> Tuple[str, bool]:
    body = {
        "model": _ollama_modelo(),
        "stream": False,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": _prompt(rotulo, texto)},
        ],
        # num_predict limita os tokens de saída (equivalente ao max_tokens).
        "options": {"num_predict": _MAX_TOKENS},
    }
    data = _http_json(_ollama_host() + "/api/chat", body=body, timeout=_TIMEOUT_S)
    truncado = data.get("done_reason") == "length"
    natural = (data.get("message") or {}).get("content", "").strip()
    return natural, truncado


# --------------------------------------------------------------------------- #
# API pública                                                                  #
# --------------------------------------------------------------------------- #
def naturalizar(tipo: str, texto_simbolico: str) -> dict:
    """Reescreve um texto de explicação. Retorna {'texto': str, 'fonte': str}.

    fonte = 'llm'      -> reescrito pela IA (Ollama);
    fonte = 'fallback' -> IA indisponível, truncada ou erro; devolve o original.

    tipo é o rótulo de contexto ('por_que' | 'como'), usado no cache e no prompt.
    """
    texto_simbolico = (texto_simbolico or "").strip()
    if not texto_simbolico:
        return {"texto": texto_simbolico, "fonte": "fallback"}

    chave = (tipo, texto_simbolico)
    if chave in _cache:
        return {"texto": _cache[chave], "fonte": "llm"}

    if not disponivel():
        return {"texto": texto_simbolico, "fonte": "fallback"}

    rotulo = _ROTULOS.get(tipo, "Como?")
    try:
        natural, truncado = _via_ollama(rotulo, texto_simbolico)
        if truncado:
            logger.warning("Explicação natural truncada (ollama); usando fallback.")
            return {"texto": texto_simbolico, "fonte": "fallback"}
        if not natural:
            return {"texto": texto_simbolico, "fonte": "fallback"}
        _cache[chave] = natural
        return {"texto": natural, "fonte": "llm"}
    except Exception as e:
        # Qualquer falha (rede, modelo inexistente, timeout, JSON inválido) cai no
        # texto simbólico. Logamos o motivo para o fallback não ficar indepurável.
        logger.warning("Falha ao naturalizar via ollama; usando fallback: %r", e)
        return {"texto": texto_simbolico, "fonte": "fallback"}
