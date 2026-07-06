"""
kb_editor.py
============
EDITOR DA BASE DE CONHECIMENTO. Camada de alto nível para o especialista
criar/editar a base usando o formato textual de regras, sem mexer no código.

Encapsula:
  - cadastro/alteração/remoção de regras (a partir de texto SE...ENTAO);
  - cadastro de variáveis perguntáveis (com texto da pergunta e valores);
  - definição de objetivos;
  - persistência (salvar/carregar), delegada à BaseConhecimento.
"""

from __future__ import annotations
from typing import List, Optional
from .knowledge_base import BaseConhecimento, Variavel, Regra
from .parser import parse_regra, regra_para_texto


class EditorBase:
    def __init__(self, kb: Optional[BaseConhecimento] = None):
        self.kb = kb or BaseConhecimento()

    # ---------------- variáveis (fatos possíveis) ---------------- #
    def definir_variavel(self, nome: str, pergunta: str = "",
                         valores: Optional[List[str]] = None,
                         perguntavel: bool = True) -> None:
        self.kb.add_variavel(Variavel(nome=nome, pergunta=pergunta,
                                      valores=valores or [], perguntavel=perguntavel))

    def remover_variavel(self, nome: str) -> bool:
        return self.kb.remover_variavel(nome)

    # ---------------- regras ---------------- #
    def adicionar_regra_texto(self, texto: str, rid: Optional[str] = None) -> Regra:
        rid = rid or self.kb.proximo_id_regra()
        regra = parse_regra(texto, rid)
        self.kb.add_regra(regra)
        return regra

    def alterar_regra_texto(self, rid: str, texto: str) -> Regra:
        regra = parse_regra(texto, rid)
        self.kb.alterar_regra(regra)
        return regra

    def remover_regra(self, rid: str) -> bool:
        return self.kb.remover_regra(rid)

    def listar_regras(self) -> List[str]:
        return [regra_para_texto(r) for r in self.kb.regras.values()]

    # ---------------- objetivos ---------------- #
    def definir_objetivos(self, objetivos: List[str]) -> None:
        self.kb.objetivos = list(objetivos)

    # ---------------- persistência ---------------- #
    def salvar(self, caminho: str) -> None:
        self.kb.salvar(caminho)

    def carregar(self, caminho: str) -> None:
        self.kb = BaseConhecimento.carregar(caminho)
