"""
shell.py
========
A SHELL propriamente dita: implementa a arquitetura conceitual de um
AGENTE BASEADO EM CONHECIMENTO, integrando os componentes:

    Base de Conhecimento  +  Motor de Inferência  +  Mecanismo de Explicação
    +  Interface (via Provedores de Evidência)

O agente é genérico e REUTILIZÁVEL: ele não contém nenhuma regra do domínio.
Todo o conhecimento vem da BaseConhecimento carregada de um arquivo. Trocar de
domínio = trocar o arquivo da base, sem alterar uma linha do código da shell.

Os "Provedores de Evidência" desacoplam o motor da forma de coletar respostas:
  - ProvedorAutomatico : respostas pré-definidas (testes/demonstração);
  - ProvedorCLI        : pergunta interativamente no terminal e aceita 'por que?'.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from .knowledge_base import BaseConhecimento
from .inference_engine import MotorInferencia, LIMIAR_CF
from .explanation import Explicador


# --------------------------------------------------------------------------- #
# Provedores de evidência                                                      #
# --------------------------------------------------------------------------- #
class ProvedorEvidencias:
    """Interface: dado o nome de uma variável, devolve (valor, cf)."""
    def obter(self, variavel: str, motor: MotorInferencia) -> Tuple[Optional[str], float]:
        raise NotImplementedError


class ProvedorAutomatico(ProvedorEvidencias):
    """Usa um dicionário de respostas. Útil para testes e demonstração.
    respostas: { 'febre': 'alta', 'tosse': 'sim', ... }  (valor None ou ausente = 'não sei')
    cfs (opcional): { 'febre': 90, ... } confiança da resposta (default 100)."""
    def __init__(self, respostas: Dict[str, Optional[str]], cfs: Optional[Dict[str, float]] = None):
        self.respostas = respostas
        self.cfs = cfs or {}

    def obter(self, variavel, motor):
        if variavel not in self.respostas:
            return None, 0.0
        val = self.respostas[variavel]
        if val is None:
            return None, 0.0
        return val, float(self.cfs.get(variavel, 100.0))


class ProvedorCLI(ProvedorEvidencias):
    """Pergunta ao usuário no terminal. Aceita:
        - um dos valores válidos da variável;
        - 'nao sei' / 'ns'           -> evidência desconhecida;
        - 'por que' / 'porque' / '?' -> dispara explicação e repete a pergunta."""
    def __init__(self, kb: BaseConhecimento):
        self.kb = kb
        self._explicador: Optional[Explicador] = None

    def vincular_explicador(self, exp: Explicador):
        self._explicador = exp

    def obter(self, variavel, motor):
        var = self.kb.variaveis.get(variavel)
        pergunta = var.texto_pergunta() if var else f"Valor de {variavel}?"
        valores = var.valores if var else []
        while True:
            opcoes = f" [{', '.join(valores)}]" if valores else ""
            try:
                resp = input(f"\n>> {pergunta}{opcoes}\n   (ou 'por que?' / 'nao sei'): ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return None, 0.0
            low = resp.lower()
            if low in ("por que", "por que?", "porque", "porque?", "?"):
                if self._explicador:
                    print("\n   [POR QUÊ?]")
                    for ln in self._explicador.por_que(variavel).splitlines():
                        print("   " + ln)
                continue
            if low in ("nao sei", "não sei", "ns", "nao", "n/a") and ("nao" not in valores):
                return None, 0.0
            if not valores or resp in valores:
                return resp, 100.0
            # tenta correspondência case-insensitive
            for v in valores:
                if v.lower() == low:
                    return v, 100.0
            print(f"   Valor inválido. Opções: {', '.join(valores)}")


# --------------------------------------------------------------------------- #
# Agente baseado em conhecimento                                               #
# --------------------------------------------------------------------------- #
class AgenteEspecialista:
    """Orquestra uma consulta de diagnóstico/recomendação sobre uma base."""

    def __init__(self, kb: BaseConhecimento, provedor: ProvedorEvidencias):
        self.kb = kb
        self.motor = MotorInferencia(kb, provedor)
        self.explicador = Explicador(self.motor)
        if isinstance(provedor, ProvedorCLI):
            provedor.vincular_explicador(self.explicador)

    # --- execução da consulta nos três modos --- #
    def consultar(self, modo: str = "backward",
                  objetivos: Optional[List[str]] = None,
                  limiar_parada: Optional[float] = 85.0) -> Dict[str, List[Tuple[str, float]]]:
        objetivos = objetivos or self.kb.objetivos or ["diagnostico"]
        modo = modo.lower()

        if modo == "forward":
            self.motor.forward_chaining(perguntar_evidencias=True)
        elif modo == "backward":
            for obj in objetivos:
                self.motor.backward_chaining(obj, limiar_parada=limiar_parada)
        elif modo in ("hibrido", "híbrido", "hybrid", "misto"):
            self.motor.hibrido(objetivos, limiar_parada=limiar_parada)
        else:
            raise ValueError(f"Modo de inferência desconhecido: {modo}")

        return {obj: self.motor.ranking(obj) for obj in objetivos}

    # --- explicações --- #
    def como(self, variavel: str, valor: str) -> str:
        return self.explicador.como(variavel, valor)

    def por_que(self, variavel: str) -> str:
        return self.explicador.por_que(variavel)

    def regras_disparadas(self) -> List[str]:
        return self.explicador.regras_disparadas()
