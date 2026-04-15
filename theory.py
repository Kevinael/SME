# -*- coding: utf-8 -*-
"""Aba Teoria — conteúdo educacional do simulador de máquinas de indução."""

from __future__ import annotations
import base64
import io
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components


# ─────────────────────────────────────────────────────────────────────────────
# UTILITÁRIOS
# ─────────────────────────────────────────────────────────────────────────────

def _inject_mathjax() -> None:
    """Injeta MathJax + MutationObserver para re-renderizar LaTeX dinâmico."""
    components.html(
        """
        <script>
        (function () {
            var par = window.parent;
            if (par.document.getElementById('mathjax-script')) {
                if (par.MathJax && par.MathJax.typesetPromise)
                    par.MathJax.typesetPromise();
                return;
            }
            par.MathJax = {
                tex: {
                    inlineMath:  [['$','$'], ['\\\\(','\\\\)']],
                    displayMath: [['$$','$$'], ['\\\\[','\\\\]']]
                },
                options: { skipHtmlTags: ['script','noscript','style','textarea','pre'] },
                startup: {
                    ready() {
                        par.MathJax.startup.defaultReady();
                        var obs = new par.MutationObserver(function () {
                            par.MathJax.typesetPromise && par.MathJax.typesetPromise();
                        });
                        obs.observe(par.document.body, { childList: true, subtree: true });
                    }
                }
            };
            var s = par.document.createElement('script');
            s.id  = 'mathjax-script';
            s.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js';
            s.async = true;
            par.document.head.appendChild(s);
        })();
        </script>
        """,
        height=0,
    )


def _b64(fname: str) -> str:
    p = Path(__file__).parent / fname
    if not p.exists():
        return ""
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _img(fname: str, pct: str = "100%") -> str:
    b64 = _b64(fname)
    if not b64:
        return f'<p style="color:#888;font-style:italic;">[{fname} não encontrada]</p>'
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'style="width:{pct};max-width:100%;display:block;'
        f'border-radius:8px;margin:.2rem 0 .2rem 0;">'
    )


# ── figura matplotlib → base64 ────────────────────────────────────────────────

def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    return f'<img src="data:image/png;base64,{b64}" style="width:100%;max-width:100%;display:block;border-radius:8px;margin:.2rem 0;">'


# ── parâmetros de referência para curvas T×s ──────────────────────────────────

_V1_REF, _f_REF, _p_REF = 220, 60, 4
_R1_REF, _X1_REF        = 0.50, 1.00
_R2_REF, _X2_REF        = 0.40, 1.00
_Xm_REF                 = 50.0
_ns_REF                 = 120 * _f_REF / _p_REF   # 1800 RPM


def _torque_ref(s: float) -> float:
    """Torque (N·m) para o motor de referência da aba teoria."""
    if abs(s) < 1e-4:
        s = 1e-4
    Z2  = _R2_REF / s + 1j * _X2_REF
    Zeq = (1j * _Xm_REF * Z2) / (1j * _Xm_REF + Z2)
    Zt  = _R1_REF + 1j * _X1_REF + Zeq
    I1  = _V1_REF / Zt
    I2  = (I1 * Zeq) / Z2
    return 3 * abs(I2) ** 2 * (_R2_REF / s) / (2 * np.pi * _ns_REF / 60)


# ── construtores de cartões ───────────────────────────────────────────────────

_P  = 'style="font-size:.92rem;line-height:1.8;margin:.45rem 0;"'
_LI = 'style="font-size:.92rem;line-height:1.9;"'

def _card(title: str, body: str) -> None:
    st.markdown(
        f'<div class="tcard"><h4>{title}</h4>{body}</div>',
        unsafe_allow_html=True,
    )


def _card_side(title: str, fname: str, body: str, *, img_right: bool = False) -> None:
    img_div = f'<div style="flex:0 0 46%;min-width:200px;">{_img(fname)}</div>'
    txt_div = f'<div style="flex:1;min-width:200px;padding-top:.1rem;">{body}</div>'
    pair    = f'{txt_div}{img_div}' if img_right else f'{img_div}{txt_div}'
    st.markdown(
        f'<div class="tcard">'
        f'<h4 style="margin-bottom:.9rem;">{title}</h4>'
        f'<div style="display:flex;gap:2rem;align-items:flex-start;flex-wrap:wrap;">'
        f'{pair}</div></div>',
        unsafe_allow_html=True,
    )


def _card_top(title: str, fname: str, body: str, *, pct: str = "88%") -> None:
    st.markdown(
        f'<div class="tcard">'
        f'<h4 style="margin-bottom:.9rem;">{title}</h4>'
        f'<div style="text-align:center;margin-bottom:1.1rem;">{_img(fname, pct)}</div>'
        f'{body}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _eq(latex: str) -> str:
    return f'<div style="text-align:center;margin:.7rem 0;">$${latex}$$</div>'


# ─────────────────────────────────────────────────────────────────────────────
# ABA 1 — MODELAGEM E CIRCUITOS EQUIVALENTES
# ─────────────────────────────────────────────────────────────────────────────

def _render_tab_circuitos() -> None:
    st.markdown(
        "O **circuito equivalente monofásico** transforma o problema eletromagnético "
        "trifásico em um circuito elétrico de regime permanente. A partir dele derivam-se "
        "as equações de torque, potência e, por extensão, o modelo $0dq$ de Krause "
        "utilizado na integração dinâmica do simulador."
    )

    # 1a. Circuito Completo
    _card_side(
        "Circuito Completo — com $R_{fe}$",
        "ind_completo.png",
        f"""
        <p {_P}>
        O ramo <em>shunt</em> contém $R_{{fe}} \\parallel jX_m$, onde $R_{{fe}}$ modela
        as perdas no ferro por <strong>histerese</strong> e <strong>correntes de Foucault</strong>.
        A corrente de excitação se decompõe em:
        </p>
        {_eq(r"I_\phi = I_c + jI_m = \frac{V_1}{R_{fe}} + \frac{V_1}{jX_m}")}
        <p {_P}>
        O elemento $R'_2/s$ concentra dois efeitos físicos em série:
        </p>
        {_eq(r"\frac{R'_2}{s} = R'_2 \;+\; R'_2\frac{1-s}{s}")}
        <p {_P}>
        onde $R'_2$ é a <strong>resistência real do rotor</strong> (perdas Joule) e
        $R'_2(1-s)/s$ é o equivalente resistivo da <strong>potência mecânica convertida</strong>.
        </p>
        """,
    )

    # 1b. Circuito IEEE
    _card_side(
        "Circuito IEEE — Modelo Simplificado (sem $R_{fe}$)",
        "ind_ieee.png",
        f"""
        <p {_P}>
        $R_{{fe}}$ é omitido — apenas $jX_m$ permanece no ramo <em>shunt</em>.
        Simplificação válida porque as perdas no ferro representam tipicamente
        $P_{{fe}} \\lesssim 2\\%\\,P_{{nom}}$; $R_{{fe}}$ é contabilizado
        separadamente no cálculo de rendimento $\\eta$.
        </p>
        <p {_P}>Equação de malha do estator:</p>
        {_eq(r"\bar{V}_1 = \bar{I}_1(R_s + jX_{ls}) + j X_m(\bar{I}_1 - \bar{I}'_2)")}
        <p {_P}>
        Este é o circuito de referência para derivação das equações de estado
        do modelo $0dq$ de Krause implementado no simulador.
        </p>
        """,
        img_right=True,
    )

    # 1c. Thévenin
    _card_side(
        "Equivalente de Thévenin — Redução da Malha do Rotor",
        "ind_thevenin.png",
        f"""
        <p {_P}>
        O estator e o ramo de magnetização são substituídos por uma fonte $V_{{th}}$
        com impedância $Z_{{th}}$, produzindo uma <strong>malha única para o rotor</strong>:
        </p>
        {_eq(r"V_{th} \approx V_1 \frac{X_m}{X_1+X_m}, \quad R_{th} \approx R_1\!\left(\frac{X_m}{X_1+X_m}\right)^{\!2}, \quad X_{th} \approx X_1")}
        <p {_P}>Torque eletromagnético em função de $s$:</p>
        {_eq(r"T_e(s) = \frac{3\,V_{th}^2\,R'_2/s}{\omega_s\!\left[(R_{th}+R'_2/s)^2+(X_{th}+X'_2)^2\right]}")}
        <p {_P}>
        Esta expressão explícita de $T_e(s)$ é a base do <strong>Teorema de Boucherot</strong>
        (Aba 2) e, ao ser linearizada no referencial $dq$, origina as equações de estado
        do <strong>modelo de Krause</strong> integradas pelo simulador.
        </p>
        """,
    )

    # 1d. Conexão com o modelo dq de Krause
    _card(
        "Do Circuito Equivalente ao Modelo $0dq$ de Krause",
        f"""
        <p {_P}>
        O simulador resolve as equações diferenciais no <strong>referencial $dq$ síncrono</strong>
        ($\\omega_{{ref}} = \\omega_e$), usando os <strong>fluxos concatenados</strong>
        $\\psi_{{qs}},\\,\\psi_{{ds}},\\,\\psi_{{qr}},\\,\\psi_{{dr}}$ como variáveis de estado,
        junto com a velocidade rotórica $\\omega_r$.
        </p>
        <p {_P}>Equações de estado (referencial síncrono):</p>
        {_eq(r"\dot{\psi}_{qs} = \omega_b\!\left(V_{qs} - \tfrac{\omega_e}{\omega_b}\psi_{ds} + \tfrac{R_s}{X_{ls}}(\psi_{mq}-\psi_{qs})\right)")}
        {_eq(r"\dot{\psi}_{qr} = \omega_b\!\left(-\tfrac{\omega_e-\omega_r}{\omega_b}\psi_{dr} + \tfrac{R_r}{X_{lr}}(\psi_{mq}-\psi_{qr})\right)")}
        {_eq(r"T_e = \tfrac{3}{2}\cdot\tfrac{p}{2}\cdot\tfrac{1}{\omega_b}(\psi_{ds}\,i_{qs}-\psi_{qs}\,i_{ds})")}
        {_eq(r"\dot{\omega}_r = \tfrac{p}{2J}(T_e - T_L) - \tfrac{B}{J}\,\omega_r")}
        <p {_P}>
        Os eixos $q$ e $d$ correspondem, respectivamente, às projeções em quadratura
        e em fase da tensão de alimentação no referencial síncrono. O acoplamento entre
        eles replica, em tempo real, o comportamento previsto pelo circuito equivalente em
        regime permanente.
        </p>
        """,
    )

    # 1e. Gaiola Dupla (circuito)
    _card_side(
        "Circuito com Gaiola de Esquilo Dupla",
        "ind_ieee_duplo.png",
        f"""
        <p {_P}>
        Dois ramos de rotor em paralelo: gaiola <strong>externa</strong>
        ($R_{{2e}}$ alto, $X_{{2e}}$ baixo) e <strong>interna</strong>
        ($R_{{2i}}$ baixo, $X_{{2i}}$ alto). Impedância equivalente:
        </p>
        {_eq(r"Z'_{2,eq} = \frac{Z'_{2e}\,Z'_{2i}}{Z'_{2e}+Z'_{2i}}")}
        <p {_P}>
        O <strong>efeito pelicular</strong> redistribui a corrente automaticamente
        com a frequência rotórica $f_r = s\\cdot f$:
        </p>
        <ul {_LI}>
          <li><strong>Partida</strong> ($s\\approx 1$, $f_r = f$): corrente concentra-se
              na gaiola externa $\\Rightarrow$ alto $T_{{part}}$.</li>
          <li><strong>Regime</strong> ($s\\approx 0{{,}}04$, $f_r \\approx 2$–$4\\;$Hz):
              corrente migra para a gaiola interna $\\Rightarrow$ baixo $s_{{nom}}$, alto $\\eta$.</li>
        </ul>
        """,
        img_right=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ABA 2 — COMPORTAMENTO DINÂMICO E TORQUE
# ─────────────────────────────────────────────────────────────────────────────

def _render_tab_dinamica() -> None:
    st.markdown(
        "O **escorregamento** $s = (n_s - n_r)/n_s$ governa o modo de operação da máquina. "
        "Três regiões fisicamente distintas dividem a curva $T_e \\times n$, "
        "com dinâmicas e riscos operacionais diferentes."
    )

    # Curva completa
    _card_top(
        "Curva Característica Completa — $T_e \\times n\\;/\\;s$",
        "T_x_s.png",
        pct="90%",
        body="",
    )

    # Três regiões
    col1, col2, col3 = st.columns(3)
    with col1:
        _card(
            "Região 1 — Frenagem &nbsp;($s > 1$)",
            f"""
            <p {_P}>
            O rotor gira em sentido oposto ao campo girante.
            $T_e < 0$: a máquina age como <strong>freio eletromagnético</strong>
            oposto ao movimento.
            </p>
            {_eq(r"P_{cu,2} = s\,P_{ag} > P_{ag} \quad (s>1)")}
            <p {_P}>
            O rotor absorve mais energia do que a fornecida pela rede —
            a diferença provém da <strong>energia cinética da carga</strong>.
            </p>
            <div class="tc-warn">
            Aplicação: <em>plugging</em> (inversão de fase para parada forçada).
            Risco severo de sobreaquecimento — operação limitada a segundos.
            </div>
            """,
        )
    with col2:
        _card(
            "Região 2 — Motor &nbsp;($0 < s < 1$)",
            f"""
            <p {_P}>Operação nominal. Potência elétrica convertida em mecânica:</p>
            {_eq(r"P_{mec} = (1-s)\,P_{ag} = T_e\,\omega_r")}
            <p {_P}>
            <strong>Região estável:</strong> $n_{{max}} < n < n_s$ — perturbações são
            autorreguladas pelo aumento de $T_e$ quando $n$ cai.<br>
            <strong>Região instável:</strong> $0 < n < n_{{max}}$ — risco de
            <em>travamento (stall)</em> sob carga.
            </p>
            <p {_P}>
            Escorregamento nominal típico: $s_n \\approx 0{{,}}02$–$0{{,}}06$.
            </p>
            """,
        )
    with col3:
        _card(
            "Região 3 — Gerador &nbsp;($s < 0$)",
            f"""
            <p {_P}>
            Rotor acelerado acima de $n_s$ por fonte motriz externa.
            $T_e$ inverte sentido: a máquina entrega potência elétrica à rede.
            </p>
            {_eq(r"P_{ag} = T_e\,\omega_s < 0 \;\Rightarrow\; P_{out,ele} > 0")}
            <p {_P}>
            $P_{{cu,2}} = s\\,P_{{ag}} < 0$: o rotor absorve potência mecânica
            e a transfere ao entreferro.
            </p>
            <div class="tc-warn" style="color:var(--success,#22eb6c);border-color:var(--success,#22eb6c);">
            Aplicações: geração eólica de indução, freio regenerativo em acionamentos.
            </div>
            """,
        )

    st.write("")

    # Boucherot
    _card(
        "Torque Máximo e Escorregamento Crítico — Teorema de Boucherot",
        f"""
        <p {_P}>
        Derivando $T_e(s)$ em relação a $s$ e igualando a zero, obtém-se o par
        $(T_{{max}},\\, s_{{cr}})$:
        </p>
        {_eq(r"T_{max} = \frac{3\,V_{th}^2}{2\,\omega_s\!\left(R_{th} + \sqrt{R_{th}^2 + (X_{th}+X'_2)^2}\right)}")}
        {_eq(r"s_{cr} = \frac{R'_2}{\sqrt{R_{th}^2 + (X_{th}+X'_2)^2}}")}
        <p {_P}>
        <strong>Teorema de Boucherot:</strong> $T_{{max}}$ <em>não depende de $R'_2$</em>.
        Variar $R'_2$ apenas <strong>desloca</strong> $s_{{cr}}$ sem alterar a amplitude do pico.
        Para obter torque de partida máximo ($T_{{part}} = T_{{max}}$), basta impor $s_{{cr}} = 1$:
        </p>
        {_eq(r"R'_2\big|_{T_{part}=T_{max}} = \sqrt{R_{th}^2 + (X_{th}+X'_2)^2}")}
        <p {_P}>
        Em <strong>motores de rotor bobinado</strong>, resistências externas são inseridas
        nos anéis coletores apenas na partida e depois curto-circuitadas, explorando este princípio.
        </p>
        """,
    )

    st.write("")

    # Efeito de R'₂ na curva
    _card_side(
        "Curvas $T_e \\times n$ — Variação de $R'_2$ (Boucherot na prática)",
        "TR2.png",
        f"""
        <p {_P}>
        $T_{{max}}$ é <strong>invariante</strong> com $R'_2$.
        O que muda é o escorregamento crítico: $s_{{cr}} \\propto R'_2$.
        </p>
        <ul {_LI}>
          <li>$R'_2 \\downarrow$: $s_{{cr}} \\downarrow$ — pico próximo a $n_s$
              $\\Rightarrow$ <span class="tc-up">alta eficiência em regime</span>,
              <span class="tc-down">baixo torque de partida</span>.</li>
          <li>$R'_2 \\uparrow$: $s_{{cr}} \\uparrow$ — pico a baixa rotação
              $\\Rightarrow$ <span class="tc-up">alto torque de partida</span>,
              <span class="tc-down">alto $s_{{nom}}$ e perdas em regime</span>.</li>
        </ul>
        {_eq(r"T_{part} = T_{max} \;\Leftrightarrow\; R'_2 = \sqrt{R_{th}^2 + (X_{th}+X'_2)^2}")}
        """,
        img_right=True,
    )

    st.write("")

    # Gaiola dupla — torque
    _card_side(
        "Gaiola de Esquilo Dupla — Composição do Torque",
        "SCdupla.png",
        f"""
        <p {_P}>
        O torque resultante é a <strong>superposição</strong> dos torques de cada gaiola:
        </p>
        {_eq(r"T_e = T_{ext} + T_{int} = \frac{3}{\omega_s}\!\left(\frac{|V_{ag}|^2 R'_{2e}/s}{|Z'_{2e}|^2} + \frac{|V_{ag}|^2 R'_{2i}/s}{|Z'_{2i}|^2}\right)")}
        <p {_P}>
        <strong>Na partida</strong> ($s=1$, $f_r = f$): o <strong>efeito pelicular</strong>
        força a corrente para a gaiola externa ($R'_{{2e}}$ alto)
        $\\Rightarrow$ alto $T_{{part}}$.
        </p>
        <p {_P}>
        <strong>Em regime</strong> ($s \\ll 1$, $f_r \\approx s\\,f$):
        $X'_{{2i}} \\to 0$ — gaiola interna ($R'_{{2i}}$ baixo) domina
        $\\Rightarrow$ baixo $s_{{nom}}$, alto $\\eta$.
        </p>
        <p {_P}>
        O resultado é uma variação <em>automática e contínua</em> de $R'_2$ efetivo
        durante a aceleração — sem componentes externos, graças ao
        <strong>perfil geométrico das barras do rotor</strong>.
        </p>
        """,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ABA 3 — BALANÇO ENERGÉTICO E FLUXO DE POTÊNCIA
# ─────────────────────────────────────────────────────────────────────────────

def _render_tab_potencia() -> None:
    st.markdown(
        "As potências fluem de forma **encadeada**, com cada estágio dissipando ou convertendo "
        "uma fração determinada por $s$, $R$, $X$ e $\\omega$. "
        "O modo de operação (motor, gerador, frenagem) inverte o sentido do fluxo."
    )

    # Tabela fundamental
    _card(
        "Relações Fundamentais de Potência",
        f"""
        <p {_P}>As identidades abaixo valem em <strong>regime permanente</strong> para qualquer $s$:</p>
        <table style="width:100%;border-collapse:collapse;font-size:.9rem;margin-top:.6rem;">
          <thead>
            <tr style="border-bottom:2px solid #bbb;">
              <th style="text-align:left;padding:.45rem .7rem;">Grandeza</th>
              <th style="text-align:left;padding:.45rem .7rem;">Expressão</th>
              <th style="text-align:left;padding:.45rem .7rem;">Nota</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Potência de entrada</strong> $P_{{in}}$</td>
              <td style="padding:.4rem .7rem;">$3\\,V_1\\,I_1\\cos\\varphi$</td>
              <td style="padding:.4rem .7rem;">Trifásico — terminais do estator</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Perdas no estator</strong> $P_{{cu,1}}$</td>
              <td style="padding:.4rem .7rem;">$3\\,I_1^2\\,R_s$</td>
              <td style="padding:.4rem .7rem;">Joule nos enrolamentos estatóricos</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Perdas no ferro</strong> $P_{{fe}}$</td>
              <td style="padding:.4rem .7rem;">$3\\,V_\\phi^2/R_{{fe}}$</td>
              <td style="padding:.4rem .7rem;">Histerese + Foucault no núcleo</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Potência no entreferro</strong> $P_{{ag}}$</td>
              <td style="padding:.4rem .7rem;">$T_e\\,\\omega_s = P_{{in}} - P_{{cu,1}} - P_{{fe}}$</td>
              <td style="padding:.4rem .7rem;">$\\omega_s = 4\\pi f/p$</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Perdas no rotor</strong> $P_{{cu,2}}$</td>
              <td style="padding:.4rem .7rem;">$s\\,P_{{ag}} = 3\\,I_2'^2\\,R_r$</td>
              <td style="padding:.4rem .7rem;">Fração de $P_{{ag}}$ dissipada no rotor</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Potência mecânica</strong> $P_{{mec}}$</td>
              <td style="padding:.4rem .7rem;">$(1-s)\\,P_{{ag}} = T_e\\,\\omega_r$</td>
              <td style="padding:.4rem .7rem;">$\\omega_r = (1-s)\\,\\omega_s$</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Potência útil</strong> $P_{{out}}$</td>
              <td style="padding:.4rem .7rem;">$P_{{mec}} - P_{{rot}}$</td>
              <td style="padding:.4rem .7rem;">$P_{{rot}}$: atrito + ventilação</td>
            </tr>
            <tr>
              <td style="padding:.4rem .7rem;"><strong>Rendimento</strong> $\\eta$</td>
              <td style="padding:.4rem .7rem;">$P_{{out}}/P_{{in}}$</td>
              <td style="padding:.4rem .7rem;">Máximo quando $P_{{cu,1}} \\approx P_{{fe}}+P_{{rot}}$</td>
            </tr>
          </tbody>
        </table>
        """,
    )

    st.write("")

    # Três modos lado a lado
    c1, c2, c3 = st.columns(3)
    with c1:
        _card(
            "Modo Motor",
            f"""
            {_img("fluxo_P_motor.png")}
            {_eq(r"P_{in} \xrightarrow{-P_{cu,1}} P_{ag} \xrightarrow{-P_{cu,2}} P_{mec} \xrightarrow{-P_{rot}} P_{out}")}
            <p {_P}>
            Relação-chave: $P_{{cu,2}} = s\\,P_{{ag}}$ e $P_{{mec}} = (1-s)P_{{ag}}$.
            A eficiência é maximizada com baixo escorregamento nominal.
            </p>
            """,
        )
    with c2:
        _card(
            "Modo Gerador",
            f"""
            {_img("fluxo_P_gerador.png")}
            {_eq(r"P_{in,mec} \xrightarrow{-P_{rot}} P_{mec} \xrightarrow{-P_{cu,2}} P_{ag} \xrightarrow{-P_{cu,1}} P_{out}")}
            <p {_P}>
            Sentido invertido: potência mecânica entra pelo eixo,
            potência elétrica sai pelos terminais do estator para a rede.
            </p>
            """,
        )
    with c3:
        _card(
            "Modo Frenagem ($s > 1$)",
            f"""
            {_img("fluxo_P_frenagem.png")}
            {_eq(r"P_{ele} + P_{cin} \longrightarrow P_{cu,2}")}
            <p {_P}>
            Energia elétrica da rede <em>e</em> energia cinética do eixo
            convertem-se <strong>integralmente em calor no rotor</strong>.
            </p>
            <div class="tc-warn">
            Operação breve — o rotor pode queimar em segundos.
            $P_{{cu,2}} = s\\,P_{{ag}} > P_{{ag}}$ porque $s > 1$.
            </div>
            """,
        )

    st.write("")

    # Insight qualitativo sobre s
    _card(
        "Interpretação Física do Escorregamento",
        f"""
        <p {_P}>
        O escorregamento $s$ é a variável que <strong>particiona</strong> a potência do entreferro
        entre perdas e produção mecânica:
        </p>
        {_eq(r"P_{ag} = \underbrace{s\,P_{ag}}_{P_{cu,2}\;\text{(calor)}} + \underbrace{(1-s)\,P_{ag}}_{P_{mec}\;\text{(trabalho)}}")}
        <p {_P}>
        Um motor com $s = 0{{,}}05$ (5%) dissipa apenas 5% da potência do entreferro no rotor —
        o restante 95% é convertido em trabalho mecânico. Por isso <strong>motores eficientes
        operam com baixo escorregamento</strong>.
        </p>
        <p {_P}>
        Na frenagem ($s > 1$), a equação acima exige $P_{{cu,2}} > P_{{ag}}$, o que só é possível
        porque a <strong>energia cinética do eixo</strong> alimenta adicionalmente o rotor.
        </p>
        """,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ABA DINÂMICA DE OPERAÇÃO
# ─────────────────────────────────────────────────────────────────────────────

def _render_tab_dinamica_operacao() -> None:
    st.markdown(
        "A compreensão da dinâmica de operação do motor de indução trifásico exige "
        "a análise de cada fase do ciclo eletromecânico — da energização inicial até "
        "a parada completa. Esta aba percorre esses estados em ordem cronológica, "
        "relacionando os fenômenos físicos às equações que os governam."
    )

    # ── pré-calcula curva T×n uma única vez ───────────────────────────────────
    s_mot  = np.linspace(0.002, 1.0, 600)
    T_mot  = np.array([_torque_ref(s) for s in s_mot])
    n_mot  = _ns_REF * (1 - s_mot)
    idx_pk = int(np.argmax(T_mot))
    T_load = T_mot[idx_pk] * 0.45
    idx_ss = next((i for i in range(idx_pk, len(T_mot) - 1)
                   if T_mot[i] >= T_load >= T_mot[i + 1]), len(T_mot) - 1)

    # ── helpers de estilo (tema claro) ────────────────────────────────────────
    def _style_ax(a):
        a.set_facecolor("white")
        for sp in a.spines.values():
            sp.set_edgecolor("#cccccc")
        a.tick_params(colors="#333333")
        a.grid(True, alpha=0.35, linestyle=":", color="#bbbbbb")

    # ═══════════════════════════════════════════════════════════════════════
    # CARD 1 — PARTIDA, ACELERAÇÃO E REGIME PERMANENTE  (com gráfico T×n)
    # ═══════════════════════════════════════════════════════════════════════
    fig1, ax = plt.subplots(figsize=(8, 4.2))
    fig1.patch.set_facecolor("white")
    _style_ax(ax)

    ax.plot(n_mot, T_mot, color="#1565c0", linewidth=2.5, label="Curva $T \\times n$")
    ax.axhline(T_load, color="#555555", linestyle="--", linewidth=1.4, label="Carga $T_L$")
    ax.axvline(_ns_REF, color="#aaaaaa", linestyle=":", linewidth=1)
    ax.text(_ns_REF + 10, T_mot.max() * 0.04, "$n_s$", color="#888", fontsize=9)

    ax.scatter([n_mot[-1]], [T_mot[-1]], color="#e65100", s=90, zorder=5)
    ax.annotate("Partida  $s=1$\n$I_p \\approx 6\\!-\\!8\\,I_n$",
                xy=(n_mot[-1], T_mot[-1]),
                xytext=(n_mot[-1] - 370, T_mot[-1] + T_mot.max() * 0.09),
                color="#e65100", fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color="#e65100", lw=1.2))

    ax.scatter([n_mot[idx_pk]], [T_mot[idx_pk]], color="#c62828", s=90, zorder=5)
    ax.annotate("Torque Máximo\n(Pull-out)",
                xy=(n_mot[idx_pk], T_mot[idx_pk]),
                xytext=(n_mot[idx_pk] - 400, T_mot[idx_pk] - T_mot.max() * 0.14),
                color="#c62828", fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color="#c62828", lw=1.2))

    ax.scatter([n_mot[idx_ss]], [T_load], color="#2e7d32", s=90, zorder=5)
    ax.annotate("Regime\nPermanente",
                xy=(n_mot[idx_ss], T_load),
                xytext=(n_mot[idx_ss] + 35, T_load + T_mot.max() * 0.13),
                color="#2e7d32", fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color="#2e7d32", lw=1.2))

    ax.annotate("", xy=(n_mot[idx_ss] - 25, T_load + 1),
                xytext=(n_mot[-1] - 10, T_mot[-1] + 1),
                arrowprops=dict(arrowstyle="->", color="#999999", lw=1.5,
                                connectionstyle="arc3,rad=-0.25"))

    ax.set_xlabel("Velocidade (rpm)", fontsize=10, fontweight="bold", color="#222")
    ax.set_ylabel("Torque (N·m)",     fontsize=10, fontweight="bold", color="#222")
    ax.set_title("Trajetória de Operação — Partida até Regime Permanente",
                 fontsize=11, fontweight="bold", color="#111")
    ax.legend(fontsize=9, facecolor="white", edgecolor="#cccccc")
    ax.set_xlim(0, _ns_REF * 1.04)
    ax.set_ylim(0, T_mot.max() * 1.2)
    fig1.tight_layout()
    _chart1 = _fig_to_b64(fig1)

    _card(
        "Partida, Aceleração e Regime Permanente",
        f"""
        <p {_P}>
        No instante em que o estator é conectado à rede trifásica, as três correntes
        defasadas de 120° entre si estabelecem um <strong>campo magnético girante</strong>
        que rotaciona à velocidade síncrona $n_s$:
        </p>
        {_eq(r"n_s = \frac{120\,f_e}{p} \quad \text{(RPM)}")}
        <p {_P}>
        Com o rotor em repouso ($s = 1$), a impedância rotórica é predominantemente
        reativa, resultando em uma corrente de partida $I_p$ entre 6 e 8 vezes a nominal
        e em um torque inicial relativamente modesto — explicado pelo baixo fator de
        potência imposto pela reatância de dispersão:
        </p>
        {_eq(r"I_p \approx (6 \text{ a } 8)\, I_n \quad (s = 1)")}
        <p {_P}>
        À medida que o rotor acelera, o escorregamento $s$ diminui e a frequência das
        correntes rotóricas $f_r = s \\cdot f_e$ cai. A redução da reatância rotórica
        melhora o fator de potência e eleva o torque até o <strong>Torque Máximo</strong>
        (Pull-out) no escorregamento crítico $s_{{cr}}$. Para $s < s_{{cr}}$, o torque
        decresce até o ponto de equilíbrio com a carga — o <strong>regime permanente</strong>
        — onde obrigatoriamente $n < n_s$, pois sem escorregamento não há indução:
        </p>
        {_eq(r"s = \frac{n_s - n}{n_s} > 0 \quad \Longleftrightarrow \quad n < n_s")}
        <div style="margin:1.2rem 0 0.4rem 0;">{_chart1}</div>
        """,
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CARD 2 — DINÂMICA DE CARGA  (com gráfico de transitório)
    # ═══════════════════════════════════════════════════════════════════════
    _t   = np.linspace(0.0, 5.0, 1000)
    t_on = 2.0
    n0, n1 = 1795.0, 1762.0
    tau_n  = 0.35
    Te0, Te1, Te_pk = 8.0, 42.0, 68.0
    tau_Te = 0.12

    _n  = np.where(_t < t_on, n0,
                   n1 + (n0 - n1) * np.exp(-(_t - t_on) / tau_n))
    _Te = np.where(_t < t_on, Te0,
                   Te1 + (Te_pk - Te1) * np.exp(-(_t - t_on) / tau_Te) *
                   np.sin(np.pi * (_t - t_on) / (3 * tau_Te)).clip(0))
    _Te = np.where(_t < t_on, Te0, _Te)

    fig2, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4.8), sharex=True)
    fig2.patch.set_facecolor("white")
    for a in (ax1, ax2):
        _style_ax(a)
        a.axvline(t_on, color="#e65100", linestyle="--", linewidth=1.2, alpha=0.8)

    ax1.plot(_t, _n, color="#1565c0", linewidth=2)
    ax1.set_ylabel("Velocidade (rpm)", fontsize=9, fontweight="bold", color="#222")
    ax1.annotate("Carga\naplicada", xy=(t_on, n0), xytext=(t_on + 0.35, n0 + 3),
                 color="#e65100", fontsize=8,
                 arrowprops=dict(arrowstyle="->", color="#e65100", lw=1.1))
    ax1.annotate(f"$\\Delta n$ = {n0 - n1:.0f} rpm",
                 xy=((t_on + 5) / 2, (n0 + n1) / 2), color="#555", fontsize=8, ha="center")

    ax2.plot(_t, _Te, color="#c62828", linewidth=2)
    ax2.set_ylabel("Torque $T_e$ (N·m)", fontsize=9, fontweight="bold", color="#222")
    ax2.set_xlabel("Tempo (s)",           fontsize=9, fontweight="bold", color="#222")

    fig2.suptitle("Resposta Transitória — Aplicação Brusca de Carga",
                  fontsize=11, fontweight="bold", color="#111")
    fig2.tight_layout()
    _chart2 = _fig_to_b64(fig2)

    _card(
        "Dinâmica de Carga — Aplicação e Alívio Bruscos",
        f"""
        <p {_P}>
        Quando uma carga é aplicada bruscamente ao eixo, o torque resistente supera
        momentaneamente $T_{{em}}$ e o rotor desacelera. O aumento do escorregamento
        eleva $f_r = s \\cdot f_e$, a corrente rotórica $I_2$ e, por acoplamento
        magnético, a corrente estatórica $I_1$. O torque cresce até um novo equilíbrio
        em velocidade ligeiramente menor, governado pela equação de movimento:
        </p>
        {_eq(r"\frac{d\omega_r}{dt} = \frac{p}{2J}(T_{em} - T_{load}) - \frac{B}{J}\,\omega_r")}
        <p {_P}>
        No alívio de carga, o processo se inverte: $T_{{em}}$ supera o resistente,
        o rotor acelera e o escorregamento reduz-se a valores muito pequenos
        ($s \\approx 0{{,}}005$ a $0{{,}}02$), suficientes apenas para suprir as
        perdas mecânicas e no ferro. O gráfico abaixo ilustra o afundamento de
        velocidade $\\Delta n$ e o pico transitório de torque ao aplicar carga:
        </p>
        <div style="margin:1.2rem 0 0.4rem 0;">{_chart2}</div>
        """,
    )

    # ═══════════════════════════════════════════════════════════════════════
    # CARD 3 — FRENAGEM E PARADA  (com gráfico comparativo)
    # ═══════════════════════════════════════════════════════════════════════
    _tb   = np.linspace(0.0, 2.5, 800)
    n_nom = 1760.0
    n_plug  = np.maximum(0.0, n_nom * (1 - _tb / 0.40))
    n_regen = n_nom * np.exp(-_tb / 0.55)
    n_dc    = n_nom * np.exp(-_tb / 1.10)

    fig3, ax = plt.subplots(figsize=(8, 4.0))
    fig3.patch.set_facecolor("white")
    _style_ax(ax)

    ax.plot(_tb, n_plug,  color="#c62828", linewidth=2.2, label="Contracorrente (Plugging)")
    ax.plot(_tb, n_regen, color="#e65100", linewidth=2.2, linestyle="--", label="Regenerativa")
    ax.plot(_tb, n_dc,    color="#1565c0", linewidth=2.2, linestyle=":",  label="Injeção CC")
    ax.axhline(0, color="#aaaaaa", linewidth=0.9)

    ax.set_xlabel("Tempo desde o início da frenagem (s)", fontsize=10, fontweight="bold", color="#222")
    ax.set_ylabel("Velocidade (rpm)",                      fontsize=10, fontweight="bold", color="#222")
    ax.set_title("Comparação dos Métodos de Frenagem — $n\\,(t)$",
                 fontsize=11, fontweight="bold", color="#111")
    ax.legend(fontsize=9.5, facecolor="white", edgecolor="#cccccc")
    ax.set_xlim(0, 2.5)
    ax.set_ylim(-30, n_nom * 1.06)
    fig3.tight_layout()
    _chart3 = _fig_to_b64(fig3)

    _card(
        "Frenagem e Parada — Métodos Eletromecânicos",
        f"""
        <p {_P}>
        A parada controlada de um motor de indução pode ser obtida por três métodos com
        princípios físicos distintos. Cada um atua em uma região diferente da curva
        $T \\times s$ e impõe condições específicas de corrente, temperatura e precisão
        de parada.
        </p>

        <hr style="border:none;border-top:1px solid #ddd;margin:.8rem 0;">

        <p {_P}><strong style="font-size:1rem;">1 — Frenagem Regenerativa</strong>
        &nbsp;<em>(s negativo)</em></p>
        <p {_P}>
        <strong>Princípio:</strong> a velocidade do rotor é forçada acima de $n_s$ —
        por torque mecânico externo (turbina, gravidade) ou redução brusca da frequência
        de referência em um inversor. O escorregamento torna-se negativo e a máquina
        passa a devolver potência à rede:
        </p>
        {_eq(r"s < 0 \;\Rightarrow\; P_{ag} < 0 \;\Rightarrow\; \text{energia devolvida \`{a} rede}")}
        <p {_P}>
        <strong>Vantagem:</strong> método mais eficiente — a energia cinética é
        convertida em energia elétrica útil em vez de ser dissipada como calor.
        Desaceleração suave e controlável; sem risco de inversão de movimento.<br>
        <strong>Limitação:</strong> exige rede ou barramento CC capaz de absorver a
        energia regenerada. Não se aplica a acionamentos diretos sem inversor.
        </p>

        <hr style="border:none;border-top:1px solid #ddd;margin:.8rem 0;">

        <p {_P}><strong style="font-size:1rem;">2 — Frenagem por Contracorrente
        (Plugging)</strong> &nbsp;<em>(s maior que 1)</em></p>
        <p {_P}>
        <strong>Princípio:</strong> inverte-se a sequência de fases do estator com o
        motor ainda girando. O campo girante passa a rotar em sentido contrário ao rotor,
        criando escorregamento acima de 1. O torque eletromagnético opõe-se ao movimento
        com intensidade máxima, desacelerando o rotor em poucos ciclos:
        </p>
        {_eq(r"s = \frac{n_s - n}{n_s} > 1 \quad (n_s \text{ invertida, } n \text{ positiva})")}
        <p {_P}>
        <strong>Vantagem:</strong> método mais rápido de parada entre os três.<br>
        <strong>Limitação crítica:</strong> as perdas Joule no rotor equivalem a
        $s \\cdot P_{{ag}}$, com $s > 1$, superando a potência de entreferro — aquecimento
        severo, operação limitada a segundos. Uma chave de corte deve atuar exatamente
        em $n = 0$; caso contrário, o motor inverte o sentido de rotação.
        </p>

        <hr style="border:none;border-top:1px solid #ddd;margin:.8rem 0;">

        <p {_P}><strong style="font-size:1rem;">3 — Injeção de Corrente Contínua
        (Frenagem CC)</strong></p>
        <p {_P}>
        <strong>Princípio:</strong> a alimentação trifásica é desconectada e aplica-se
        tensão CC a dois terminais do estator. A corrente contínua cria um campo
        magnético estacionário no entreferro. O rotor em movimento corta esse campo,
        induzindo correntes rotóricas que geram um torque de frenagem proporcional
        à velocidade — que se anula naturalmente em repouso:
        </p>
        {_eq(r"T_{brake} \propto \omega_r \;\xrightarrow{\;\omega_r \to 0\;}\; 0")}
        <p {_P}>
        <strong>Vantagem:</strong> parada suave; o torque decai a zero em $\\omega_r = 0$
        sem risco de inversão e sem necessidade de chave de corte. O calor é
        dissipado no estator, permitindo ciclos mais frequentes que o plugging.<br>
        <strong>Limitação:</strong> desaceleração mais lenta. Requer retificador e
        controle da corrente CC injetada.
        </p>

        <hr style="border:none;border-top:1px solid #ddd;margin:.8rem 0;">

        <p {_P}>O gráfico compara a evolução de $n(t)$ nos três métodos a partir do
        mesmo ponto de regime permanente:</p>
        <div style="margin:.6rem 0 .4rem 0;">{_chart3}</div>
        """,
    )


# ABA 4 — GUIA DE SENSIBILIDADE DE PARÂMETROS
# ─────────────────────────────────────────────────────────────────────────────

_PARAMS_ELETRICOS = [
    {
        "nome": "$V_l$ — Tensão de Linha (RMS)",
        "desc": (
            "Define a amplitude do campo magnético girante no estator. "
            "Determina o fluxo no entreferro: $\\Phi \\propto V_l/f$. "
            "É a grandeza com maior impacto no torque disponível."
        ),
        "up": (
            "O torque máximo cresce com $V_l^2$: $T_{{max}} \\propto V_{{th}}^2 \\propto V_l^2$. "
            "A corrente de partida também aumenta significativamente."
        ),
        "down": (
            "O torque de partida cai — pode tornar-se insuficiente para vencer a inércia da carga, "
            "impedindo a partida (stall na aceleração)."
        ),
        "warn": (
            "Sobretensão ($> 110\\%\\,V_n$) provoca <strong>saturação do núcleo</strong> e "
            "degradação térmica do isolamento. "
            "Subtensão severa ($< 85\\%\\,V_n$) pode causar <strong>travamento (stall)</strong> sob carga nominal."
        ),
    },
    {
        "nome": "$f$ — Frequência da Rede",
        "desc": (
            "Determina a velocidade síncrona: $n_s = 120\\,f/p\\;$(rpm). "
            "As reatâncias escalam proporcionalmente: $X = 2\\pi f L$."
        ),
        "up": (
            "Aumenta $n_s$, $X_m$, $X_{{ls}}$, $X_{{lr}}$. "
            "Com $V_l$ constante a relação $V/f$ cai, reduzindo o fluxo e o torque máximo."
        ),
        "down": (
            "Reduz a velocidade de operação. Com $V_l$ constante a relação $V/f$ cresce, "
            "levando o núcleo à <strong>saturação magnética</strong>."
        ),
        "warn": (
            "Operar fora da frequência nominal sem controle $V/f = $ const. compromete "
            "o fluxo, a eficiência e a integridade térmica da máquina."
        ),
    },
    {
        "nome": "$R_s$ — Resistência do Estator",
        "desc": (
            "Representa as perdas Joule nos enrolamentos estatóricos: $P_{{cu,1}} = 3I_1^2 R_s$. "
            "Provoca queda de tensão interna, reduzindo a tensão efetiva no entreferro."
        ),
        "up": (
            "Aumenta a dissipação térmica e reduz $T_{{max}}$, "
            "pois $R_{{th}} \\uparrow$ eleva o denominador da expressão de Boucherot."
        ),
        "down": (
            "Minimiza perdas internas e melhora o rendimento. "
            "Em valores extremos, aproxima o modelo de um transformador ideal no primário."
        ),
        "warn": (
            "$R_s$ excessivo (enrolamentos danificados ou sobreaquecidos) causa "
            "<strong>sobreaquecimento progressivo</strong>. "
            "Valores muito próximos de zero podem gerar <strong>instabilidade numérica</strong> no integrador."
        ),
    },
    {
        "nome": "$R_r$ — Resistência do Rotor",
        "desc": (
            "Parâmetro determinante da curva de torque. "
            "Define o escorregamento crítico: $s_{{cr}} = R_r / \\sqrt{{R_{{th}}^2 + X_{{eq}}^2}}$."
        ),
        "up": (
            "$s_{{cr}}$ aumenta — pico de torque desloca-se para rotações menores. "
            "O torque de partida cresce até o limite $T_{{max}}$ (quando $s_{{cr}} = 1$)."
        ),
        "down": (
            "Melhora a eficiência ($s_{{nom}}$ cai) e reduz o escorregamento em regime. "
            "O torque de partida diminui proporcionalmente."
        ),
        "warn": (
            "$R_r$ muito alto indica <strong>barras fraturadas</strong> — provoca escorregamento excessivo e vibração. "
            "Valores nulos causam <strong>singularidade matemática</strong> nas equações do rotor."
        ),
    },
    {
        "nome": "$X_m$ — Reatância de Magnetização",
        "desc": (
            "Representa o ramo de magnetização (<em>shunt</em>) do circuito: "
            "caminho do fluxo principal pelo núcleo. "
            "Relaciona-se com a indutância mútua: $X_m = 2\\pi f L_m$."
        ),
        "up": (
            "Reduz a corrente de magnetização em vazio $I_m = V_1/X_m$, "
            "melhorando o fator de potência em regime."
        ),
        "down": (
            "Aumenta $I_m$ — maior corrente reativa necessária para excitar o núcleo, "
            "piorando o fator de potência."
        ),
        "warn": (
            "$X_m$ baixo indica núcleo de má qualidade ou em <strong>saturação magnética</strong>. "
            "Valores excessivamente baixos podem causar <strong>divergência numérica</strong> no integrador."
        ),
    },
    {
        "nome": "$R_{fe}$ — Resistência de Perdas no Ferro",
        "desc": (
            "Modela histerese e correntes de Foucault em paralelo com $X_m$. "
            "Perdas no ferro: $P_{{fe}} = 3\\,V_\\phi^2 / R_{{fe}}$. "
            "Valores típicos: $100$–$2000\\;\\Omega$ para máquinas de médio porte."
        ),
        "up": (
            "$P_{{fe}}$ menor. O motor opera com maior eficiência, "
            "especialmente em regimes de baixa carga onde as perdas no núcleo dominam."
        ),
        "down": (
            "$P_{{fe}}$ maior. O rendimento cai, especialmente em operação a vazio. "
            "Pode indicar lâminas de baixa qualidade ou operação a frequência elevada."
        ),
        "warn": (
            "$R_{{fe}}$ é usado <strong>apenas no cálculo estático</strong> de potências e rendimento — "
            "não influencia o ODE nem a dinâmica simulada. "
            "Valores $< 50\\;\\Omega$ indicam núcleo de baixíssima qualidade."
        ),
    },
    {
        "nome": "$X_{ls}$ e $X_{lr}$ — Reatâncias de Dispersão",
        "desc": (
            "Modelam fluxos que não enlaçam ambos os enrolamentos (dispersão). "
            "Definem a reatância de curtocircuito: $X_{{cc}} = X_{{ls}} + X_{{lr}}$, "
            "que limita o torque máximo e a corrente de partida."
        ),
        "up": (
            "Aumenta $X_{{cc}}$, reduzindo $T_{{max}} \\propto 1/(X_{{th}}+X_{{lr}})$. "
            "Corrente de partida cai, facilitando a proteção."
        ),
        "down": (
            "$T_{{max}}$ sobe e correntes de partida aumentam. "
            "Torna o motor mais sensível a transitórios de carga e variações de tensão."
        ),
        "warn": (
            "Dispersão muito baixa resulta em <strong>picos de corrente perigosos ao isolamento</strong>. "
            "Dispersão excessiva pode <strong>impedir a partida</strong> sob carga nominal."
        ),
    },
]

_PARAMS_MECANICOS = [
    {
        "nome": "$p$ — Número de Polos",
        "desc": (
            "Define a velocidade síncrona: $n_s = 120\\,f/p\\;$(rpm), "
            "ou equivalentemente $\\omega_s = 4\\pi f/p\\;$(rad/s)."
        ),
        "up": (
            "Reduz $n_s$. Para a mesma potência $P = T\\,\\omega$, "
            "o torque nominal deve ser proporcionalmente maior."
        ),
        "down": (
            "Aumenta $n_s$ e $\\omega_s$. "
            "O torque nominal diminui para a mesma potência de saída."
        ),
        "warn": "$p$ deve ser sempre inteiro par. Valores ímpares invalidam o modelo físico.",
    },
    {
        "nome": "$J$ — Momento de Inércia",
        "desc": (
            "Governa a dinâmica de aceleração via equação mecânica: "
            "$J\\,\\dot{\\omega}_r = T_e - T_L - B\\,\\omega_r$. "
            "Inclui o rotor e a carga acoplada ao eixo."
        ),
        "up": (
            "Aceleração mais lenta — transitórios amortecidos e tempo de partida maior. "
            "Reduz a sensibilidade a variações abruptas de carga."
        ),
        "down": (
            "Resposta dinâmica acelerada — o rotor reage quase instantaneamente a variações de $T_e$. "
            "Útil para servoacionamentos, mas exige proteção contra sobrecargas rápidas."
        ),
        "warn": (
            "$J$ muito baixo pode gerar <strong>oscilações numéricas ruidosas</strong> no ODE. "
            "$J$ muito alto pode exigir $t_{{max}}$ muito grande para atingir o regime permanente."
        ),
    },
    {
        "nome": "$B$ — Coeficiente de Atrito Viscoso",
        "desc": (
            "Modela perdas mecânicas proporcionais à velocidade: "
            "$T_{{atrito}} = B\\,\\omega_r$ (mancais e ventilação)."
        ),
        "up": (
            "Aumenta o amortecimento do sistema e a dissipação mecânica. "
            "O ponto de equilíbrio em regime é deslocado para menor rotação."
        ),
        "down": (
            "Reduz perdas mecânicas. "
            "Se $B = 0$, o amortecimento depende exclusivamente da carga externa $T_L$."
        ),
        "warn": (
            "Valores elevados simulam <strong>falha catastrófica em rolamentos</strong> e "
            "podem impedir que o motor atinja a rotação nominal."
        ),
    },
]


def _render_tab_sensibilidade() -> None:
    st.markdown(
        "**Manual de calibração** do simulador: como cada parâmetro afeta qualitativamente "
        "o comportamento da máquina. Útil para diagnóstico, ajuste de modelo e estudo de falhas."
    )

    st.write("")
    st.markdown("### Parâmetros Elétricos")
    for item in _PARAMS_ELETRICOS:
        st.markdown(
            f'<div class="tcard">'
            f'<h4>{item["nome"]}</h4>'
            f'<p {_P}>{item["desc"]}</p>'
            f'<ul {_LI}>'
            f'<li><span class="tc-up"><strong>Se aumentar:</strong></span>&nbsp; {item["up"]}</li>'
            f'<li><span class="tc-down"><strong>Se diminuir:</strong></span>&nbsp; {item["down"]}</li>'
            f'</ul>'
            f'<div class="tc-warn" style="margin-top:.6rem;"><strong>Atenção — calibrações extremas:</strong> {item["warn"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("### Parâmetros Mecânicos")
    for item in _PARAMS_MECANICOS:
        st.markdown(
            f'<div class="tcard">'
            f'<h4>{item["nome"]}</h4>'
            f'<p {_P}>{item["desc"]}</p>'
            f'<ul {_LI}>'
            f'<li><span class="tc-up"><strong>Se aumentar:</strong></span>&nbsp; {item["up"]}</li>'
            f'<li><span class="tc-down"><strong>Se diminuir:</strong></span>&nbsp; {item["down"]}</li>'
            f'</ul>'
            f'<div class="tc-warn" style="margin-top:.6rem;"><strong>Atenção — calibrações extremas:</strong> {item["warn"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# ABA 5 — CONFIGURAÇÕES DE SIMULAÇÃO E ALERTAS
# ─────────────────────────────────────────────────────────────────────────────

def _render_tab_config() -> None:
    st.markdown(
        "Diretrizes para escolha do **tempo de simulação** $t_{{max}}$ e do "
        "**passo de integração** $h$, com critérios de estabilidade numérica "
        "e alertas para cenários que podem comprometer a simulação."
    )

    st.write("")

    # tmax
    _card(
        "Tempo de Simulação — $t_{max}$",
        f"""
        <p {_P}>
        Define o horizonte temporal da integração numérica.
        Deve ser suficiente para conter o <strong>transitório completo de partida</strong>
        e, se necessário, a estabilização em regime permanente.
        </p>
        <p {_P}><strong>Referência prática:</strong></p>
        <ul {_LI}>
          <li>Transitório de partida típico: $t_{{part}} \\approx 3$–$5 \\times \\tau_m$,
              onde $\\tau_m = J\\,\\omega_s / T_{{e,nom}}$.</li>
          <li>Regime permanente: observar pelo menos $5$–$10$ ciclos elétricos após
              $t_{{part}}$ para calcular valores RMS confiáveis.</li>
          <li>Experimentos com pulso de carga: incluir margem após $t_{{off}}$
              para visualizar o retorno ao regime.</li>
        </ul>
        <ul {_LI}>
          <li><span class="tc-up"><strong>$t_{{max}}$ maior:</strong></span>
              Permite observar fenômenos de longo prazo e verificar estabilidade.
              Aumenta o custo computacional linearmente.</li>
          <li><span class="tc-down"><strong>$t_{{max}}$ menor:</strong></span>
              Processamento rápido, mas arrisca truncar a análise antes da estabilização
              — os valores RMS e o torque médio ficam incorretos.</li>
        </ul>
        <div class="tc-warn">
        <strong>Atenção:</strong> $t_{{max}}$ muito grande combinado com $h$ muito pequeno
        pode causar <strong>estouro de memória</strong> no navegador.
        Verifique: $N = t_{{max}}/h$ pontos armazenados.
        </div>
        """,
    )

    st.write("")

    # h
    _card(
        "Passo de Integração — $h$",
        f"""
        <p {_P}>
        Discretização temporal para o solver (<strong>LSODA / scipy.odeint</strong>).
        O passo controla precisão numérica e estabilidade da integração.
        </p>
        <p {_P}><strong>Critério de estabilidade numérica:</strong></p>
        {_eq(r"h \;\leq\; \frac{1}{20\,f}")}
        <p {_P}>
        Este critério garante pelo menos <strong>20 pontos por ciclo elétrico</strong>,
        suficientes para integrar a frequência fundamental sem aliasing numérico.
        </p>
        <table style="width:100%;border-collapse:collapse;font-size:.9rem;margin-top:.5rem;">
          <thead>
            <tr style="border-bottom:2px solid #bbb;">
              <th style="padding:.4rem .7rem;text-align:left;">Frequência $f$</th>
              <th style="padding:.4rem .7rem;text-align:left;">$h_{{max}}$ recomendado</th>
              <th style="padding:.4rem .7rem;text-align:left;">Pontos/ciclo</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;">50 Hz</td>
              <td style="padding:.4rem .7rem;">$1{{,}}00\\;$ms</td>
              <td style="padding:.4rem .7rem;">20</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;">60 Hz</td>
              <td style="padding:.4rem .7rem;">$0{{,}}83\\;$ms</td>
              <td style="padding:.4rem .7rem;">20</td>
            </tr>
            <tr>
              <td style="padding:.4rem .7rem;">60 Hz (alta fidelidade)</td>
              <td style="padding:.4rem .7rem;">$0{{,}}20\\;$ms</td>
              <td style="padding:.4rem .7rem;">83</td>
            </tr>
          </tbody>
        </table>
        <ul {_LI} style="margin-top:.7rem;">
          <li><span class="tc-up"><strong>$h$ maior (passo grosso):</strong></span>
              Simulação rápida, mas com risco de imprecisão nas correntes de partida
              e possível divergência numérica.</li>
          <li><span class="tc-down"><strong>$h$ menor (passo fino):</strong></span>
              Alta fidelidade e estabilidade — indicado para análise de harmônicos
              e comparação com dados experimentais.</li>
        </ul>
        <div class="tc-warn">
        <strong>Atenção:</strong> para $f = 60\\;$Hz, passos $h > 1\\;$ms costumam
        causar <strong>divergência do integrador</strong> — as correntes crescem
        indefinidamente nos primeiros ciclos de partida.
        </div>
        """,
    )

    st.write("")

    # Alertas de calibrações extremas
    _card(
        "Alertas de Calibração — Cenários Críticos",
        f"""
        <p {_P}>
        As combinações de parâmetros abaixo podem comprometer a validade física
        da simulação ou causar falha numérica:
        </p>
        <table style="width:100%;border-collapse:collapse;font-size:.9rem;margin-top:.5rem;">
          <thead>
            <tr style="border-bottom:2px solid #bbb;">
              <th style="padding:.4rem .7rem;text-align:left;">Cenário</th>
              <th style="padding:.4rem .7rem;text-align:left;">Condição</th>
              <th style="padding:.4rem .7rem;text-align:left;">Risco</th>
            </tr>
          </thead>
          <tbody>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Saturação magnética</strong></td>
              <td style="padding:.4rem .7rem;">$V_l/f \\gg (V_l/f)_{{nom}}$ ou $X_m$ muito baixo</td>
              <td style="padding:.4rem .7rem;">
                Fluxo sai da região linear — $L_m$ cai, modelo dq deixa de ser válido.
                Sintoma: corrente de magnetização excessiva.
              </td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Travamento (Stall)</strong></td>
              <td style="padding:.4rem .7rem;">$T_L > T_{{max}}$ ou $V_l < 85\\%\\,V_n$</td>
              <td style="padding:.4rem .7rem;">
                Motor não acelera — fica preso na região instável da curva $T_e \\times n$.
                Corrente permanece elevada e o rotor superaquece.
              </td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Divergência numérica</strong></td>
              <td style="padding:.4rem .7rem;">$h > 1/(20f)$, $R_s \\approx 0$ ou $X_m \\approx 0$</td>
              <td style="padding:.4rem .7rem;">
                Correntes crescem sem limite nos primeiros ciclos.
                O simulador exibe valores absurdos (NaN, $\\infty$).
              </td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
              <td style="padding:.4rem .7rem;"><strong>Estouro de memória</strong></td>
              <td style="padding:.4rem .7rem;">$N = t_{{max}}/h > 5 \\times 10^6$ pontos</td>
              <td style="padding:.4rem .7rem;">
                Alocação excessiva de arrays NumPy — lentidão extrema ou travamento do navegador.
              </td>
            </tr>
            <tr>
              <td style="padding:.4rem .7rem;"><strong>Regime não atingido</strong></td>
              <td style="padding:.4rem .7rem;">$t_{{max}} < 3\\,\\tau_m$</td>
              <td style="padding:.4rem .7rem;">
                Os valores RMS e de torque médio são calculados sobre dados transitórios —
                resultados de regime incorretos sem aviso explícito.
              </td>
            </tr>
          </tbody>
        </table>
        """,
    )

    st.write("")

    # Guia rápido
    _card(
        "Guia Rápido de Configuração",
        f"""
        <p {_P}><strong>Passo a passo para uma simulação confiável:</strong></p>
        <ol style="font-size:.92rem;line-height:2.0;padding-left:1.4rem;">
          <li>Calcule $\\tau_m \\approx J\\,\\omega_s / T_{{e,nom}}$ e defina $t_{{max}} \\geq 5\\,\\tau_m$.</li>
          <li>Escolha $h \\leq 1/(20f)$ — para 60 Hz use $h = 0{{,}}5\\;$ms como padrão seguro.</li>
          <li>Verifique que $T_L < T_{{max}}$ antes de simular (evita stall).</li>
          <li>Confirme $V_l/f$ próximo ao valor nominal (evita saturação).</li>
          <li>Se a simulação divergir, reduza $h$ pela metade e repita.</li>
          <li>Se o regime não aparecer nos gráficos, duplique $t_{{max}}$.</li>
        </ol>
        """,
    )


# ─────────────────────────────────────────────────────────────────────────────
# RENDER PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def render_theory_tab() -> None:
    _inject_mathjax()

    st.markdown(
        "Fundamentos físicos da máquina de indução trifásica — "
        "selecione uma aba para explorar o tema desejado."
    )

    tab1, tab2, tab3, tab4, tab5= st.tabs([
        "1 - Modelagem e Circuitos",
        "2 - Dinâmica e Torque",
        "3 - Balanço Energético",
        "4 - Sensibilidade de Parâmetros",
        "5 - Configurações e Alertas"
        #"6 - Dinâmica de Operação",
    ])

    with tab1:
        st.markdown("## Modelagem e Circuitos Equivalentes")
        _render_tab_circuitos()

    with tab2:
        st.markdown("## Comportamento Dinâmico e Torque")
        _render_tab_dinamica()

    with tab3:
        st.markdown("## Balanço Energético e Fluxo de Potência")
        _render_tab_potencia()

    with tab4:
        st.markdown("## Guia de Sensibilidade de Parâmetros")
        _render_tab_sensibilidade()

    with tab5:
        st.markdown("## Configurações de Simulação e Alertas")
        _render_tab_config()

    #with tab6:
      #  st.markdown("## Dinâmica de Operação")
      #  _render_tab_dinamica_operacao()
