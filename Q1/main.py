#!/usr/bin/env python3
"""
main.py — ponto de entrada da aplicação.

Abre a interface de linha de comando da shell. Por padrão já carrega a base
demonstrativa de Suporte Técnico; é possível passar outra base como argumento.

Uso:
    python main.py                          # carrega bases/suporte_tecnico.json
    python main.py bases/pragas_agricolas.json
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from expert_shell.cli import main

if __name__ == "__main__":
    # se nenhuma base for informada, usa a demonstrativa
    if len(sys.argv) == 1:
        padrao = os.path.join(ROOT, "bases", "suporte_tecnico.json")
        if os.path.exists(padrao):
            sys.argv.append(padrao)
    main()
