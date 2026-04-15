# -*- coding: utf-8 -*-
"""
eqcircuit_plotter.py — Circuito Equivalente Monofasico em T (MIT)
Desenha o circuito com schemdraw + matplotlib.

Uso como modulo (Streamlit):
    from eqcircuit_plotter import render_circuit
    render_circuit(mp, dark, _palette)

Uso standalone:
    python eqcircuit_plotter.py           # fundo escuro
    python eqcircuit_plotter.py --light   # fundo claro
"""

from __future__ import annotations
import io
import sys
from typing import Any, Callable
import matplotlib
import matplotlib.figure
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import schemdraw
import schemdraw.elements as elm


def build_figure(mp: Any, dark: bool, palette_fn: Callable[[bool], dict[str, str]]) -> matplotlib.figure.Figure:
    c      = palette_fn(dark)
    bg_hex = "#000000" if dark else "#ffffff"
    wire   = "#ffffff" if dark else "#000000"

    OFST   = 0.20
    OFSTV  = 0.30
    FS     = 20
    FS_VAL = 18

    fig, ax = plt.subplots(figsize=(13, 3.8))
    fig.patch.set_facecolor(bg_hex)
    ax.set_facecolor(bg_hex)
    ax.set_axis_off()

    with schemdraw.Drawing(canvas=ax) as d:
        d.config(fontsize=10, color=wire)

        # ── fonte Vs ────────────────────────────────────────────────────
        src = d.add(
            elm.SourceSin().up().color(wire)
            .label(r"$V_s$", loc="top", ofst=OFSTV, fontsize=FS, color=wire)
            .length(d.unit)
        )

        # ── fio superior ────────────────────────────────────────────────
        d.add(elm.Line().right().length(0.4))

        # ── Rs ──────────────────────────────────────────────────────────
        d.add(
            elm.Resistor().right().color(wire)
            .label(r"$R_s$",              loc="top",    ofst=OFST, fontsize=FS,     color=wire)
            .label(f"{mp.Rs:.3f} \u03a9", loc="bottom", ofst=OFST, fontsize=FS_VAL, color=wire)
        )

        # ── jXls ────────────────────────────────────────────────────────
        d.add(
            elm.Inductor2().right().color(wire)
            .label(r"$jX_{ls}$",           loc="top",    ofst=OFST, fontsize=FS,     color=wire)
            .label(f"{mp.Xls:.3f} \u03a9", loc="bottom", ofst=OFST, fontsize=FS_VAL, color=wire)
        )

        # ── no T ────────────────────────────────────────────────────────
        T_node = d.add(elm.Line().right().length(0))
        T_pos  = T_node.end   # coordenada (x, y) do no T

        # ── fio separador para acomodar o paralelo (Rfe ocupa sep=1.6 a direita do no T)
        d.add(elm.Line().right().length(1.6))

        # ── jXlr ────────────────────────────────────────────────────────
        d.add(
            elm.Inductor2().right().color(wire)
            .label(r"$jX_{lr}$",           loc="top",    ofst=OFST, fontsize=FS,     color=wire)
            .label(f"{mp.Xlr:.3f} \u03a9", loc="bottom", ofst=OFST, fontsize=FS_VAL, color=wire)
        )

        # ── Rr/s ────────────────────────────────────────────────────────
        d.add(
            elm.Resistor().right().color(wire)
            .label(r"$\dfrac{R_{r}}{s}$",    loc="top",    ofst=OFST, fontsize=FS,     color=wire)
            .label(f"{mp.Rr:.3f} \u03a9/s",  loc="bottom", ofst=OFST, fontsize=FS_VAL, color=wire)
        )

        # ── fio de retorno direito + inferior + esquerdo ─────────────────
        d.add(elm.Line().down().length(d.unit))
        d.add(elm.Line().left().tox(src.start))
        d.add(elm.Line().up().toy(src.start))

        # ── ramo shunt paralelo: Rfe // jXm ─────────────────────────────
        sep = 1.6

        # ramo esquerdo: jXm — alinhado ao no T
        xm_el = d.add(
            elm.Inductor2().at(T_pos).down().color(wire)
            .length(d.unit)
        )
        xm_bot = d.here

        # ramo direito: Rfe — deslocado para a direita
        rfe_top = (T_pos[0] + sep, T_pos[1])
        d.add(elm.Line().at(T_pos).right().length(sep))
        rfe_el = d.add(
            elm.Resistor().at(rfe_top).down().color(wire)
            .length(d.unit)
        )
        rfe_bot = d.here


        # fio inferior fechando o paralelo
        d.add(elm.Line().at(xm_bot).right().tox(rfe_bot))

 # ── labels dos ramos verticais via ax.text (coordenadas do drawing) ──
        xm_cx,  xm_cy  = xm_el.center[0],  xm_el.center[1]
        rfe_cx, rfe_cy = rfe_el.center[0], rfe_el.center[1]

        ax.text(xm_cx - 0.85, xm_cy + 0.35, r"$jX_m$",
            fontsize=FS,     color=wire, ha="right", va="center")
        ax.text(xm_cx - 0.85, xm_cy - 0.35, f"{mp.Xm:.2f} \u03a9",
            fontsize=FS_VAL, color=wire, ha="right", va="center")

        ax.text(rfe_cx + 0.85, rfe_cy + 0.35, r"$R_{fe}$",
            fontsize=FS,     color=wire, ha="left", va="center")
        ax.text(rfe_cx + 0.85, rfe_cy - 0.35, f"{mp.Rfe:.0f} \u03a9",
            fontsize=FS_VAL, color=wire, ha="left", va="center")

    fig.subplots_adjust(left=0.04, right=0.98, top=0.96, bottom=0.08)
    return fig


def render_circuit(mp: Any, dark: bool, palette_fn: Callable[[bool], dict[str, str]]) -> None:
    """Gera o circuito e exibe via st.image (uso Streamlit)."""
    import streamlit as st

    bg_hex = "#0d1117" if dark else "#ffffff"
    fig = build_figure(mp, dark, palette_fn)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, facecolor=bg_hex, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)

    st.image(buf, width='stretch')


# ── Execucao standalone ──────────────────────────────────────────────────────
if __name__ == "__main__":
    from dataclasses import dataclass, field
    import numpy as np

    @dataclass
    class _MP:
        Vl:  float = 220.0
        f:   float = 60.0
        Rs:  float = 0.435
        Rr:  float = 0.816
        Xm:  float = 26.13
        Xls: float = 0.754
        Xlr: float = 0.754
        Rfe: float = 500.0
        p:   int   = 4
        J:   float = 0.089
        B:   float = 0.0
        Xml: float = field(init=False)
        wb:  float = field(init=False)
        def __post_init__(self):
            self.Xml = 1.0 / (1.0/self.Xm + 1.0/self.Xls + 1.0/self.Xlr)
            self.wb  = 2.0 * np.pi * self.f

    def _palette(dark: bool) -> dict[str, str]:
        if dark:
            return dict(muted="#8892b0", text="#e4e8f5", accent="#4f8ef7",
                        border="#2a3150", surface="#161b27")
        return dict(muted="#4b5563", text="#111827", accent="#2563eb",
                    border="#d0d8f0", surface="#ffffff")

    dark = "--light" not in sys.argv
    mp   = _MP()
    matplotlib.use("TkAgg")
    fig  = build_figure(mp, dark, _palette)
    plt.show()
