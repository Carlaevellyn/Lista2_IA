"""
inference_engine.py
===================
MOTOR DE INFERÊNCIA da shell. Implementa os três modos exigidos:

  - Forward Chaining  (encadeamento para frente / dirigido pelos dados)
  - Backward Chaining (encadeamento para trás   / dirigido pelos objetivos)
  - Hybrid            (misto: forward para consolidar evidências + backward
                       para fechar os objetivos)

Recursos adicionais:
  - Fatores de confiança (CF) estilo MYCIN/Expert SINTA, para lidar com incerteza.
  - Registro de JUSTIFICATIVAS: para cada fato inferido guarda-se qual regra o
    produziu e de quais fatos ela dependeu -> base do mecanismo de explicação.
  - Pilha de objetivos (goal stack): durante o backward, sabe-se exatamente por
    que cada pergunta está sendo feita -> base da explicação "Por quê?".

A obtenção de evidências (perguntas ao usuário) é delegada a um objeto
`provedor_evidencias` com o método obter(variavel) -> (valor|None, cf).
Isso desacopla o motor da interface (CLI, web, LLM, testes automáticos...).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Callable

from .knowledge_base import BaseConhecimento, Regra, ParVV

# Limiar mínimo de confiança para uma condição/regra ser considerada ativa.
LIMIAR_CF = 20.0


# --------------------------------------------------------------------------- #
# Combinação de fatores de confiança (modelo MYCIN), valores em [-100, 100]    #
# --------------------------------------------------------------------------- #
def combinar_cf(c1: float, c2: float) -> float:
    x, y = c1 / 100.0, c2 / 100.0
    if x >= 0 and y >= 0:
        z = x + y * (1 - x)
    elif x <= 0 and y <= 0:
        z = x + y * (1 + x)
    else:
        z = (x + y) / (1 - min(abs(x), abs(y)))
    return max(-100.0, min(100.0, z * 100.0))


# --------------------------------------------------------------------------- #
# Estruturas auxiliares                                                        #
# --------------------------------------------------------------------------- #
@dataclass
class Justificativa:
    """Registra como um fato (var=val) foi obtido por uma regra específica."""
    regra_id: str
    condicoes: List[Tuple[str, str, float]]  # (var, val, cf de cada condição)
    cf_antecedente: float
    cf_regra: float
    cf_resultado: float


@dataclass
class ItemPilha:
    """Um nível da pilha de objetivos, para a explicação 'Por quê?'."""
    regra_id: str
    objetivo: ParVV          # conclusão que a regra tenta estabelecer
    condicao_atual: ParVV    # condição sendo verificada no momento


class MotorInferencia:
    def __init__(self, kb: BaseConhecimento, provedor_evidencias):
        self.kb = kb
        self.provedor = provedor_evidencias  # objeto com .obter(variavel)->(valor,cf)

        # Memória de trabalho: (var, val) -> cf acumulado (apenas crenças positivas)
        self.fatos: Dict[ParVV, float] = {}
        # Origem de cada fato perguntado/inferido: "usuario" ou Justificativa(s)
        self.justificativas: Dict[ParVV, List[Justificativa]] = {}
        self.fatos_perguntados: Dict[str, float] = {}  # var -> cf da resposta do usuário
        # variáveis já totalmente processadas (perguntadas ou inferidas)
        self.avaliadas: set[str] = set()
        # pilha de objetivos corrente (backward)
        self.pilha: List[ItemPilha] = []
        # trilha cronológica de eventos (para depuração/relatório)
        self.trilha: List[str] = []
        # limiar de PARADA ANTECIPADA do backward: ao alcançar este CF para um
        # objetivo, o motor deixa de avaliar (e de perguntar) as regras restantes
        # daquele objetivo. None = avaliação exaustiva (gera ranking completo).
        self._limiar_parada: Optional[float] = None

    # ------------------------------------------------------------------ #
    # Acesso a fatos                                                      #
    # ------------------------------------------------------------------ #
    def cf_de(self, var: str, val: str) -> float:
        return self.fatos.get((var, val), 0.0)

    def _afirmar(self, par: ParVV, cf: float, just: Optional[Justificativa]) -> bool:
        """Adiciona/atualiza um fato combinando o CF. Retorna True se houve mudança."""
        antigo = self.fatos.get(par, None)
        novo = cf if antigo is None else combinar_cf(antigo, cf)
        mudou = (antigo is None) or (abs(novo - antigo) > 0.01)
        self.fatos[par] = novo
        if just is not None:
            self.justificativas.setdefault(par, []).append(just)
        if mudou:
            self.trilha.append(f"fato: {par[0]} = {par[1]} (CF={novo:.0f})")
        return mudou

    # ------------------------------------------------------------------ #
    # Obtenção de evidência (pergunta ao usuário)                         #
    # ------------------------------------------------------------------ #
    def _perguntar(self, var: str) -> None:
        """Solicita o valor de uma variável perguntável ao provedor de evidências."""
        if var in self.avaliadas:
            return
        valor, cf = self.provedor.obter(var, self)  # pode usar self.pilha p/ 'por quê'
        self.avaliadas.add(var)
        if valor is None:
            self.trilha.append(f"pergunta: {var} -> (não sei)")
            return
        self.fatos_perguntados[var] = cf
        self._afirmar((var, valor), cf, None)
        self.trilha.append(f"pergunta: {var} -> {valor} (CF={cf:.0f})")

    # ================================================================== #
    # FORWARD CHAINING                                                    #
    # ================================================================== #
    def forward_chaining(self, perguntar_evidencias: bool = True) -> None:
        """Dirigido pelos dados: coleta evidências e dispara todas as regras
        cujas condições estejam satisfeitas, até não haver mais mudanças."""
        self.trilha.append("=== FORWARD CHAINING ===")
        if perguntar_evidencias:
            # Pergunta todas as variáveis perguntáveis citadas em condições de regras.
            usadas = {v for r in self.kb.regras.values() for v in r.variaveis_condicao()}
            for var in usadas:
                if self.kb.is_perguntavel(var):
                    self._perguntar(var)

        mudou = True
        while mudou:
            mudou = False
            for regra in self.kb.regras.values():
                if self._tentar_disparar(regra):
                    mudou = True

    def _tentar_disparar(self, regra: Regra) -> bool:
        """No forward: dispara a regra se TODAS as condições já estão satisfeitas."""
        cfs = []
        for (v, val) in regra.condicoes:
            cf = self.cf_de(v, val)
            if cf <= LIMIAR_CF:
                return False
            cfs.append(cf)
        cf_ant = min(cfs)
        cf_res = cf_ant * regra.cf / 100.0
        if cf_res <= LIMIAR_CF:
            return False
        just = Justificativa(
            regra_id=regra.id,
            condicoes=[(v, val, self.cf_de(v, val)) for (v, val) in regra.condicoes],
            cf_antecedente=cf_ant,
            cf_regra=regra.cf,
            cf_resultado=cf_res,
        )
        # evita recombinar a mesma regra repetidamente
        ja = any(j.regra_id == regra.id for j in self.justificativas.get(regra.conclusao, []))
        if ja:
            return False
        self.trilha.append(f"dispara {regra.id} -> {regra.conclusao[0]} = {regra.conclusao[1]}")
        return self._afirmar(regra.conclusao, cf_res, just)

    # ================================================================== #
    # BACKWARD CHAINING                                                   #
    # ================================================================== #
    def backward_chaining(self, objetivo: str, limiar_parada: Optional[float] = 85.0) -> Dict[str, float]:
        """Dirigido pelo objetivo: tenta estabelecer os valores da variável-alvo,
        perguntando ao usuário apenas o que for necessário.

        limiar_parada: ao alcançar este CF para o objetivo, o motor PARA de avaliar
        (e de perguntar) as regras restantes — economia de perguntas típica de shells
        de diagnóstico. Use None para avaliação exaustiva (ranking completo)."""
        self.trilha.append(f"=== BACKWARD CHAINING (objetivo: {objetivo}) ===")
        self._limiar_parada = limiar_parada
        self._resolver(objetivo)
        return {val: cf for (v, val), cf in self.fatos.items() if v == objetivo}

    def _resolver(self, var: str) -> None:
        """Garante que a variável 'var' seja avaliada (perguntada ou inferida)."""
        if var in self.avaliadas:
            return

        if self.kb.is_perguntavel(var):
            self._perguntar(var)
            return

        # variável inferível: aplica as regras que a concluem (na ordem da base)
        self.avaliadas.add(var)  # marca cedo para evitar recursão infinita
        for regra in self.kb.regras_que_concluem(var):
            self._avaliar_regra_backward(regra)
            # PARADA ANTECIPADA: se já há um valor suficientemente confiável para
            # este objetivo, não vale a pena avaliar (nem perguntar) o restante.
            if self._limiar_parada is not None:
                melhor = max((cf for (vv, _val), cf in self.fatos.items() if vv == var),
                             default=0.0)
                if melhor >= self._limiar_parada:
                    self.trilha.append(
                        f"parada antecipada em '{var}' (CF={melhor:.0f} >= {self._limiar_parada:.0f})")
                    break

    def _avaliar_regra_backward(self, regra: Regra) -> None:
        """Tenta provar o antecedente de uma regra; se conseguir, afirma a conclusão.
        Avalia as condições da esquerda para a direita e PODA na primeira que falha
        (não pergunta condições subsequentes de uma regra já descartada)."""
        cfs = []
        for (v, val) in regra.condicoes:
            self.pilha.append(ItemPilha(regra.id, regra.conclusao, (v, val)))
            self._resolver(v)              # obtém o valor da variável da condição
            self.pilha.pop()
            cf = self.cf_de(v, val)
            if cf <= LIMIAR_CF:
                return                     # condição falhou -> poda o resto da regra
            cfs.append(cf)

        cf_ant = min(cfs)
        cf_res = cf_ant * regra.cf / 100.0
        if cf_res <= LIMIAR_CF:
            return
        just = Justificativa(
            regra_id=regra.id,
            condicoes=[(v, val, self.cf_de(v, val)) for (v, val) in regra.condicoes],
            cf_antecedente=cf_ant,
            cf_regra=regra.cf,
            cf_resultado=cf_res,
        )
        self.trilha.append(f"dispara {regra.id} -> {regra.conclusao[0]} = {regra.conclusao[1]}")
        self._afirmar(regra.conclusao, cf_res, just)

    # ================================================================== #
    # HÍBRIDO (MISTO)                                                     #
    # ================================================================== #
    def hibrido(self, objetivos: List[str],
                limiar_parada: Optional[float] = 85.0) -> Dict[str, Dict[str, float]]:
        """Estratégia mista:
        1) FORWARD a partir das evidências já conhecidas (sem novas perguntas),
           consolidando tudo o que for dedutível dos fatos disponíveis;
        2) BACKWARD sobre cada objetivo, perguntando só o que ainda faltar.
        O passo 1 reaproveita conhecimento; o passo 2 garante foco no objetivo."""
        self.trilha.append("=== HÍBRIDO (forward de consolidação + backward dirigido) ===")
        # Passo 1: forward apenas com o que já se sabe (não faz perguntas).
        self.forward_chaining(perguntar_evidencias=False)
        # Passo 2: backward para fechar os objetivos.
        resultado: Dict[str, Dict[str, float]] = {}
        for obj in objetivos:
            self.backward_chaining(obj, limiar_parada=limiar_parada)
            resultado[obj] = {val: cf for (v, val), cf in self.fatos.items() if v == obj}
        return resultado

    # ------------------------------------------------------------------ #
    # Consulta de resultados                                              #
    # ------------------------------------------------------------------ #
    def ranking(self, variavel: str) -> List[Tuple[str, float]]:
        """Valores inferidos para uma variável, ordenados por confiança decrescente."""
        itens = [(val, cf) for (v, val), cf in self.fatos.items()
                 if v == variavel and cf > LIMIAR_CF]
        return sorted(itens, key=lambda t: t[1], reverse=True)
