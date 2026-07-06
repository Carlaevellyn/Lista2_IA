#!/usr/bin/env python3
"""
run_web.py — sobe a interface web da shell.

Por padrão carrega a base demonstrativa de Suporte Técnico e abre o navegador
em http://127.0.0.1:5000. É possível passar outra base como argumento.

Uso:
    python run_web.py                          # bases/suporte_tecnico.json
    python run_web.py bases/pragas_agricolas.json
"""
import os
import sys
import threading
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from expert_shell.web.server import criar_app

HOST = "127.0.0.1"
PORT = 5000

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "bases", "suporte_tecnico.json")
    if not os.path.isabs(base):
        base = os.path.join(ROOT, base)

    app = criar_app(base if os.path.exists(base) else None)

    # abre o navegador assim que o servidor estiver de pé (só no processo principal,
    # evita abrir duas abas por causa do reloader do Flask)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{HOST}:{PORT}")).start()

    print(f"\n  Expert Shell (web) em http://{HOST}:{PORT}   (Ctrl+C para sair)\n")
    app.run(host=HOST, port=PORT, debug=False)
