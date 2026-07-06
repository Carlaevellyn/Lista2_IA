"""
cli.py
======
INTERFACE COM O USUÁRIO (linha de comando) da shell.

Oferece dois grandes modos:
  [A] EDITOR  — o especialista cria/edita a base (variáveis, regras, objetivos)
                e a persiste em arquivo, sem tocar no código.
  [B] CONSULTA — o usuário final realiza uma consulta de diagnóstico, escolhendo
                 a estratégia de inferência (forward / backward / híbrido),
                 podendo perguntar 'por que?' a cada pergunta e 'como?' ao final.

Uso:
    python -m expert_shell.cli                # inicia com base vazia
    python -m expert_shell.cli bases/x.json   # carrega uma base
"""

from __future__ import annotations
import sys
from typing import Optional

from .knowledge_base import BaseConhecimento
from .kb_editor import EditorBase
from .parser import regra_para_texto
from .shell import AgenteEspecialista, ProvedorCLI


def _input(msg: str) -> str:
    try:
        return input(msg)
    except (EOFError, KeyboardInterrupt):
        print()
        return "0"


# ----------------------------------------------------------------------- #
# Editor                                                                   #
# ----------------------------------------------------------------------- #
def menu_editor(ed: EditorBase):
    while True:
        print(f"\n--- EDITOR DA BASE ({ed.kb.dominio}) ---")
        print(" 1) Listar regras           2) Adicionar regra")
        print(" 3) Alterar regra           4) Remover regra")
        print(" 5) Listar variáveis        6) Definir/editar variável perguntável")
        print(" 7) Definir objetivos       8) Salvar base")
        print(" 9) Carregar base           0) Voltar")
        op = _input("Opção: ").strip()

        if op == "1":
            if not ed.kb.regras:
                print("  (base sem regras)")
            for r in ed.kb.regras.values():
                print("  " + regra_para_texto(r) + f"   [{r.id}]")
        elif op == "2":
            txt = _input("  Regra (SE ... E ... ENTAO ... [CF n]): ").strip()
            try:
                r = ed.adicionar_regra_texto(txt)
                print(f"  Adicionada como {r.id}.")
            except Exception as e:
                print(f"  Erro: {e}")
        elif op == "3":
            rid = _input("  ID da regra a alterar: ").strip()
            txt = _input("  Nova regra: ").strip()
            try:
                ed.alterar_regra_texto(rid, txt)
                print(f"  Regra {rid} atualizada.")
            except Exception as e:
                print(f"  Erro: {e}")
        elif op == "4":
            rid = _input("  ID da regra a remover: ").strip()
            print("  Removida." if ed.remover_regra(rid) else "  ID não encontrado.")
        elif op == "5":
            for nome, v in ed.kb.variaveis.items():
                tipo = "perguntável" if v.perguntavel else "inferida"
                print(f"  {nome} ({tipo}) valores={v.valores}")
        elif op == "6":
            nome = _input("  Nome da variável: ").strip()
            perg = _input("  Texto da pergunta: ").strip()
            vals = [x.strip() for x in _input("  Valores (separe por vírgula): ").split(",") if x.strip()]
            ed.definir_variavel(nome, perg, vals, perguntavel=True)
            print("  Variável definida.")
        elif op == "7":
            objs = [x.strip() for x in _input("  Objetivos (vírgula): ").split(",") if x.strip()]
            ed.definir_objetivos(objs)
            print(f"  Objetivos = {objs}")
        elif op == "8":
            cam = _input("  Arquivo destino (.json): ").strip()
            ed.salvar(cam); print(f"  Salvo em {cam}.")
        elif op == "9":
            cam = _input("  Arquivo a carregar (.json): ").strip()
            try:
                ed.carregar(cam); print("  Base carregada.")
            except Exception as e:
                print(f"  Erro: {e}")
        elif op == "0":
            return


# ----------------------------------------------------------------------- #
# Consulta                                                                 #
# ----------------------------------------------------------------------- #
def menu_consulta(kb: BaseConhecimento):
    if not kb.regras:
        print("  Base vazia: carregue ou crie regras antes de consultar.")
        return
    print("\nEstratégia de inferência:")
    print("  1) Backward (dirigida ao objetivo — pergunta só o necessário)")
    print("  2) Forward  (dirigida pelos dados — coleta evidências e deduz)")
    print("  3) Híbrida  (forward de consolidação + backward dirigido)")
    modo = {"1": "backward", "2": "forward", "3": "hibrido"}.get(_input("Opção: ").strip(), "backward")

    agente = AgenteEspecialista(kb, ProvedorCLI(kb))
    resultados = agente.consultar(modo=modo)

    print("\n" + "=" * 60)
    print("RESULTADO DA CONSULTA")
    print("=" * 60)
    algum = False
    for obj, ranking in resultados.items():
        if not ranking:
            continue
        algum = True
        print(f"\n{obj.upper()}:")
        for val, cf in ranking:
            print(f"   • {val:35s} CF = {cf:5.0f}")
    if not algum:
        print("  Nenhuma conclusão pôde ser estabelecida com as evidências fornecidas.")
        return

    print(f"\nRegras disparadas: {agente.regras_disparadas()}")

    # explicações 'como?' sob demanda
    while True:
        q = _input("\nExplicar uma conclusão? (ex.: 'diagnostico=malware' ou ENTER p/ sair): ").strip()
        if not q:
            return
        if "=" not in q:
            print("  Formato: variavel=valor"); continue
        var, val = (s.strip() for s in q.split("=", 1))
        print("\n[COMO?]")
        for ln in agente.como(var, val).splitlines():
            print("  " + ln)


# ----------------------------------------------------------------------- #
# Principal                                                                #
# ----------------------------------------------------------------------- #
def main(argv: Optional[list] = None):
    argv = argv if argv is not None else sys.argv[1:]
    ed = EditorBase()
    if argv:
        try:
            ed.carregar(argv[0])
            print(f"Base carregada de {argv[0]}: {ed.kb.dominio}")
        except Exception as e:
            print(f"Não foi possível carregar '{argv[0]}': {e}")

    while True:
        print("\n========= SHELL DE SISTEMA BASEADO EM CONHECIMENTO =========")
        print(f"Domínio atual: {ed.kb.dominio}  | regras: {len(ed.kb.regras)}")
        print(" 1) Editor da base de conhecimento")
        print(" 2) Realizar consulta (diagnóstico/recomendação)")
        print(" 3) Definir nome do domínio")
        print(" 0) Sair")
        op = _input("Opção: ").strip()
        if op == "1":
            menu_editor(ed)
        elif op == "2":
            menu_consulta(ed.kb)
        elif op == "3":
            ed.kb.dominio = _input("Nome do domínio: ").strip() or ed.kb.dominio
        elif op == "0":
            print("Até logo.")
            return


if __name__ == "__main__":
    main()
