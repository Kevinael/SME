from __future__ import annotations
import re
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly_charts import _plot_theme


def _strip_latex(s: str) -> str:
    """Remove marcação LaTeX $...$ para uso em títulos do Plotly."""
    _greek = {
        '\\omega': 'ω', '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ',
        '\\delta': 'δ', '\\theta': 'θ', '\\tau': 'τ', '\\phi': 'φ',
    }
    def _convert(m: re.Match) -> str:
        inner = m.group(1)
        for cmd, uni in _greek.items():
            inner = inner.replace(cmd, uni)
        inner = inner.replace('{', '').replace('}', '').replace('_', '').replace('\\', '')
        return inner
    return re.sub(r'\$([^$]+)\$', _convert, s)


def build_fig_fft(res: dict, dark: bool, key: str = "ias", label: str = "ias") -> go.Figure:
    """Espectro de amplitudes (FFT) de uma variável em regime permanente."""
    pt  = _plot_theme(dark)
    col = "#4f8ef7" if dark else "#1d4ed8"

    ss_start = int(res.get("_ss_start", 0))
    y = np.asarray(res[key][ss_start:], dtype=float)
    t = np.asarray(res["t"][ss_start:], dtype=float)
    if len(y) < 4:
        fig = go.Figure()
        fig.update_layout(title="Dados insuficientes para FFT", height=300,
                          paper_bgcolor=pt["paper_bg"], plot_bgcolor=pt["plot_bg"])
        return fig

    dt   = float(t[1] - t[0]) if len(t) > 1 else 1e-3
    N    = len(y)
    yf   = np.abs(np.fft.rfft(y)) * 2.0 / N
    freq = np.fft.rfftfreq(N, d=dt)

    # limita a 2kHz para legibilidade
    mask = freq <= 2000
    freq, yf = freq[mask], yf[mask]

    # detecta fundamental e marca harmônicas ímpares (1ª, 3ª, 5ª, 7ª, 9ª)
    f1_idx = int(np.argmax(yf[freq > 0.1])) + np.searchsorted(freq, 0.1)
    f1     = float(freq[f1_idx]) if f1_idx < len(freq) else 60.0
    harm_freqs = [f1 * k for k in [1, 3, 5, 7, 9] if f1 * k <= freq[-1]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=freq, y=yf, name=label,
        marker_color=col, opacity=0.85,
        hovertemplate="f = %{x:.1f} Hz<br>A = %{y:.4f}<extra></extra>",
    ))
    for hf in harm_freqs:
        fig.add_vline(x=hf, line_dash="dot", line_color="#ef4444", line_width=1.2,
                      annotation_text=f"{hf:.0f} Hz", annotation_font_color="#ef4444",
                      annotation_font_size=9)
    fig.update_layout(
        height=320,
        title=dict(text=f"Espectro de Amplitudes — {label} (regime permanente)",
                   x=0.5, xanchor="center", font=dict(size=12, color=pt["fg"])),
        paper_bgcolor=pt["paper_bg"], plot_bgcolor=pt["plot_bg"],
        font=dict(family="Inter, system-ui", size=10, color=pt["fg"]),
        margin=dict(l=50, r=20, t=50, b=40),
        xaxis=dict(title="Frequência (Hz)", showgrid=True, gridcolor=pt["grid"],
                   tickfont=dict(size=9, color=pt["fg"]), exponentformat="none"),
        yaxis=dict(title="Amplitude", showgrid=True, gridcolor=pt["grid"],
                   tickfont=dict(size=9, color=pt["fg"]), exponentformat="none"),
        showlegend=False,
    )
    return fig


def render_harmonicas(res: dict, var_keys: list, var_labels: list,
                      dark: bool, render_plotly_fn) -> None:
    """Renderiza a seção de análise espectral (FFT) na UI."""
    ac_keys = [k for k in var_keys if k in ("ias", "ibs", "ics", "iar", "ibr", "icr", "Va", "Vb", "Vc")]
    if not ac_keys:
        return

    st.divider()
    st.markdown('<p class="slabel">Análise Espectral</p>', unsafe_allow_html=True)
    with st.expander("Ver Espectro de Harmônicas (FFT)", expanded=False):
        fft_var = st.selectbox(
            "Variável para análise",
            options=ac_keys,
            format_func=lambda k: next((lbl for kk, lbl in zip(var_keys, var_labels) if kk == k), k),
            key="fft_var_select",
        )
        fft_lbl      = next((lbl for kk, lbl in zip(var_keys, var_labels) if kk == fft_var), fft_var)
        fft_lbl_plot = _strip_latex(fft_lbl)
        fig_fft = build_fig_fft(res, dark, key=fft_var, label=fft_lbl_plot)
        render_plotly_fn(fig_fft, div_id="ems-fft")
        st.caption("Linhas vermelhas tracejadas indicam harmônicas ímpares (1ª, 3ª, 5ª, 7ª, 9ª).")
