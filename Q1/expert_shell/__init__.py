"""
expert_shell
============
Shell genérica para construção de Sistemas Baseados em Conhecimento
(diagnóstico e recomendação), nos moldes do Expert SINTA.

API principal:
    from expert_shell import (BaseConhecimento, EditorBase, AgenteEspecialista,
                              ProvedorCLI, ProvedorAutomatico)
"""
from .knowledge_base import BaseConhecimento, Variavel, Regra
from .parser import parse_regra, regra_para_texto
from .inference_engine import MotorInferencia, combinar_cf, LIMIAR_CF
from .explanation import Explicador
from .kb_editor import EditorBase
from .shell import (AgenteEspecialista, ProvedorEvidencias,
                    ProvedorAutomatico, ProvedorCLI)

__all__ = [
    "BaseConhecimento", "Variavel", "Regra",
    "parse_regra", "regra_para_texto",
    "MotorInferencia", "combinar_cf", "LIMIAR_CF",
    "Explicador", "EditorBase",
    "AgenteEspecialista", "ProvedorEvidencias",
    "ProvedorAutomatico", "ProvedorCLI",
]
