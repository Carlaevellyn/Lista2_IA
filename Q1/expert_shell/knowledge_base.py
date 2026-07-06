"""
knowledge_base.py
=================
Módulo de REPRESENTAÇÃO DO CONHECIMENTO da shell.

Define as estruturas de dados que compõem a Base de Conhecimento:
  - Variavel : um atributo do domínio (perguntável ou inferível) e seus valores.
  - Regra    : uma regra de produção no formato SE ... E ... ENTAO ...
  - BaseConhecimento : agrega variáveis, regras e objetivos, e cuida da
                       persistência (carregar/salvar em JSON).

O conhecimento é declarativo: o especialista define tudo isto sem tocar no
código da shell. Por isso a base é totalmente serializável em JSON.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from typing import List, Tuple, Dict, Optional


# Uma condição/conclusão é sempre um par (variavel, valor). Ex.: ("febre", "alta")
ParVV = Tuple[str, str]


@dataclass
class Variavel:
    """Descreve um atributo do domínio.

    nome        : identificador da variável (ex.: "febre").
    pergunta    : texto exibido ao usuário quando a variável precisa ser obtida.
    valores     : lista de valores possíveis (ex.: ["alta", "baixa", "ausente"]).
    perguntavel : True  -> o valor é obtido perguntando ao usuário (evidência);
                  False -> o valor é deduzido por regras (variável inferida).
    """
    nome: str
    pergunta: str = ""
    valores: List[str] = field(default_factory=list)
    perguntavel: bool = True

    def texto_pergunta(self) -> str:
        return self.pergunta or f"Qual o valor de '{self.nome}'?"


@dataclass
class Regra:
    """Regra de produção: SE <condicoes> ENTAO <conclusao> (com fator de confiança).

    id         : identificador único (ex.: "R3").
    condicoes  : lista de pares (variavel, valor) ligados por E (conjunção).
    conclusao  : par (variavel, valor) afirmado quando todas as condições valem.
    cf         : fator de confiança da regra, no intervalo [-100, 100]
                 (100 = regra totalmente confiável; valores menores modelam incerteza).
    """
    id: str
    condicoes: List[ParVV]
    conclusao: ParVV
    cf: float = 100.0

    # ------- utilidades de leitura -------
    @property
    def variavel_conclusao(self) -> str:
        return self.conclusao[0]

    @property
    def valor_conclusao(self) -> str:
        return self.conclusao[1]

    def variaveis_condicao(self) -> List[str]:
        return [v for (v, _val) in self.condicoes]

    def __str__(self) -> str:
        cond = " E ".join(f"{v} = {val}" for (v, val) in self.condicoes)
        c_v, c_val = self.conclusao
        return f"{self.id}: SE {cond} ENTAO {c_v} = {c_val} (CF={self.cf:g})"


class BaseConhecimento:
    """Agrega o conhecimento do domínio e oferece operações de edição/persistência."""

    def __init__(self, dominio: str = "Domínio genérico"):
        self.dominio: str = dominio
        self.variaveis: Dict[str, Variavel] = {}
        self.regras: Dict[str, Regra] = {}
        # objetivos = variáveis-alvo que o motor tenta resolver (hipóteses/diagnósticos)
        self.objetivos: List[str] = []

    # ------------------------------------------------------------------ #
    # Edição de variáveis (fatos possíveis)                              #
    # ------------------------------------------------------------------ #
    def add_variavel(self, var: Variavel) -> None:
        self.variaveis[var.nome] = var

    def remover_variavel(self, nome: str) -> bool:
        return self.variaveis.pop(nome, None) is not None

    def is_perguntavel(self, nome: str) -> bool:
        v = self.variaveis.get(nome)
        return bool(v and v.perguntavel)

    # ------------------------------------------------------------------ #
    # Edição de regras                                                    #
    # ------------------------------------------------------------------ #
    def add_regra(self, regra: Regra) -> None:
        if regra.id in self.regras:
            raise ValueError(f"Já existe regra com id '{regra.id}'.")
        self.regras[regra.id] = regra
        self._registrar_variaveis_da_regra(regra)

    def alterar_regra(self, regra: Regra) -> None:
        """Substitui (ou cria) a regra de mesmo id."""
        self.regras[regra.id] = regra
        self._registrar_variaveis_da_regra(regra)

    def remover_regra(self, rid: str) -> bool:
        return self.regras.pop(rid, None) is not None

    def regras_que_concluem(self, variavel: str) -> List[Regra]:
        """Todas as regras cuja conclusão é sobre a variável dada (usado no backward)."""
        return [r for r in self.regras.values() if r.variavel_conclusao == variavel]

    def proximo_id_regra(self) -> str:
        n = 1
        while f"R{n}" in self.regras:
            n += 1
        return f"R{n}"

    def _registrar_variaveis_da_regra(self, regra: Regra) -> None:
        """Garante que toda variável citada em uma regra exista na base.
        Variáveis que aparecem como conclusão passam a ser tratadas como inferíveis."""
        for (v, val) in regra.condicoes:
            var = self.variaveis.setdefault(v, Variavel(nome=v))
            if val not in var.valores:
                var.valores.append(val)
        cv, cval = regra.conclusao
        var = self.variaveis.setdefault(cv, Variavel(nome=cv, perguntavel=False))
        var.perguntavel = False  # se algo conclui a variável, ela é inferida
        if cval not in var.valores:
            var.valores.append(cval)

    # ------------------------------------------------------------------ #
    # Persistência (carregar / salvar JSON)                               #
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "dominio": self.dominio,
            "objetivos": self.objetivos,
            "variaveis": {n: asdict(v) for n, v in self.variaveis.items()},
            "regras": [
                {
                    "id": r.id,
                    "se": [list(c) for c in r.condicoes],
                    "entao": list(r.conclusao),
                    "cf": r.cf,
                }
                for r in self.regras.values()
            ],
        }

    def salvar(self, caminho: str) -> None:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def carregar(cls, caminho: str) -> "BaseConhecimento":
        with open(caminho, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "BaseConhecimento":
        kb = cls(dominio=data.get("dominio", "Domínio genérico"))
        kb.objetivos = list(data.get("objetivos", []))
        for nome, v in data.get("variaveis", {}).items():
            kb.variaveis[nome] = Variavel(
                nome=v.get("nome", nome),
                pergunta=v.get("pergunta", ""),
                valores=list(v.get("valores", [])),
                perguntavel=bool(v.get("perguntavel", True)),
            )
        for r in data.get("regras", []):
            regra = Regra(
                id=r["id"],
                condicoes=[tuple(c) for c in r["se"]],
                conclusao=tuple(r["entao"]),
                cf=float(r.get("cf", 100.0)),
            )
            kb.regras[regra.id] = regra
            kb._registrar_variaveis_da_regra(regra)
        return kb
