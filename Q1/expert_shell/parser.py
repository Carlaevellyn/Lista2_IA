"""
parser.py
=========
Tradutor entre o formato textual de regras usado pelo especialista
( SE cond1 E cond2 ENTAO conclusao [CF n] ) e o objeto Regra interno.

Permite que o especialista digite regras em linguagem próxima da natural,
sem conhecer a estrutura de dados da shell.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Optional
from .knowledge_base import Regra


def _sem_acento(texto: str) -> str:
    """Remove acentos para tornar o parser tolerante a ENTAO/ENTÃO, etc."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _split_condicao(cond: str):
    """Converte 'febre = alta' em ('febre', 'alta')."""
    if "=" not in cond:
        raise ValueError(f"Condição inválida (esperado 'var = valor'): '{cond}'")
    var, val = cond.split("=", 1)
    return (var.strip(), val.strip())


def parse_regra(texto: str, rid: str) -> Regra:
    """Faz o parsing de uma regra textual e devolve um objeto Regra.

    Exemplos aceitos:
        SE febre = alta E tosse = sim ENTAO suspeita = gripe
        SE febre = alta E tosse = sim ENTAO suspeita = gripe CF 80
        SE temperatura = alta ENTÃO diagnostico = superaquecimento  (acento ok)
    """
    original = texto.strip()
    plano = _sem_acento(original)

    # extrai CF opcional ao final: "... CF 80" ou "... [CF 80]"
    cf = 100.0
    m_cf = re.search(r"\[?\s*CF\s*=?\s*(-?\d+(?:\.\d+)?)\s*\]?\s*$", plano, re.IGNORECASE)
    if m_cf:
        cf = float(m_cf.group(1))
        # remove o trecho do CF tanto da versão plana quanto da original (mesmo span)
        original = original[: m_cf.start()].strip()
        plano = plano[: m_cf.start()].strip()

    # localiza SE ... ENTAO (case-insensitive, sobre a versão sem acento)
    m = re.match(r"\s*SE\s+(.*?)\s+ENTAO\s+(.*)\s*$", plano, re.IGNORECASE | re.DOTALL)
    if not m:
        raise ValueError(
            "Formato inválido. Use: SE <cond> E <cond> ENTAO <conclusao> [CF n]"
        )

    # usamos os índices encontrados na versão plana para recortar a ORIGINAL,
    # preservando acentos dos valores (ex.: 'difícil')
    parte_se = original[m.start(1):m.end(1)]
    parte_entao = original[m.start(2):m.end(2)]

    # separa as condições por ' E ' (com espaços, para não quebrar palavras com E)
    condicoes_txt = re.split(r"\s+E\s+", parte_se, flags=re.IGNORECASE)
    condicoes = [_split_condicao(c) for c in condicoes_txt if c.strip()]
    if not condicoes:
        raise ValueError("Nenhuma condição encontrada na regra.")

    conclusao = _split_condicao(parte_entao)
    return Regra(id=rid, condicoes=condicoes, conclusao=conclusao, cf=cf)


def regra_para_texto(regra: Regra) -> str:
    """Operação inversa: serializa uma Regra no formato textual legível."""
    cond = " E ".join(f"{v} = {val}" for (v, val) in regra.condicoes)
    cv, cval = regra.conclusao
    base = f"SE {cond} ENTAO {cv} = {cval}"
    if regra.cf != 100.0:
        base += f" CF {regra.cf:g}"
    return base
