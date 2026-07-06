"""
explanation.py
==============
MECANISMO DE EXPLICAÇÃO, no estilo dos sistemas especialistas clássicos.

Responde a duas perguntas:

  POR QUÊ?  -> Justifica por que uma pergunta está sendo feita ao usuário,
              olhando a pilha de objetivos (goal stack) do motor: revela qual
              hipótese está sob avaliação e qual regra precisa daquela informação.

  COMO?     -> Explica como uma conclusão foi obtida, percorrendo a árvore de
              justificativas (que regras dispararam e a partir de quais fatos),
              de forma recursiva até as evidências fornecidas pelo usuário.
"""

from __future__ import annotations
from typing import List
from .inference_engine import MotorInferencia, Justificativa


class Explicador:
    def __init__(self, motor: MotorInferencia):
        self.motor = motor

    # ------------------------------------------------------------------ #
    # POR QUÊ?  (durante uma pergunta)                                    #
    # ------------------------------------------------------------------ #
    def por_que(self, variavel: str) -> str:
        """Explica por que a 'variavel' está sendo perguntada agora."""
        pilha = self.motor.pilha
        if not pilha:
            return (f"Estou perguntando sobre '{variavel}' porque é uma evidência "
                    f"inicial necessária para iniciar o raciocínio.")
        topo = pilha[-1]
        obj_var, obj_val = topo.objetivo
        cond_var, cond_val = topo.condicao_atual
        linhas = [
            f"Porque estou avaliando a hipótese '{obj_var} = {obj_val}'.",
            f"A regra {topo.regra_id} exige a condição '{cond_var} = {cond_val}', "
            f"e preciso conhecer '{variavel}' para verificá-la.",
        ]
        # cadeia de objetivos encadeados (mostra o porquê do porquê)
        if len(pilha) > 1:
            cadeia = " <- ".join(
                f"{it.objetivo[0]}={it.objetivo[1]} (regra {it.regra_id})"
                for it in reversed(pilha)
            )
            linhas.append(f"Cadeia de objetivos: {cadeia}.")
        return "\n".join(linhas)

    # ------------------------------------------------------------------ #
    # COMO?  (após uma conclusão)                                         #
    # ------------------------------------------------------------------ #
    def como(self, variavel: str, valor: str) -> str:
        """Explica como se chegou a 'variavel = valor', recursivamente."""
        par = (variavel, valor)
        if par not in self.motor.fatos:
            return f"Não há conclusão registrada para '{variavel} = {valor}'."
        linhas: List[str] = []
        self._explicar_par(par, nivel=0, linhas=linhas, visitados=set())
        return "\n".join(linhas)

    def _explicar_par(self, par, nivel, linhas, visitados):
        var, val = par
        ind = "   " * nivel
        cf = self.motor.fatos.get(par, 0.0)

        if par in visitados:
            linhas.append(f"{ind}- {var} = {val} (já explicado acima)")
            return
        visitados.add(par)

        justs = self.motor.justificativas.get(par, [])
        if not justs:
            # sem justificativa por regra => veio do usuário (evidência)
            linhas.append(f"{ind}- '{var} = {val}' foi informado por você "
                          f"(evidência, CF={cf:.0f}).")
            return

        for j in justs:
            linhas.append(
                f"{ind}- '{var} = {val}' (CF={cf:.0f}) foi concluído pela regra "
                f"{j.regra_id} (CF da regra={j.cf_regra:g}), porque:"
            )
            for (cv, cval, ccf) in j.condicoes:
                linhas.append(f"{ind}   • '{cv} = {cval}' valia (CF={ccf:.0f})")
            # aprofunda nas condições que também foram inferidas
            for (cv, cval, _ccf) in j.condicoes:
                if (cv, cval) in self.motor.justificativas:
                    self._explicar_par((cv, cval), nivel + 1, linhas, visitados)

    # ------------------------------------------------------------------ #
    # Resumo geral do raciocínio                                          #
    # ------------------------------------------------------------------ #
    def regras_disparadas(self) -> List[str]:
        ids = []
        for justs in self.motor.justificativas.values():
            for j in justs:
                if j.regra_id not in ids:
                    ids.append(j.regra_id)
        return ids
