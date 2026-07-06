# Q2 — Akinator Anime (Inferência) + CBR Médico (Case-Based Reasoning)

## Integrantes

* Carla Evellyn
* Jhennifer Kyria
* Sthefany Barboza

---

# Questão 2.1 – Sistema de Inferência (Akinator Anime)

## Descrição

Este projeto implementa um sistema de inferência inspirado no jogo Akinator, capaz de identificar personagens de anime a partir das respostas fornecidas pelo usuário.

O sistema utiliza uma base de conhecimento armazenada em JSON contendo personagens e seus atributos. Durante a execução, perguntas são realizadas ao usuário para reduzir o conjunto de hipóteses até encontrar o personagem mais provável.

---

## Técnica Utilizada

### Busca em Espaço de Hipóteses

Inicialmente todos os personagens cadastrados são considerados candidatos.

A cada resposta do usuário:

* Personagens incompatíveis são eliminados;
* O espaço de hipóteses é reduzido;
* Novas perguntas são selecionadas automaticamente;
* O processo continua até restar apenas uma hipótese ou uma hipótese mais provável.

---

## Seleção Inteligente de Perguntas

O sistema utiliza uma estratégia para escolher a próxima pergunta.

A função busca o atributo que melhor divide os candidatos restantes, reduzindo o número de perguntas necessárias para identificar o personagem.

Essa abordagem melhora a eficiência do processo de inferência.

---

## Base de Conhecimento

Arquivo:

```text
personagens.json
```

Cada personagem possui informações como:

* nome
* anime
* humano
* poder
* pirata
* ninja
* estudante
* protagonista
* espada
* vilao
* professor
* guerreiro
* magico
* anti_heroi
* transformação
* olhos_especiais

entre outros atributos.

---

## Ranking de Hipóteses

Durante a execução o sistema calcula uma pontuação para cada candidato com base nas respostas fornecidas.

As hipóteses mais compatíveis são apresentadas ao usuário juntamente com:

* personagem mais provável;
* quantidade de hipóteses restantes;
* ranking dos candidatos.

---

## Aprendizado

Quando o sistema não consegue identificar corretamente o personagem, o usuário pode ensinar um novo personagem informando:

* nome;
* anime;
* respostas dos atributos.

O novo conhecimento é armazenado automaticamente na base.

---

## Testes Automáticos

O sistema possui uma aba exclusiva para avaliação.

Para cada personagem cadastrado:

1. O sistema simula uma partida automaticamente;
2. Tenta identificar o personagem;
3. Registra o resultado.

Os resultados são armazenados em:

```text
testes.json
```

---

## Métricas de Avaliação

São calculadas automaticamente:

* Taxa de acerto;
* Número de falhas;
* Média de perguntas realizadas;
* Histórico completo dos testes.

---

## Funcionalidades

* Inferência baseada em perguntas e respostas;
* Eliminação automática de hipóteses;
* Escolha inteligente de perguntas;
* Ranking de candidatos;
* Aprendizado incremental;
* Persistência em JSON;
* Testes automáticos;
* Métricas de desempenho;
* Interface gráfica desenvolvida com Streamlit.

---

## Execução

```bash
pip install streamlit
streamlit run app.py
```

---

# Questão 2.4 – Sistema CBR (Case-Based Reasoning)

## Descrição

Este projeto implementa um sistema de diagnóstico médico simplificado utilizando a técnica de Raciocínio Baseado em Casos (CBR).

O sistema compara os sintomas informados pelo usuário com casos armazenados previamente e sugere o diagnóstico e tratamento mais adequados.

---

## Ciclo CBR Implementado

### 1. Retrieve (Recuperação)

Recupera os casos mais semelhantes ao problema informado.

### 2. Reuse (Reutilização)

Utiliza a solução do caso mais semelhante.

### 3. Revise (Revisão)

Permite que o usuário valide ou rejeite o diagnóstico sugerido.

### 4. Retain (Retenção)

Caso necessário, um novo caso pode ser armazenado na base de conhecimento.

---

## Base de Conhecimento

Arquivo:

```text
casos.json
```

Cada caso contém:

* sintomas;
* diagnóstico;
* tratamento;
* pesos dos sintomas.

---

## Método de Similaridade

O sistema utiliza similaridade ponderada por sintomas.

Cada sintoma pode possuir um peso diferente, permitindo que sintomas mais importantes tenham maior influência no cálculo.

A similaridade é calculada como:

```text
Similaridade =
(pontos obtidos / pontos totais) × 100
```

---

## Recursos Implementados

### Recuperação de Casos

* Busca dos casos mais semelhantes;
* Ordenação por similaridade;
* Exibição do Top 3 resultados.

### Explicabilidade

Para cada caso recuperado são exibidos:

* sintomas coincidentes;
* sintomas ausentes;
* percentual de similaridade;
* pesos utilizados.

### Nível de Confiança

O sistema classifica automaticamente o resultado em:

* 🟢 Alta
* 🟡 Média
* 🔴 Baixa

---

## Estatísticas

A aplicação possui uma aba dedicada para análise dos dados.

São exibidos:

* quantidade de casos cadastrados;
* quantidade de diagnósticos distintos;
* consultas realizadas;
* média de similaridade;
* diagnósticos mais frequentes;
* histórico de consultas;
* gráfico de distribuição dos diagnósticos.

---

## Funcionalidades

* Seleção de sintomas por checkboxes;
* Observações do paciente;
* Similaridade ponderada;
* Top 3 casos mais semelhantes;
* Diagnóstico sugerido;
* Tratamento sugerido;
* Validação do usuário;
* Inclusão de novos casos;
* Histórico de consultas;
* Estatísticas da base;
* Persistência em JSON;
* Interface gráfica desenvolvida com Streamlit.

---

## Execução

```bash
pip install streamlit
streamlit run CBR.py
```

---

# Tecnologias Utilizadas

* Python 3
* Streamlit
* JSON

# Técnicas de Inteligência Artificial

* Busca em Espaço de Hipóteses
* Sistemas de Inferência
* Case-Based Reasoning (CBR)
* Aprendizado Incremental
* Recuperação Baseada em Similaridade

