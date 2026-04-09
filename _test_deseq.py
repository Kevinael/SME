import streamlit as st
from desequilibrio_falta import render_desequilibrio_ui, abc_voltages_deseq
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Teste — Desequilíbrio de Tensão", layout="wide")
st.title("Teste: Desequilíbrio de Tensão / Falta de Fase")

config = {}
render_desequilibrio_ui(config, tmax=2.0)

if st.button("Simular"):
    t = np.linspace(0.0, 2.0, 4000)
    Va, Vb, Vc = abc_voltages_deseq(
        t, Vl=220.0, f=60.0,
        deseq_a=config["deseq_a"],
        deseq_b=config["deseq_b"],
        deseq_c=config["deseq_c"],
        falta_fase_a=config["falta_fase_a"],
        falta_fase_b=config["falta_fase_b"],
        falta_fase_c=config["falta_fase_c"],
    )
    t_deseq = config["t_deseq"]
    if t_deseq > 0.0:
        mask = t < t_deseq
        t_bal = t[mask]
        Va_bal, Vb_bal, Vc_bal = abc_voltages_deseq(t_bal, 220.0, 60.0)
        Va[mask], Vb[mask], Vc[mask] = Va_bal, Vb_bal, Vc_bal

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=Va, name="Va", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=t, y=Vb, name="Vb", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=t, y=Vc, name="Vc", line=dict(color="green")))
    if t_deseq > 0.0:
        fig.add_vline(x=t_deseq, line_dash="dash", line_color="orange",
                      annotation_text=f"t={t_deseq:.2f}s")
    fig.update_layout(title="Tensões de fase", xaxis_title="Tempo (s)", yaxis_title="Tensão (V)")
    st.plotly_chart(fig, use_container_width=True)
