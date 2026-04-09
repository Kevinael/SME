# -*- coding: utf-8 -*-
"""
curva_tn.py — Curva T×n e Fluxo de Potência (MIT)

Modelo: circuito equivalente completo com impedância complexa.
Cobre as 3 regiões: motor (0<s≤1), gerador (s<0), frenagem (s>1).
"""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly_charts import _plot_theme


# ── Mapeamento dos parâmetros da máquina para o circuito ─────────────────────
#   V1     = mp.Vl                 tensão de fase RMS (simulação aplica Va_rms = Vl por enrolamento)
#   R1     = mp.Rs                resistência do estator
#   X1     = mp.Xls_a             reatância de dispersão do estator (wb·Lls)
#   R2     = mp.Rr                resistência do rotor referida ao estator
#   X2     = mp.Xlr_a             reatância de dispersão do rotor (wb·Llr)
#   Xm     = mp.wb * mp.Lm        reatância de magnetização na frequência de operação
#   ws_mec = mp.wb * 2 / mp.p    velocidade síncrona mecânica (rad/s)


def _extract_params(mp):
    """Extrai os parâmetros do circuito a partir de MachineParams.

    V1 = mp.Vl: tensão de fase RMS aplicada por enrolamento (igual à simulação,
    que aplica Va = sqrt(2)*Vl*sin(θ) → Va_rms = Vl por fase).
    """
    V1     = mp.Vl
    R1     = mp.Rs
    X1     = mp.Xls_a
    R2     = mp.Rr
    X2     = mp.Xlr_a
    Xm     = mp.wb * mp.Lm
    ws_mec = mp.wb * 2.0 / mp.p
    ns     = mp.n_sync
    return V1, R1, X1, R2, X2, Xm, ws_mec, ns


def _torque_array(s_arr: np.ndarray, V1, R1, X1, R2, X2, Xm, ws_mec) -> np.ndarray:
    """Calcula torque eletromagnético para um array de escorregamentos (vetorizado)."""
    # substitui s=0 por valor pequeno para evitar divisão por zero
    s = np.where(s_arr == 0.0, 1e-9, s_arr)

    Z2  = (R2 / s) + 1j * X2
    Zeq = (1j * Xm * Z2) / (1j * Xm + Z2)
    Zt  = R1 + 1j * X1 + Zeq
    I1  = V1 / Zt
    Veq = I1 * Zeq
    I2  = Veq / Z2
    P2  = 3.0 * np.abs(I2) ** 2 * (R2 / s)
    return P2 / ws_mec


def calc_curva_tn(mp, n_points: int = 600) -> dict:
    """Calcula a curva T×n pelo circuito equivalente completo.

    Cobre as 3 regiões: gerador (s<0), motor (0<s≤1) e frenagem (s>1).
    Retorna dict com arrays e escalares de interesse.
    """
    V1, R1, X1, R2, X2, Xm, ws_mec, ns = _extract_params(mp)

    # ── varredura de escorregamento cobrindo as 3 regiões ────────────────────
    s_neg  = np.linspace(-1.0, -1e-4, n_points // 4)          # gerador
    s_pos1 = np.linspace(1e-4,  1.0,  n_points // 2)          # motor
    s_pos2 = np.linspace(1.001, 2.0,  n_points // 4)          # frenagem
    s_all  = np.concatenate([s_neg, s_pos1, s_pos2])

    Te_all = _torque_array(s_all, V1, R1, X1, R2, X2, Xm, ws_mec)
    n_rpm  = ns * (1.0 - s_all)

    # ── pico de torque na região de motor ────────────────────────────────────
    mask_motor = (s_all > 0) & (s_all <= 1.0)
    Te_motor   = Te_all[mask_motor]
    s_motor    = s_all[mask_motor]
    idx_max    = int(np.argmax(Te_motor))
    Te_max     = float(Te_motor[idx_max])
    s_max      = float(s_motor[idx_max])
    n_max      = float(ns * (1.0 - s_max))

    # ── torque de partida (s = 1) ─────────────────────────────────────────────
    Te_part = float(_torque_array(np.array([1.0]), V1, R1, X1, R2, X2, Xm, ws_mec)[0])

    return {
        "n_rpm":   n_rpm,
        "Te":      Te_all,
        "s":       s_all,
        "Te_max":  Te_max,
        "Te_part": Te_part,
        "s_max":   s_max,
        "n_sinc":  ns,
        "n_max":   n_max,
    }


def calc_fluxo_potencia(s: float, mp) -> dict:
    """Calcula o fluxo de potência no ponto de operação.

    Parâmetros extraídos de mp (parâmetros do usuário).
    Retorna P_in, P_cu1, P_ag, P_cu2, P_mec, P_out, eta, I1_rms, I2_rms, region.
    """
    V1, R1, X1, R2, X2, Xm, ws_mec, ns = _extract_params(mp)

    if abs(s) < 1e-9:
        s = 1e-9

    Z2  = (R2 / s) + 1j * X2
    Zeq = (1j * Xm * Z2) / (1j * Xm + Z2)
    Zt  = R1 + 1j * X1 + Zeq
    I1  = V1 / Zt
    Veq = I1 * Zeq
    I2  = Veq / Z2

    P_in  = 3.0 * (V1 * np.conj(I1)).real
    P_cu1 = 3.0 * abs(I1) ** 2 * R1
    P_ag  = 3.0 * abs(I2) ** 2 * (R2 / s)    # = P_in - P_cu1
    P_cu2 = s * P_ag
    P_mec = (1.0 - s) * P_ag
    P_out = P_mec                              # sem perdas rotacionais modeladas

    if P_in != 0:
        eta = (P_out / P_in * 100.0) if P_in > 0 else (P_out / P_in * 100.0)
    else:
        eta = 0.0

    if s < 0:
        region = "Gerador"
    elif s > 1:
        region = "Frenagem"
    else:
        region = "Motor"

    return {
        "P_in":   float(P_in),
        "P_cu1":  float(P_cu1),
        "P_ag":   float(P_ag),
        "P_cu2":  float(P_cu2),
        "P_mec":  float(P_mec),
        "P_out":  float(P_out),
        "eta":    float(eta),
        "I1_rms": float(abs(I1)),
        "I2_rms": float(abs(I2)),
        "region": region,
        "slip":   float(s),
    }


def build_fig_tn(tn: dict, dark: bool,
                 Te_op: float | None = None, n_op: float | None = None) -> go.Figure:
    """Plota a curva T×n com as 3 regiões de operação."""
    pt  = _plot_theme(dark)
    ns  = tn["n_sinc"]

    # cores por região
    col_motor   = "#4f8ef7" if dark else "#1d4ed8"
    col_gen     = "#34d399" if dark else "#059669"
    col_brake   = "#f87171" if dark else "#dc2626"
    col_op      = "#fbbf24" if dark else "#d97706"

    s_arr = tn["s"]
    Te    = tn["Te"]
    n_rpm = tn["n_rpm"]
    n_max_pct = tn["n_max"] / ns * 100.0

    mask_motor  = (s_arr > 0) & (s_arr <= 1.0)
    mask_gen    = s_arr < 0
    mask_brake  = s_arr > 1.0

    fig = go.Figure()

    # ── regiões ──────────────────────────────────────────────────────────────
    for mask, col, name in [
        (mask_motor, col_motor, "Motor (0 < s ≤ 1)"),
        (mask_gen,   col_gen,   "Gerador (s < 0)"),
        (mask_brake, col_brake, "Frenagem (s > 1)"),
    ]:
        if mask.any():
            fig.add_trace(go.Scatter(
                x=n_rpm[mask] / ns * 100.0, y=Te[mask],
                mode="lines", name=name,
                line=dict(color=col, width=2.2),
                hovertemplate="n = %{x:.1f} %ns<br>Te = %{y:.2f} N·m<extra>" + name + "</extra>",
            ))

    # ── ponto de pico (pull-out) ──────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=[n_max_pct], y=[tn["Te_max"]],
        mode="markers+text", name="Te,max (pull-out)",
        marker=dict(color=col_motor, size=9, symbol="circle"),
        text=[f"Te,max = {tn['Te_max']:.1f} N·m"],
        textposition="top right",
        textfont=dict(color=pt["fg"], size=10),
        hovertemplate=f"n = {n_max_pct:.1f} %ns<br>Te,max = {tn['Te_max']:.2f} N·m<extra>Pull-out</extra>",
    ))

    # ── ponto de partida (s=1) ────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=[0.0], y=[tn["Te_part"]],
        mode="markers+text", name="Te,partida (s=1)",
        marker=dict(color=col_motor, size=7, symbol="circle-open"),
        text=[f"Te,p = {tn['Te_part']:.1f} N·m"],
        textposition="top right",
        textfont=dict(color=pt["fg"], size=10),
        hovertemplate=f"Te,partida = {tn['Te_part']:.2f} N·m<extra>Partida</extra>",
    ))

    # ── ponto de operação da simulação ────────────────────────────────────────
    if Te_op is not None and n_op is not None:
        fig.add_trace(go.Scatter(
            x=[n_op / ns * 100.0], y=[Te_op],
            mode="markers", name="Ponto de operação",
            marker=dict(color=col_op, size=10, symbol="diamond"),
            hovertemplate=f"n = {n_op:.1f} rpm<br>Te = {Te_op:.2f} N·m<extra>Operação</extra>",
        ))

    # ── linha da velocidade síncrona ──────────────────────────────────────────
    fig.add_vline(x=100.0, line_dash="dash", line_color=pt["grid"], line_width=1,
                  annotation_text="ns", annotation_font_color=pt["fg"],
                  annotation_position="top right")

    # ── anotações de região ───────────────────────────────────────────────────
    for txt, xref, col in [
        ("Motor",   50.0, col_motor),
        ("Gerador", 115.0, col_gen),
        ("Frenagem", -50.0, col_brake),
    ]:
        fig.add_annotation(x=xref, y=tn["Te_max"] * 0.15,
                           text=txt, showarrow=False,
                           font=dict(color=col, size=10, family="Inter, system-ui"),
                           xref="x", yref="y")

    fig.update_layout(
        height=420,
        title=dict(text="Curva Característica T×n — Três Regiões de Operação",
                   x=0.5, xanchor="center", font=dict(size=13, color=pt["fg"])),
        paper_bgcolor=pt["paper_bg"], plot_bgcolor=pt["plot_bg"],
        font=dict(family="Inter, system-ui", size=11, color=pt["fg"]),
        margin=dict(l=60, r=20, t=50, b=50),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="Velocidade (% da velocidade síncrona)",
                   showgrid=True, gridcolor=pt["grid"], gridwidth=0.4,
                   zeroline=True, zerolinecolor=pt["grid"],
                   tickfont=dict(size=10, color=pt["fg"]),
                   ticksuffix=" %"),
        yaxis=dict(title="Torque eletromagnético Te (N·m)",
                   showgrid=True, gridcolor=pt["grid"], gridwidth=0.4,
                   tickfont=dict(size=10, color=pt["fg"]),
                   autorange=True),
    )
    return fig


def build_fig_fluxo_potencia(fp: dict, dark: bool) -> go.Figure:
    """Gráfico de barras horizontais mostrando o fluxo de potência."""
    pt = _plot_theme(dark)

    labels = ["P_in", "P_cu1 (cobre\nestator)", "P_ag\n(entreferro)",
              "P_cu2 (cobre\nrotor)", "P_mec\n(mecânica)", "P_out\n(saída)"]
    values = [fp["P_in"], fp["P_cu1"], fp["P_ag"], fp["P_cu2"], fp["P_mec"], fp["P_out"]]
    colors = ["#94a3b8", "#f87171", "#4f8ef7", "#f87171", "#34d399", "#059669"]
    if not dark:
        colors = ["#64748b", "#dc2626", "#1d4ed8", "#dc2626", "#059669", "#065f46"]

    texts = [f"{v:,.1f} W" for v in values]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=texts,
        textposition="outside",
        textfont=dict(size=10, color=pt["fg"]),
        hovertemplate="%{y}: %{x:,.1f} W<extra></extra>",
    ))

    eta_str = f"η = {fp['eta']:.1f} %"
    region_str = fp["region"]

    fig.update_layout(
        height=320,
        title=dict(
            text=f"Fluxo de Potência no Ponto de Operação — {region_str} | {eta_str}",
            x=0.5, xanchor="center", font=dict(size=12, color=pt["fg"])
        ),
        paper_bgcolor=pt["paper_bg"], plot_bgcolor=pt["plot_bg"],
        font=dict(family="Inter, system-ui", size=11, color=pt["fg"]),
        margin=dict(l=130, r=80, t=50, b=30),
        xaxis=dict(title="Potência (W)", showgrid=True, gridcolor=pt["grid"],
                   tickfont=dict(size=10, color=pt["fg"])),
        yaxis=dict(tickfont=dict(size=10, color=pt["fg"]), autorange="reversed"),
        showlegend=False,
    )
    return fig


def _op_on_curve(tn: dict, res: dict):
    """Retorna (Te_op, n_op) projetado sobre a curva T×n.

    Usa Te_ss da simulação e interpola na região estável (0 < s < s_max)
    para encontrar a velocidade correspondente na curva. Isso garante que
    o ponto fique sobre a curva com o valor de torque correto.
    """
    Te_ss = float(res.get("Te_ss", 0.0))
    if Te_ss <= 0:
        return None, None

    s_arr  = tn["s"]
    Te_arr = tn["Te"]
    n_arr  = tn["n_rpm"]

    # região estável do motor: s entre 0 e s_max (Te cresce monotonicamente com s)
    mask = (s_arr > 0) & (s_arr <= tn["s_max"])
    if not mask.any():
        return None, None

    Te_stable = Te_arr[mask]
    n_stable  = n_arr[mask]

    if Te_ss > Te_stable.max():
        return None, None  # além do torque de pull-out

    # interpolação: Te_stable crescente → n_stable decrescente
    n_op  = float(np.interp(Te_ss, Te_stable, n_stable))
    return Te_ss, n_op


def render_curva_tn(mp, res: dict, dark: bool, decimals: int, render_plotly_fn) -> None:
    """Renderiza a seção da curva T×n e fluxo de potência na UI."""
    st.divider()
    st.markdown('<p class="slabel">Curva Característica</p>', unsafe_allow_html=True)

    with st.expander("Ver Curva T×n (Torque × Velocidade)", expanded=False):
        tn    = calc_curva_tn(mp)
        Te_op, n_op = _op_on_curve(tn, res)

        fig_tn = build_fig_tn(tn, dark, Te_op=Te_op, n_op=n_op)
        render_plotly_fn(fig_tn, div_id="ems-tn")

        c1, c2, c3 = st.columns(3)
        c1.metric("Torque Máximo $T_{e,max}$ (pull-out)", f"{tn['Te_max']:.{decimals}f} N·m")
        c2.metric("Torque de Partida $T_{e,p}$ (s=1)",    f"{tn['Te_part']:.{decimals}f} N·m")
        c3.metric("Escorregamento em $T_{e,max}$",         f"{tn['s_max']*100:.{decimals}f} %")
