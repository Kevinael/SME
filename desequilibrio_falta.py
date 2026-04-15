# -*- coding: utf-8 -*-
"""
desequilibrio_falta.py
======================
Módulo reservado para simulação de desequilíbrio de tensão e falta de fase.
Não é importado nem utilizado pelo restante da aplicação.

Para reativar: importe render_desequilibrio_ui em EMS_UI.py e adicione
deseq_a, deseq_b, deseq_c, falta_fase_a, falta_fase_b, falta_fase_c
como parâmetros de run_simulation em EMS_PY.py.
"""
from __future__ import annotations
import numpy as np


# ── Geração de tensões com desequilíbrio/falta ──────────────────────────────

def abc_voltages_deseq(t, Vl: float, f: float,
                       deseq_a: float = 0.0,
                       deseq_b: float = 0.0,
                       deseq_c: float = 0.0,
                       falta_fase_a: bool = False,
                       falta_fase_b: bool = False,
                       falta_fase_c: bool = False):
    """Gera tensões abc com desequilíbrio e/ou falta de fase em qualquer fase.

    deseq_a / deseq_b / deseq_c : desvio fracional em Vl (ex: 0.1 = +10%, -0.1 = -10%).
    falta_fase_a/b/c             : se True, força a tensão da fase a zero.
    Aceita t escalar ou np.ndarray; retorna o mesmo tipo.
    """
    scalar = np.ndim(t) == 0
    t_arr = np.atleast_1d(np.asarray(t, dtype=float))
    tetae = 2.0 * np.pi * f * t_arr
    zero  = np.zeros_like(t_arr)

    Va = zero if falta_fase_a else np.sqrt(2.0/3.0) * Vl * (1.0 + deseq_a) * np.sin(tetae)
    Vb = zero if falta_fase_b else np.sqrt(2.0/3.0) * Vl * (1.0 + deseq_b) * np.sin(tetae - 2.0 * np.pi / 3.0)
    Vc = zero if falta_fase_c else np.sqrt(2.0/3.0) * Vl * (1.0 + deseq_c) * np.sin(tetae + 2.0 * np.pi / 3.0)

    if scalar:
        return float(Va[0]), float(Vb[0]), float(Vc[0])
    return Va, Vb, Vc


# ── Bloco de UI ─────────────────────────────────────────────────────────────

def render_desequilibrio_ui(config: dict, tmax: float = 2.0) -> None:
    """Renderiza o expander de desequilíbrio de tensão / falta de fase.

    Preenche config com as chaves:
      deseq_a, deseq_b, deseq_c,
      falta_fase_a, falta_fase_b, falta_fase_c,
      t_deseq.
    Deve ser chamado dentro do bloco de configuração do experimento em EMS_UI.py.
    """
    import streamlit as st
    st.write("")
    with st.expander("Desequilíbrio de Tensão / Falta de Fase", expanded=False):
        st.info("Simula assimetria na rede. Útil para estudar diagnóstico de falhas e proteção de motores.")

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown("**Fase A**")
            deseq_a = st.slider(
                "Desvio fase A (%)", min_value=-30, max_value=30, value=0, step=1,
                help="Ex: +10 → Va = 1.1 × Vnominal", key="deseq_a"
            ) / 100.0
            falta_a = st.toggle("Falta de Fase A (Va = 0)", value=False, key="falta_a")
            if falta_a:
                st.warning("Falta na fase A — correntes muito elevadas.")

        with col_b:
            st.markdown("**Fase B**")
            deseq_b = st.slider(
                "Desvio fase B (%)", min_value=-30, max_value=30, value=0, step=1,
                help="Ex: +10 → Vb = 1.1 × Vnominal", key="deseq_b"
            ) / 100.0
            falta_b = st.toggle("Falta de Fase B (Vb = 0)", value=False, key="falta_b")
            if falta_b:
                st.warning("Falta na fase B — correntes muito elevadas.")

        with col_c:
            st.markdown("**Fase C**")
            deseq_c = st.slider(
                "Desvio fase C (%)", min_value=-30, max_value=30, value=0, step=1,
                help="Ex: -10 → Vc = 0.9 × Vnominal", key="deseq_c"
            ) / 100.0
            falta_c = st.toggle("Falta de Fase C (Vc = 0)", value=False, key="falta_c")
            if falta_c:
                st.warning("Falta na fase C — correntes muito elevadas.")

        faltas_ativas = sum([falta_a, falta_b, falta_c])
        if faltas_ativas >= 2:
            st.error("Atenção: duas ou mais fases em falta — operação monofásica ou sem tensão. "
                     "Reduza o tempo de simulação.")
        elif faltas_ativas == 1:
            st.warning("Uma fase em falta: operação bifásica — correntes muito elevadas. "
                       "Reduza o tempo de simulação.")

        t_deseq = st.number_input(
            "Instante de início do desequilíbrio (s)",
            min_value=0.0, max_value=float(tmax), value=1.0, step=0.1, format="%.2f",
            help="O desequilíbrio começa a atuar neste instante. Use 0 para aplicar desde o início.",
        )

        any_active = any([deseq_a, deseq_b, deseq_c, falta_a, falta_b, falta_c])
        if any_active and t_deseq > 0.0:
            st.caption(f"Rede balanceada até {t_deseq:.2f} s — desequilíbrio/falta aplicado a partir desse instante.")

        config["deseq_a"]      = deseq_a
        config["deseq_b"]      = deseq_b
        config["deseq_c"]      = deseq_c
        config["falta_fase_a"] = falta_a
        config["falta_fase_b"] = falta_b
        config["falta_fase_c"] = falta_c
        config["t_deseq"]      = t_deseq
