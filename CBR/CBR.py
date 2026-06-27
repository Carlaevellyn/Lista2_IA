import json
import streamlit as st

ARQUIVO = "casos.json"

SINTOMAS_DISPONIVEIS = [
    "febre",
    "tosse",
    "dor_muscular",
    "dor_cabeca",
    "falta_ar",
    "nausea",
    "coriza",
    "congestao_nasal",
    "azia",
    "dor_estomago",
    "dor_garganta",
    "espirros",
    "coceira_nariz",
    "dor_ouvido",
    "perda_audicao",
    "diarreia",
    "chiado_peito",
    "manchas_pele"
]


# =========================
# BANCO DE CASOS
# =========================

def carregar_casos():
    try:
        with open(
            ARQUIVO,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)

    except Exception:
        return []


def salvar_casos(casos):

    with open(
        ARQUIVO,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            casos,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


# =========================
# CBR
# =========================

def calcular_similaridade(
    sintomas_usuario,
    sintomas_caso
):

    iguais = len(
        set(sintomas_usuario)
        &
        set(sintomas_caso)
    )

    total = len(
        set(sintomas_usuario)
        |
        set(sintomas_caso)
    )

    if total == 0:
        return 0

    return round(
        (iguais / total) * 100,
        2
    )


def recuperar_casos(
    sintomas_usuario,
    casos
):

    resultados = []

    for caso in casos:

        similaridade = calcular_similaridade(
            sintomas_usuario,
            caso["sintomas"]
        )

        resultados.append(
            {
                "caso": caso,
                "similaridade": similaridade
            }
        )

    resultados.sort(
        key=lambda x: x["similaridade"],
        reverse=True
    )

    return resultados


# =========================
# CONFIGURAÇÃO STREAMLIT
# =========================

st.set_page_config(
    page_title="Sistema CBR Médico",
    page_icon="🩺",
    layout="centered"
)

st.title("🩺 Sistema CBR Médico")
st.caption(
    "Case-Based Reasoning (CBR)"
)

casos = carregar_casos()

# =========================
# SESSION STATE
# =========================

if "buscou" not in st.session_state:
    st.session_state.buscou = False

if "resultados" not in st.session_state:
    st.session_state.resultados = []

if "sintomas_usuario" not in st.session_state:
    st.session_state.sintomas_usuario = []


# =========================
# SINTOMAS
# =========================

st.subheader(
    "Selecione os sintomas"
)

col1, col2 = st.columns(2)

sintomas_usuario = []

with col1:

    for sintoma in SINTOMAS_DISPONIVEIS[:9]:

        if st.checkbox(
            sintoma,
            key=f"cb_{sintoma}"
        ):
            sintomas_usuario.append(
                sintoma
            )

with col2:

    for sintoma in SINTOMAS_DISPONIVEIS[9:]:

        if st.checkbox(
            sintoma,
            key=f"cb_{sintoma}"
        ):
            sintomas_usuario.append(
                sintoma
            )


# =========================
# BUSCA
# =========================

if st.button(
    "🔍 Buscar Diagnóstico",
    use_container_width=True
):

    if len(sintomas_usuario) == 0:

        st.warning(
            "Selecione pelo menos um sintoma."
        )

    else:

        resultados = recuperar_casos(
            sintomas_usuario,
            casos
        )

        st.session_state.resultados = resultados
        st.session_state.sintomas_usuario = sintomas_usuario
        st.session_state.buscou = True


# =========================
# EXIBIÇÃO DOS RESULTADOS
# =========================

if st.session_state.buscou:

    resultados = (
        st.session_state.resultados
    )

    st.divider()

    st.subheader(
        "🏆 Casos Mais Semelhantes"
    )

    for posicao, resultado in enumerate(
        resultados[:3],
        start=1
    ):

        caso = resultado["caso"]

        st.markdown(
            f"### {posicao}º Lugar"
        )

        st.write(
            f"**Diagnóstico:** "
            f"{caso['diagnostico']}"
        )

        st.progress(
            int(resultado["similaridade"])
        )

        st.write(
            f"Similaridade: "
            f"{resultado['similaridade']}%"
        )

        st.write(
            f"Sintomas do caso: "
            f"{', '.join(caso['sintomas'])}"
        )

        st.divider()

    # =====================
    # REUSE
    # =====================

    melhor_caso = resultados[0]["caso"]

    st.success(
        f"Diagnóstico sugerido: "
        f"{melhor_caso['diagnostico']}"
    )

    st.info(
        f"Tratamento sugerido: "
        f"{melhor_caso['tratamento']}"
    )

    # =====================
    # REVISE
    # =====================

    st.subheader(
        "Revise a solução"
    )

    ajudou = st.radio(
        "A solução foi útil?",
        ["Sim", "Não"]
    )

    # =====================
    # RETAIN
    # =====================

    if ajudou == "Não":

        st.subheader(
            "➕ Adicionar Novo Caso"
        )

        novo_diagnostico = st.text_input(
            "Diagnóstico correto"
        )

        novo_tratamento = st.text_area(
            "Tratamento correto"
        )

        if st.button(
            "💾 Salvar Novo Caso"
        ):

            if (
                novo_diagnostico.strip()
                and
                novo_tratamento.strip()
            ):

                novo_caso = {

                    "id":
                    len(casos) + 1,

                    "sintomas":
                    st.session_state.sintomas_usuario,

                    "diagnostico":
                    novo_diagnostico,

                    "tratamento":
                    novo_tratamento
                }

                casos.append(
                    novo_caso
                )

                salvar_casos(
                    casos
                )

                st.success(
                    "✅ Novo caso adicionado à base de conhecimento!"
                )

            else:

                st.error(
                    "Preencha diagnóstico e tratamento."
                )

    # =====================
    # NOVA CONSULTA
    # =====================

    st.divider()

    if st.button(
        "🔄 Nova Consulta"
    ):

        st.session_state.buscou = False
        st.session_state.resultados = []
        st.session_state.sintomas_usuario = []

        st.rerun()