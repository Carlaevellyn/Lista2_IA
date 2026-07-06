"""
server.py
=========
Interface WEB (Flask) da shell de sistema baseado em conhecimento.

É apenas uma nova CAMADA DE APRESENTAÇÃO: reaproveita o mesmo agente, motor e
mecanismo de explicação da CLI. O motor permanece intocado graças ao padrão
"Provedor de Evidências" — aqui implementamos um `ProvedorWeb`.

Desafio resolvido: o motor pergunta de forma SÍNCRONA e bloqueante (o backward
só pergunta o necessário). Para casar isso com o modelo requisição/resposta do
HTTP, cada consulta roda numa THREAD de trabalho; o `ProvedorWeb` publica a
pergunta numa fila e bloqueia esperando a resposta, que chega pelos endpoints.
Enquanto a thread está parada na pergunta, o motor está ocioso — então o
endpoint "Por quê?" pode ler a pilha de objetivos com segurança.
"""

from __future__ import annotations

import os
import queue
import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, render_template

from ..knowledge_base import BaseConhecimento
from ..parser import regra_para_texto
from ..shell import AgenteEspecialista, ProvedorEvidencias
from ..inference_engine import MotorInferencia
from .. import llm


# --------------------------------------------------------------------------- #
# Caminhos do projeto                                                          #
# --------------------------------------------------------------------------- #
WEB_DIR = os.path.dirname(os.path.abspath(__file__))          # .../expert_shell/web
PKG_DIR = os.path.dirname(WEB_DIR)                            # .../expert_shell (pacote)
PROJ_ROOT = os.path.dirname(PKG_DIR)                         # raiz do projeto
BASES_DIR = os.path.join(PROJ_ROOT, "bases")

# Sentinela usado na fila para representar a resposta "não sei".
_NAO_SEI = object()

# Ciclo de vida das sessões de consulta.
TIMEOUT_RESPOSTA = 600.0   # s: se o usuário não responder, a worker desiste (evita thread eterna)
TTL_TERMINADA = 1800.0     # s: por quanto tempo manter uma sessão já concluída (p/ "Como?")
MAX_SESSOES = 50           # teto absoluto de sessões retidas em memória


class ConsultaAbandonada(Exception):
    """Levantada quando o usuário não responde dentro de TIMEOUT_RESPOSTA."""


# --------------------------------------------------------------------------- #
# Provedor de evidências para a web                                            #
# --------------------------------------------------------------------------- #
class ProvedorWeb(ProvedorEvidencias):
    """Coleta respostas via HTTP. Quando o motor pede uma evidência, publica a
    pergunta na fila `saida` e BLOQUEIA em `entrada` até o usuário responder."""

    def __init__(self, kb: BaseConhecimento,
                 saida: "queue.Queue", entrada: "queue.Queue"):
        self.kb = kb
        self.saida = saida
        self.entrada = entrada
        self.variavel_atual: Optional[str] = None

    def obter(self, variavel: str, motor: MotorInferencia) -> Tuple[Optional[str], float]:
        var = self.kb.variaveis.get(variavel)
        self.variavel_atual = variavel
        self.saida.put({
            "tipo": "pergunta",
            "variavel": variavel,
            "pergunta": var.texto_pergunta() if var else f"Qual o valor de '{variavel}'?",
            "valores": list(var.valores) if var else [],
        })
        try:
            resposta = self.entrada.get(timeout=TIMEOUT_RESPOSTA)  # bloqueia até /api/responder
        except queue.Empty:
            # usuário abandonou a consulta -> encerra a worker em vez de bloquear para sempre
            raise ConsultaAbandonada("Tempo de resposta esgotado; consulta encerrada.")
        self.variavel_atual = None
        if resposta is _NAO_SEI or resposta is None:
            return None, 0.0
        return resposta, 100.0


# --------------------------------------------------------------------------- #
# Sessão de consulta (uma thread de trabalho por consulta)                     #
# --------------------------------------------------------------------------- #
class SessaoConsulta:
    def __init__(self, kb: BaseConhecimento, modo: str):
        self.kb = kb
        self.modo = modo
        self.saida: "queue.Queue" = queue.Queue()    # worker -> HTTP
        self.entrada: "queue.Queue" = queue.Queue()  # HTTP   -> worker
        self.provedor = ProvedorWeb(kb, self.saida, self.entrada)
        self.agente = AgenteEspecialista(kb, self.provedor)
        self.terminada = False
        self.criada_em = time.monotonic()
        self._thread = threading.Thread(target=self._executar, daemon=True)

    def iniciar(self) -> dict:
        self._thread.start()
        return self._proximo_evento()

    def responder(self, valor: Optional[str]) -> dict:
        if self.terminada:
            return {"tipo": "erro", "msg": "Consulta já encerrada."}
        self.entrada.put(_NAO_SEI if valor is None else valor)
        return self._proximo_evento()

    def _proximo_evento(self) -> dict:
        evento = self.saida.get()
        if evento.get("tipo") in ("resultado", "erro"):
            self.terminada = True
        return evento

    def por_que(self) -> str:
        var = self.provedor.variavel_atual
        if not var:
            return "Não há pergunta em aberto no momento."
        return self.agente.por_que(var)

    def como(self, variavel: str, valor: str) -> str:
        return self.agente.como(variavel, valor)

    def _executar(self) -> None:
        try:
            resultados = self.agente.consultar(modo=self.modo)
            self.saida.put({
                "tipo": "resultado",
                "objetivos": self._serializar(resultados),
                "regras_disparadas": self.agente.regras_disparadas(),
            })
        except ConsultaAbandonada as e:  # usuário sumiu: worker encerra silenciosamente
            self.saida.put({"tipo": "erro", "msg": str(e)})
        except Exception as e:  # erro inesperado vira evento, não derruba a thread
            self.saida.put({"tipo": "erro", "msg": str(e)})
        finally:
            # marca como concluída assim que a worker termina (mesmo se o cliente
            # nunca consumir o evento final) -> permite que o TTL recicle a sessão.
            self.terminada = True

    @staticmethod
    def _serializar(resultados: Dict[str, List[Tuple[str, float]]]) -> List[dict]:
        saida = []
        for objetivo, ranking in resultados.items():
            saida.append({
                "objetivo": objetivo,
                "conclusoes": [{"valor": val, "cf": round(cf, 1)} for val, cf in ranking],
            })
        return saida


# --------------------------------------------------------------------------- #
# Aplicação Flask                                                              #
# --------------------------------------------------------------------------- #
app = Flask(__name__)

# Estado do servidor (app local de usuário único; um lock protege as escritas).
# _estado["kb"] já nasce com uma base vazia, então _kb_atual() nunca escreve —
# elimina a corrida de leitura/escrita apontada na revisão.
_lock = threading.Lock()
_estado: Dict[str, object] = {"kb": BaseConhecimento(), "arquivo": None}
_sessoes: Dict[str, SessaoConsulta] = {}


def _kb_atual() -> BaseConhecimento:
    return _estado["kb"]  # type: ignore[return-value]


def _limpar_sessoes() -> None:
    """Descarta sessões concluídas há mais de TTL_TERMINADA e impõe um teto.
    Chamado sob _lock. Threads daemon de sessões abandonadas encerram sozinhas
    pelo TIMEOUT_RESPOSTA do provedor."""
    agora = time.monotonic()
    mortas = [sid for sid, s in _sessoes.items()
              if s.terminada and (agora - s.criada_em) > TTL_TERMINADA]
    for sid in mortas:
        _sessoes.pop(sid, None)
    if len(_sessoes) > MAX_SESSOES:
        antigas = sorted(_sessoes.items(), key=lambda kv: kv[1].criada_em)
        for sid, _ in antigas[: len(_sessoes) - MAX_SESSOES]:
            _sessoes.pop(sid, None)


def carregar_base_inicial(caminho: Optional[str]) -> None:
    """Chamado pelo launcher para abrir uma base ao subir o servidor."""
    if caminho and os.path.exists(caminho):
        _estado["kb"] = BaseConhecimento.carregar(caminho)
        _estado["arquivo"] = os.path.basename(caminho)


def _bases_disponiveis() -> List[str]:
    if not os.path.isdir(BASES_DIR):
        return []
    return sorted(f for f in os.listdir(BASES_DIR) if f.endswith(".json"))


# ---------------------------- Rotas ---------------------------------------- #
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/base")
def api_base():
    """Estado da base atual: domínio, objetivos, regras (leitura) e bases disponíveis."""
    kb = _kb_atual()
    regras = [{"id": r.id, "texto": regra_para_texto(r)} for r in kb.regras.values()]
    variaveis = [
        {
            "nome": v.nome,
            "tipo": "perguntável" if v.perguntavel else "inferida",
            "valores": v.valores,
        }
        for v in kb.variaveis.values()
    ]
    return jsonify({
        "dominio": kb.dominio,
        "arquivo": _estado.get("arquivo"),
        "objetivos": kb.objetivos,
        "n_regras": len(kb.regras),
        "regras": regras,
        "variaveis": variaveis,
        "bases_disponiveis": _bases_disponiveis(),
    })


@app.post("/api/carregar")
def api_carregar():
    """Carrega uma base do diretório bases/ (apenas pelo nome do arquivo)."""
    arquivo = (request.json or {}).get("arquivo", "")
    nome = os.path.basename(arquivo)  # impede travessia de diretório
    if not nome.endswith(".json"):
        return jsonify({"erro": "Arquivo inválido."}), 400
    caminho = os.path.join(BASES_DIR, nome)
    if not os.path.exists(caminho):
        return jsonify({"erro": f"Base '{nome}' não encontrada."}), 404
    try:
        with _lock:
            _estado["kb"] = BaseConhecimento.carregar(caminho)
            _estado["arquivo"] = nome
    except Exception as e:
        return jsonify({"erro": f"Falha ao carregar: {e}"}), 400
    return api_base()


@app.post("/api/consulta")
def api_consulta():
    """Inicia uma consulta no modo escolhido. Retorna a 1ª pergunta ou o resultado."""
    modo = (request.json or {}).get("modo", "backward")
    with _lock:
        kb = _kb_atual()
        if not kb.regras:
            return jsonify({"erro": "Base vazia: carregue uma base antes de consultar."}), 400
        _limpar_sessoes()
        sid = uuid.uuid4().hex
        sessao = SessaoConsulta(kb, modo)
        _sessoes[sid] = sessao
    # iniciar() roda a 1ª inferência (pode bloquear na 1ª pergunta) -> FORA do lock
    evento = sessao.iniciar()
    return jsonify({"sid": sid, **evento})


@app.post("/api/responder")
def api_responder():
    """Envia a resposta da pergunta atual. valor=null significa 'não sei'."""
    dados = request.json or {}
    sid = dados.get("sid", "")
    sessao = _sessoes.get(sid)
    if not sessao:
        return jsonify({"erro": "Sessão não encontrada ou expirada."}), 404
    evento = sessao.responder(dados.get("valor"))
    if evento.get("tipo") in ("resultado", "erro"):
        pass  # mantém a sessão viva para permitir 'como?' depois do resultado
    return jsonify({"sid": sid, **evento})


def _talvez_naturalizar(tipo: str, texto: str) -> dict:
    """Anexa a versão natural (IA) quando ?natural=1 é pedido. Sempre devolve o
    texto simbólico em 'texto' (fonte da verdade); a versão IA vem em 'texto_natural'."""
    saida = {"texto": texto}
    if request.args.get("natural") in ("1", "true", "sim"):
        r = llm.naturalizar(tipo, texto)
        saida["texto_natural"] = r["texto"]
        saida["fonte"] = r["fonte"]
    return saida


@app.get("/api/llm")
def api_llm():
    """Informa ao front se a camada de IA está disponível e qual provedor."""
    return jsonify(llm.info())


@app.get("/api/porque")
def api_porque():
    sessao = _sessoes.get(request.args.get("sid", ""))
    if not sessao:
        return jsonify({"erro": "Sessão não encontrada."}), 404
    return jsonify(_talvez_naturalizar("por_que", sessao.por_que()))


@app.get("/api/como")
def api_como():
    sessao = _sessoes.get(request.args.get("sid", ""))
    if not sessao:
        return jsonify({"erro": "Sessão não encontrada."}), 404
    var = request.args.get("var", "")
    val = request.args.get("val", "")
    return jsonify(_talvez_naturalizar("como", sessao.como(var, val)))


def criar_app(caminho_base: Optional[str] = None) -> Flask:
    carregar_base_inicial(caminho_base)
    return app
