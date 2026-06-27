import json
import streamlit as st

ARQUIVO_PERSONAGENS = "personagens.json"

perguntas = {
    "humano": "O personagem é humano?",
    "poder": "Possui poderes especiais?",
    "pirata": "É pirata?",
    "ninja": "É ninja?",
    "estudante": "É estudante?",
    "protagonista": "É protagonista?",
    "espada": "Usa espada?",
    "vilao": "É vilão?",
    "masculino": "É masculino?",
    "alien": "É alienígena?",
    "professor": "É professor?",
    "detetive": "É detetive?",
    "guerreiro": "É guerreiro?",
    "magico": "Utiliza magia?",
    "anime_moderno": "É de anime recente?"
}


def carregar_personagens():
    try:
        with open(
            ARQUIVO_PERSONAGENS,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:
        return []


def salvar_personagens(personagens):

    with open(
        ARQUIVO_PERSONAGENS,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            personagens,
            f,
            ensure_ascii=False,
            indent=4
        )


st.set_page_config(
    page_title="Akinator Anime",
    page_icon="🎭",
    layout="centered"
)

st.title("🎭 Akinator Anime")
st.caption("Pense em um personagem e responda às perguntas")

personagens = carregar_personagens()

if "candidatos" not in st.session_state:
    st.session_state.candidatos = personagens.copy()

if "indice" not in st.session_state:
    st.session_state.indice = 0

if "fim" not in st.session_state:
    st.session_state.fim = False


lista_perguntas = list(perguntas.items())

if not st.session_state.fim:

    progresso = (
        st.session_state.indice
        / len(lista_perguntas)
    )

    st.progress(progresso)

    if (
        st.session_state.indice
        < len(lista_perguntas)
    ):

        atributo, pergunta = (
            lista_perguntas[
                st.session_state.indice
            ]
        )

        st.subheader(pergunta)

        col1, col2, col3 = st.columns(3)

        with col1:

            if st.button(
                "✅ Sim",
                use_container_width=True
            ):

                st.session_state.candidatos = [

                    p

                    for p in st.session_state.candidatos

                    if p[atributo] == "s"
                ]

                st.session_state.indice += 1
                st.rerun()

        with col2:

            if st.button(
                "❌ Não",
                use_container_width=True
            ):

                st.session_state.candidatos = [

                    p

                    for p in st.session_state.candidatos

                    if p[atributo] == "n"
                ]

                st.session_state.indice += 1
                st.rerun()

        with col3:

            if st.button(
                "🤔 Não sei",
                use_container_width=True
            ):

                st.session_state.indice += 1
                st.rerun()

        if (
            len(
                st.session_state.candidatos
            ) <= 1
        ):

            st.session_state.fim = True
            st.rerun()

else:

    st.balloons()

    candidatos = (
        st.session_state.candidatos
    )

    if len(candidatos) > 0:

        personagem = candidatos[0]

        st.success(
            f"🎉 Eu acho que é: "
            f"{personagem['nome']}"
        )

    else:

        st.error(
            "Não consegui descobrir."
        )

        with st.form(
            "novo_personagem"
        ):

            nome = st.text_input(
                "Qual era o personagem?"
            )

            dados = {}

            for atributo, pergunta in perguntas.items():

                dados[atributo] = st.selectbox(
                    pergunta,
                    ["s", "n"],
                    key=atributo
                )

            enviar = st.form_submit_button(
                "Adicionar"
            )

            if enviar:

                novo = {
                    "nome": nome
                }

                novo.update(dados)

                personagens.append(novo)

                salvar_personagens(
                    personagens
                )

                st.success(
                    "Personagem adicionado!"
                )

    if st.button(
        "🔄 Jogar novamente"
    ):

        st.session_state.candidatos = (
            personagens.copy()
        )

        st.session_state.indice = 0
        st.session_state.fim = False

        st.rerun()