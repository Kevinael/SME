from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


_LINE_COLORS_DARK  = ["#FFFFFF","#FFFFFF","#FFFFFF","#a78bfa",
                      "#ffffff","#14b8a6","#f59e0b","#6366f1",
                      "#84cc16","#ef4444","#06b6d4","#d946ef"]
_LINE_COLORS_LIGHT = ["#000000","#000000","#000000","#000000",
                      "#000000","#000000","#000000","#000000",
                      "#000000","#000000","#000000","#000000"]


def _colors(dark: bool) -> list:
    return _LINE_COLORS_DARK if dark else _LINE_COLORS_LIGHT


def _plot_theme(dark: bool) -> dict:
    return dict(
        plot_bg  = "#000000" if dark else "#ffffff",
        paper_bg = "#161b27" if dark else "#ffffff",
        fg       = "#ffffff" if dark else "#000000",
        grid     = "#ffffff" if dark else "#B9ADAD",
    )


def build_fig_stacked(res, var_keys, var_labels, dark, t_events, decimals=2) -> go.Figure:
    n = len(var_keys)
    pt = _plot_theme(dark)
    cols = _colors(dark)

    fig = make_subplots(
        rows=n, cols=1,
        shared_xaxes=True,
        vertical_spacing=max(0.05, 0.07/max(n,1)),
    )
    t = res["t"]
    for i, (key, lbl) in enumerate(zip(var_keys, var_labels), 1):
        col = cols[(i-1) % len(cols)]
        fig.add_trace(go.Scatter(
            x=t, y=res[key], mode="lines", name=lbl,
            line=dict(color=col, width=1.9),
            hovertemplate=f"<b>{lbl}</b><br>t = %{{x:.4f}} s<br>valor = %{{y:.{decimals}f}}<extra></extra>",
        ), row=i, col=1)
        for te in (t_events or []):
            fig.add_vline(x=te, line_dash="dot", line_color="#000000",
                          line_width=1.1, row=i, col=1)
        fig.update_yaxes(row=i, col=1,
                         title_text=lbl,
                         title_font=dict(size=12, color=pt["fg"]),
                         showgrid=True, gridcolor=pt["grid"], gridwidth=0.4,
                         zeroline=True, zerolinecolor=pt["grid"],
                         tickfont=dict(size=10, color=pt["fg"]),
                         exponentformat="none",
                         autorange=True,
                         rangemode="normal",
                         fixedrange=False)

    fig.update_xaxes(row=n, col=1, title_text="Tempo (s)",
                     showgrid=True, gridcolor=pt["grid"], gridwidth=0.4,
                     tickfont=dict(size=10, color=pt["fg"]))
    fig.update_xaxes(uirevision="x_shared")
    fig.update_yaxes(uirevision="y_auto")
    fig.update_layout(
        height=max(300, 280*n),
        paper_bgcolor=pt["paper_bg"], plot_bgcolor=pt["plot_bg"],
        font=dict(family="Inter, system-ui", size=11, color=pt["fg"]),
        margin=dict(l=55, r=20, t=45, b=40),
        hovermode="x unified", showlegend=False,
        uirevision="layout",
    )
    return fig


def build_fig_sidebyside(res, var_keys, var_labels, dark, t_events, decimals=2,
                         ref_list=None, primary_color=None,
                         compact: bool = False) -> list[go.Figure]:
    # ref_list: list of {"res": dict, "color": str, "dash": str, "label": str}
    # primary_color: if set, overrides palette for the primary trace
    cols = _colors(dark)
    figs = []
    t    = res["t"]
    th   = _plot_theme(dark)
    for i, (key, lbl) in enumerate(zip(var_keys, var_labels)):
        pcol = primary_color if primary_color else cols[i % len(cols)]
        fig = go.Figure()
        for ref_item in (ref_list or []):
            res_ref   = ref_item.get("res")
            ref_color = ref_item.get("color", "#888888")
            ref_dash  = ref_item.get("dash", "dash")
            ref_label = ref_item.get("label", "Referência")
            if res_ref is not None and key in res_ref:
                fig.add_trace(go.Scatter(
                    x=res_ref["t"], y=res_ref[key], mode="lines", name=ref_label,
                    line=dict(color=ref_color, width=1.4, dash=ref_dash),
                    hovertemplate=f"<b>{ref_label}</b><br>t = %{{x:.4f}} s<br>valor = %{{y:.{decimals}f}}<extra></extra>",
                ))
        fig.add_trace(go.Scatter(
            x=t, y=res[key], mode="lines", name=lbl,
            line=dict(color=pcol, width=1.8),
            hovertemplate=f"<b>{lbl}</b><br>t = %{{x:.4f}} s<br>valor = %{{y:.{decimals}f}}<extra></extra>",
        ))
        for te in (t_events or []):
            fig.add_vline(x=te, line_dash="dot", line_color="#000000", line_width=1.1)
        _h   = 200 if compact else 230
        _m   = dict(l=28, r=8,  t=26, b=26) if compact else dict(l=45, r=12, t=36, b=36)
        _fsz = 9   if compact else 10
        fig.update_layout(
            title=dict(text=lbl, x=0.5, xanchor="center",
                       font=dict(size=11 if compact else 12, color=th["fg"])),
            height=_h,
            paper_bgcolor=th["paper_bg"], plot_bgcolor=th["plot_bg"],
            font=dict(family="Inter, system-ui", size=_fsz, color=th["fg"]),
            margin=_m,
            xaxis=dict(title="Tempo (s)", showgrid=True,
                       gridcolor=th["grid"], tickfont=dict(size=9, color=th["fg"])),
            yaxis=dict(showgrid=True, gridcolor=th["grid"],
                       zeroline=True, zerolinecolor=th["grid"],
                       tickfont=dict(size=9, color=th["fg"]),
                       exponentformat="none",
                       autorange=True, rangemode="normal", fixedrange=False),
            hovermode="x unified", showlegend=False,
        )
        figs.append(fig)
    return figs


def build_fig_overlay(res, var_keys, var_labels, dark, t_events, decimals=2,
                      ref_list=None, primary_color=None,
                      compact: bool = False) -> go.Figure:
    # ref_list: list of {"res": dict, "color": str, "dash": str, "label": str}
    # primary_color: if set, overrides palette for all primary traces
    pt   = _plot_theme(dark)
    cols = _colors(dark)
    t    = res["t"]

    right_units = {"n", "wr"}
    has_right   = any(k in right_units for k in var_keys)

    fig = go.Figure()
    for ref_item in (ref_list or []):
        res_ref   = ref_item.get("res")
        ref_color = ref_item.get("color", "#888888")
        ref_dash  = ref_item.get("dash", "dash")
        ref_label = ref_item.get("label", "Referência")
        if res_ref is not None:
            for key, lbl in zip(var_keys, var_labels):
                if key not in res_ref:
                    continue
                yaxis = "y2" if (key in right_units and has_right) else "y"
                fig.add_trace(go.Scatter(
                    x=res_ref["t"], y=res_ref[key], mode="lines",
                    name=f"{ref_label} — {lbl}", yaxis=yaxis,
                    line=dict(color=ref_color, width=1.4, dash=ref_dash),
                    hovertemplate=f"<b>{ref_label}</b><br>t = %{{x:.4f}} s<br>valor = %{{y:.{decimals}f}}<extra></extra>",
                ))
    for i, (key, lbl) in enumerate(zip(var_keys, var_labels)):
        pcol  = primary_color if primary_color else cols[i % len(cols)]
        yaxis = "y2" if (key in right_units and has_right) else "y"
        fig.add_trace(go.Scatter(
            x=t, y=res[key], mode="lines", name=lbl,
            line=dict(color=pcol, width=1.9), yaxis=yaxis,
            hovertemplate=f"<b>{lbl}</b><br>t = %{{x:.4f}} s<br>valor = %{{y:.{decimals}f}}<extra></extra>",
        ))
    for te in (t_events or []):
        fig.add_vline(x=te, line_dash="dot", line_color="#000000", line_width=1.1)

    y2_cfg = dict(
        overlaying="y", side="right",
        showgrid=False, zeroline=False,
        tickfont=dict(size=10, color=pt["fg"]),
        exponentformat="none",
        autorange=True, rangemode="normal", fixedrange=False,
    ) if has_right else {}

    _r_val = (45 if has_right else 8)  if compact else (65 if has_right else 20)
    _ov_m  = dict(l=35, r=_r_val, t=32, b=28) if compact else dict(l=55, r=65 if has_right else 20, t=48, b=40)
    fig.update_layout(
        height=320 if compact else 380,
        title=dict(text="Curvas Sobrepostas", x=0.5, xanchor="center",
                   font=dict(size=11 if compact else 12, color=pt["fg"])),
        paper_bgcolor=pt["paper_bg"], plot_bgcolor=pt["plot_bg"],
        font=dict(family="Inter, system-ui", size=10 if compact else 11, color=pt["fg"]),
        margin=_ov_m,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="right", x=1, font=dict(size=10),
                    bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="Tempo (s)", showgrid=True,
                   gridcolor=pt["grid"], gridwidth=0.4,
                   tickfont=dict(size=10, color=pt["fg"])),
        yaxis=dict(showgrid=True, gridcolor=pt["grid"],
                   zeroline=True, zerolinecolor=pt["grid"],
                   tickfont=dict(size=10, color=pt["fg"]),
                   exponentformat="none",
                   autorange=True, rangemode="normal", fixedrange=False),
        yaxis2=y2_cfg if has_right else {},
    )
    return fig
