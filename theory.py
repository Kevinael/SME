import streamlit as st


THEORY_DATA = [
    {
        "group": "Parâmetros Elétricos",
        "items": [
            {
                "nome": "$V_l$ — Tensão de Linha (RMS)",
                "desc": (
                    "Define a amplitude do campo magnético girante no estator. "
                    "É a grandeza que estabelece o ponto de operação magnética da máquina "
                    "e determina o fluxo no entreferro."
                ),
                "up": (
                    "O torque máximo cresce com o quadrado da tensão. "
                    "A corrente de partida também aumenta significativamente."
                ),
                "down": (
                    "O torque de partida cai, podendo tornar-se insuficiente para vencer a inércia da carga, "
                    "impedindo a partida do motor."
                ),
                "warn": (
                    "Sobretensão provoca saturação do núcleo e degradação térmica do isolamento. "
                    "Subtensão severa pode causar o travamento (stall) sob carga."
                ),
            },
            {
                "nome": "$f$ — Frequência da Rede",
                "desc": (
                    "Determina a velocidade síncrona do campo girante ($n_s = 120 \\times f / p$). "
                    "As reatâncias do circuito equivalente são diretamente proporcionais a este parâmetro."
                ),
                "up": (
                    "Aumenta a velocidade síncrona e as reatâncias ($X_m$, $X_{ls}$, $X_{lr}$), "
                    "deslocando a curva T × n e reduzindo o torque de partida se a tensão for constante."
                ),
                "down": (
                    "Reduz a velocidade de operação. Com tensão constante, a relação V/f cresce, "
                    "levando o núcleo à saturação magnética."
                ),
                "warn": (
                    "Operar fora da frequência nominal sem controle V/f constante compromete "
                    "o fluxo, a eficiência e a integridade térmica da máquina."
                ),
            },
            {
                "nome": "$R_s$ — Resistência do Estator",
                "desc": (
                    "Representa as perdas Joule nos enrolamentos estatóricos. "
                    "Provoca queda de tensão interna, reduzindo a FEM disponível no entreferro."
                ),
                "up": (
                    "Aumenta a dissipação térmica e reduz o torque máximo. "
                    "O motor opera com menor eficiência e maior aquecimento."
                ),
                "down": (
                    "Minimiza perdas internas e melhora o rendimento. "
                    "Em valores extremos, aproxima o modelo de um transformador ideal no primário."
                ),
                "warn": (
                    "$R_s$ excessivo (comum em enrolamentos danificados) causa sobreaquecimento fatal. "
                    "Valores próximos a zero podem gerar instabilidade numérica."
                ),
            },
            {
                "nome": "$R_r$ — Resistência do Rotor",
                "desc": (
                    "Parâmetro determinante da curva de torque. Controla o escorregamento de regime "
                    "e o torque de partida."
                ),
                "up": (
                    "O escorregamento de regime aumenta (menor rotação sob carga). "
                    "O torque de partida cresce até o ponto de torque máximo."
                ),
                "down": (
                    "Melhora a eficiência e reduz o escorregamento em regime. "
                    "O torque de partida diminui e a curva T × n torna-se mais íngreme próxima à sincronia."
                ),
                "warn": (
                    "$R_r$ muito alto indica barras fraturadas — provoca escorregamento excessivo. "
                    "Valores nulos causam singularidade matemática nas equações do rotor."
                ),
            },
            {
                "nome": "$X_m$ — Reatância de Magnetização",
                "desc": (
                    "Representa o ramo de magnetização (shunt) do circuito: o caminho do fluxo principal pelo núcleo."
                ),
                "up": "Reduz a corrente de magnetização em vazio, melhorando o fator de potência.",
                "down": "Aumenta a corrente reativa necessária para excitar o núcleo, piorando o fator de potência.",
                "warn": (
                    "$X_m$ baixo indica núcleo de má qualidade ou saturado. "
                    "Valores excessivamente baixos podem causar divergência numérica."
                ),
            },
            {
                "nome": "$R_{fe}$ — Resistência de Perdas no Ferro",
                "desc": (
                    "Modela as perdas no núcleo ferromagnético (histerese + correntes de Foucault) "
                    "como um resistor em paralelo com $X_m$ no ramo shunt do circuito equivalente. "
                    "Valores típicos estão entre 100 e 2000 Ω para motores de médio porte."
                ),
                "up": (
                    "Reduz as perdas no ferro ($P_{fe}$ menor). O motor opera com maior eficiência "
                    "em regimes de baixa carga onde as perdas no núcleo dominam."
                ),
                "down": (
                    "Aumenta as perdas no núcleo. O rendimento cai, especialmente em operação a vazio. "
                    "Pode indicar lâminas de baixa qualidade ou frequência elevada."
                ),
                "warn": (
                    "$R_{fe}$ é usado apenas no cálculo de potências e rendimento em regime permanente — "
                    "não influencia as equações diferenciais nem a dinâmica simulada. "
                    "Valores muito baixos (< 50 Ω) indicam núcleo de baixíssima qualidade."
                ),
            },
            {
                "nome": "$X_{ls}$ e $X_{lr}$ — Reatâncias de Dispersão",
                "desc": (
                    "Modelam os fluxos que não enlaçam ambos os enrolamentos (dispersão). "
                    "Limitam a corrente de partida e a capacidade máxima de transferência de torque."
                ),
                "up": (
                    "Aumenta a impedância total, reduzindo a corrente de partida, "
                    "porém limita drasticamente o torque máximo."
                ),
                "down": (
                    "Eleva o torque máximo e as correntes de partida. "
                    "Torna o motor mais sensível a transitórios de carga."
                ),
                "warn": (
                    "Dispersão muito baixa resulta em picos de corrente perigosos ao isolamento. "
                    "Dispersão excessiva pode impedir a partida do motor sob carga nominal."
                ),
            },
        ],
    },
    {
        "group": "Parâmetros Mecânicos",
        "items": [
            {
                "nome": "$p$ — Número de Polos",
                "desc": "Define a velocidade síncrona e a faixa de rotação da máquina.",
                "up": "Reduz a velocidade síncrona. Para manter a mesma potência mecânica, o torque nominal deve ser maior.",
                "down": "Aumenta a velocidade síncrona. O torque nominal diminui para uma mesma potência de saída.",
                "warn": "O número de polos deve ser sempre um inteiro par. Valores ímpares invalidam o modelo físico.",
            },
            {
                "nome": "$J$ — Momento de Inércia",
                "desc": "Representa a inércia rotacional do conjunto rotor-carga. Rege a dinâmica de aceleração.",
                "up": "Aceleração mais lenta e resposta a transitórios amortecida.",
                "down": "Resposta dinâmica acelerada. O rotor reage quase instantaneamente a variações de torque.",
                "warn": (
                    "$J$ muito baixo pode gerar oscilações numéricas ruidosas. "
                    "$J$ muito alto pode exigir tempo de simulação maior para atingir o regime."
                ),
            },
            {
                "nome": "$B$ — Coeficiente de Atrito Viscoso",
                "desc": "Modela perdas mecânicas proporcionais à velocidade (mancais e ventilação).",
                "up": "Aumenta o amortecimento do sistema e a dissipação mecânica.",
                "down": "Reduz perdas mecânicas. Se $B = 0$, o amortecimento depende exclusivamente da carga externa.",
                "warn": (
                    "Valores elevados podem impedir que o motor atinja a velocidade nominal, "
                    "simulando uma falha catastrófica em rolamentos."
                ),
            },
        ],
    },
    {
        "group": "Parâmetros de Simulação",
        "items": [
            {
                "nome": "$t_{max}$ — Tempo de Simulação",
                "desc": "Define o horizonte temporal da integração. Deve comportar o transitório de partida.",
                "up": "Permite observar fenômenos de longo prazo, mas aumenta o custo computacional.",
                "down": "Processamento rápido, mas corre o risco de truncar a análise antes da estabilização.",
                "warn": "$t_{max}$ elevado com passo reduzido pode causar estouro de memória no navegador.",
            },
            {
                "nome": "$h$ — Passo de Integração",
                "desc": "Discretização temporal para o solver (scipy.odeint / LSODA).",
                "up": "Aumenta a velocidade de cálculo, mas compromete a precisão.",
                "down": "Garante alta fidelidade e estabilidade, exigindo maior tempo de processamento.",
                "warn": "Recomenda-se $h \\leq 1/(20 \\cdot f)$. Passos acima de 1 ms costumam causar divergência a 60 Hz.",
            },
        ],
    },
]


def render_theory_tab() -> None:
    st.markdown(
        "Nesta aba, cada parâmetro é descrito em termos de seu significado físico e do impacto "
        "qualitativo que provoca no comportamento da máquina."
    )
    for group in THEORY_DATA:
        st.write("")
        st.markdown(f"## {group['group']}")
        for item in group["items"]:
            st.markdown(
                f'<div class="tcard">'
                f'<h4>{item["nome"]}</h4>'
                f'<p>{item["desc"]}</p>'
                f'<p><span class="tc-up">Se aumentar:</span> {item["up"]}</p>'
                f'<p><span class="tc-down">Se diminuir:</span> {item["down"]}</p>'
                f'<div class="tc-warn">Atenção — calibrações extremas: {item["warn"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
