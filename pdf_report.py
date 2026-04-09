from __future__ import annotations
import io
import numpy as np
from EMS_PY import MachineParams
from eqcircuit_plotter import build_figure as _build_circuit_figure
from theme import _palette


def _build_pdf_page_fig(res: dict, var_keys: list, var_labels: list,
                         t_events: list, color_offset: int = 0) -> "matplotlib.figure.Figure":
    """Gera uma figura matplotlib com até 4 subplots para uma página do PDF."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    COLORS = ["#1d4ed8","#ea580c","#16a34a","#7c3aed",
              "#db2777","#0d9488","#d97706","#4f46e5",
              "#65a30d","#dc2626","#0891b2","#c026d3"]

    n   = max(1, len(var_keys))
    t   = res["t"]
    fig, axes = plt.subplots(n, 1, figsize=(11, 3.2 * n), sharex=True)
    if n == 1:
        axes = [axes]

    fig.patch.set_facecolor("white")

    for i, (key, lbl, ax) in enumerate(zip(var_keys, var_labels, axes)):
        color = COLORS[(i + color_offset) % len(COLORS)]
        y = np.asarray(res[key])
        ax.plot(t, y, color=color, linewidth=1.2, solid_capstyle="round")
        ax.set_ylabel(lbl, fontsize=9, labelpad=4)
        ax.tick_params(labelsize=8)
        ax.tick_params(axis="x", labelbottom=True)
        ax.set_xlabel("Tempo (s)", fontsize=8)
        ax.set_facecolor("#f9fafc")
        ax.grid(True, color="#dde4f5", linewidth=0.5, linestyle="-")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#c0cce0")
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.2f"))
        for te in (t_events or []):
            ax.axvline(x=te, color="#94a3b8", linewidth=0.8, linestyle="--")

        y_range = float(np.max(y) - np.min(y)) or 1.0

        # ── pico (maior módulo) ───────────────────────────────────────────
        pk_idx = int(np.argmax(np.abs(y)))
        t_pk   = float(t[pk_idx])
        y_pk   = float(np.abs(y[pk_idx]))
        ax.plot(t_pk, y_pk, "^", color="#dc2626", markersize=6, zorder=5,
                label=f"Pico: {y_pk:.2f}")

        # ── regime permanente (valor pré-calculado em EMS_PY) ────────────
        rms_key  = key + "_rms"
        y_ss_rms = float(res[rms_key]) if rms_key in res else float(np.abs(y[-1]))
        ss_start = int(res.get("_ss_start", len(y) - 1))
        y_ss_mid = float(np.mean(y[ss_start:]))
        t_ss     = float(t[ss_start + (len(y) - ss_start)//2])
        ax.axvline(x=float(t[ss_start]), color="#16a34a", linewidth=0.7,
                   linestyle=":", alpha=0.6)
        ax.plot(t_ss, y_ss_mid, "D", color="#16a34a", markersize=5, zorder=5,
                label=f"Regime RMS: {y_ss_rms:.2f}")
        ax.legend(fontsize=7, loc="upper right", framealpha=0.8)

    fig.subplots_adjust(left=0.10, right=0.97, top=0.95, bottom=0.08,
                        hspace=0.75)
    return fig


def build_fig_matplotlib_pdf(res: dict, var_keys: list, var_labels: list,
                              t_events: list) -> "matplotlib.figure.Figure":
    """Compatibilidade: retorna figura com todas as variaveis (usado internamente)."""
    return _build_pdf_page_fig(res, var_keys, var_labels, t_events, color_offset=0)

def generate_pdf_report(exp_label: str, mp: MachineParams, res: dict,
                        fig, var_keys: list,
                        var_labels: list | None = None,
                        t_events: list | None = None,
                        exp_type: str = "dol") -> bytes:
    """Gera o relatório técnico em PDF e retorna como bytes (stream)."""
    from fpdf import FPDF
    import datetime

    var_labels = var_labels or var_keys
    t_events   = t_events   or []

    # ── Mapa de substituição Unicode → latin-1 ───────────────────────────────
    _UNICODE_SAFE = {
        '\u2014': '-',  '\u2013': '-',   # em dash, en dash
        '\u2091': 'e',  '\u2090': 'a',   # subscript e, a
        '\u209B': 's',  '\u1D63': 'r',   # subscript s, r
        '\u2080': '0',  '\u2081': '1',   '\u2082': '2',  '\u2083': '3',
        '\u2084': '4',  '\u2085': '5',   '\u2086': '6',  '\u2087': '7',
        '\u2088': '8',  '\u2089': '9',   # subscript digits
        '\u00B7': '.',                   # middle dot
        '\u03C9': 'w',  '\u03B1': 'a',   '\u03B2': 'b',  '\u03B7': 'n',
        '\u03C3': 's',  '\u03C6': 'phi', '\u03BB': 'lambda',
    }

    def _safe(text: str) -> str:
        for ch, repl in _UNICODE_SAFE.items():
            text = text.replace(ch, repl)
        return text.encode('latin-1', errors='ignore').decode('latin-1')

    # ── Subclasse com cabecalho e rodape automaticos ───────────────────────
    class EMS_PDF(FPDF):
        def normalize_text(self, text: str) -> str:
            return super().normalize_text(_safe(text))

        def header(self):
            # Faixa cinza clara
            self.set_fill_color(230, 230, 230)
            self.rect(0, 0, 210, 18, style="F")
            # Titulo (esquerda)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(30, 30, 30)
            self.set_xy(20, 4)
            self.cell(120, 10, "EMS - RELATÓRIO TÉCNICO DE SIMULAÇÃO", border=0)
            # Timestamp e versão (direita)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(80, 80, 80)
            ts = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M")
            self.set_xy(130, 4)
            self.cell(60, 5, f"Gerado em: {ts}", border=0, align="R")
            self.set_xy(130, 9)
            self.cell(60, 5, "Versão 1.0 | EMS Simulator", border=0, align="R")
            self.ln(8)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, f"Página {self.page_no()} de {{nb}}", align="C")

    # ── Funcoes auxiliares ─────────────────────────────────────────────────
    def section_title(pdf: EMS_PDF, title: str) -> None:
        """Linha de secao com fundo azul escuro e texto branco."""
        pdf.set_fill_color(25, 60, 140)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"  {title}", border=0, fill=True, ln=True)
        pdf.ln(2)

    def _render_cell_with_sub(pdf: EMS_PDF, text: str, w: float,
                               row_h: float, fill_rgb: tuple) -> None:
        """Renderiza uma celula com suporte a subscrito via marcacao [sub].
        Formato: texto normal[sub]subscrito[/sub]texto normal
        Ex: 'R[sub]fe[/sub]' -> R com 'fe' subscrito.
        """
        import re
        parts = re.split(r'\[sub\](.*?)\[/sub\]', text)

        x0 = pdf.get_x() + 2
        y0 = pdf.get_y()

        # fundo da celula com a cor correta
        pdf.set_fill_color(*fill_rgb)
        pdf.cell(w, row_h, "", border=0, fill=True)

        pdf.set_xy(x0, y0)
        MAIN_SIZE = 10
        SUB_SIZE  = 7
        SUB_DY    = 2.2

        for i, part in enumerate(parts):
            if not part:
                continue
            if i % 2 == 1:
                # subscrito
                pdf.set_font("Helvetica", "", SUB_SIZE)
                pdf.set_xy(pdf.get_x(), y0 + SUB_DY)
                pdf.cell(pdf.get_string_width(part) + 0.3, row_h - SUB_DY,
                         part, border=0, fill=False)
                pdf.set_xy(pdf.get_x(), y0)
            else:
                # texto normal
                pdf.set_font("Helvetica", "", MAIN_SIZE)
                pdf.set_xy(pdf.get_x(), y0)
                pdf.cell(pdf.get_string_width(part), row_h,
                         part, border=0, fill=False)

        # reposiciona cursor para a proxima celula da linha
        pdf.set_xy(x0 - 2 + w, y0)

    def zebra_table(pdf: EMS_PDF, rows: list[tuple], col_widths: list[float],
                    col_aligns: list[str], row_h: float = 7) -> None:
        """Tabela com zebra striping. rows = list[(celula, ...)]
        A primeira coluna suporta marcacao [sub]...[/sub] para subscritos.
        """
        for idx, row in enumerate(rows):
            fill_rgb = (242, 245, 255) if idx % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(*fill_rgb)
            pdf.set_text_color(40, 40, 40)
            pdf.set_font("Helvetica", "", 10)
            for col_i, (cell, w, align) in enumerate(zip(row, col_widths, col_aligns)):
                if col_i == 0 and '[sub]' in str(cell):
                    _render_cell_with_sub(pdf, str(cell), w, row_h, fill_rgb)
                else:
                    pdf.set_fill_color(*fill_rgb)
                    pdf.cell(w, row_h, f"  {cell}", border=0, fill=True, align=align)
            pdf.ln(row_h)

    def fmt_power(val: float) -> tuple[str, str]:
        """Retorna (valor_fmt, unidade)."""
        if abs(val) >= 1000:
            return f"{val/1000:.3f}", "kW"
        return f"{val:.2f}", "W"

    # ── Instancia e configuracoes globais ──────────────────────────────────
    pdf = EMS_PDF()
    pdf.alias_nb_pages()                       # habilita {nb} no footer
    pdf.set_margins(left=20, top=24, right=20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 1 — IDENTIFICACAO DO EXPERIMENTO
    # ══════════════════════════════════════════════════════════════════════
    section_title(pdf, "1. Identificação do Experimento")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(50, 7, "  Tipo de experimento:", border=0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, exp_label, border=0, ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 7, "  Velocidade síncrona:", border=0)
    pdf.cell(0, 7, f"{mp.n_sync:.1f} RPM  |  {mp.wb/(mp.p/2.0):.3f} rad/s (mecânica)", border=0, ln=True)
    pdf.cell(50, 7, "  Frequência nominal:", border=0)
    pdf.cell(0, 7, f"{mp.f:.1f} Hz  |  vel. campo girante: {mp.n_sync:.1f} RPM  ({mp.wb/(mp.p/2.0):.3f} rad/s)", border=0, ln=True)
    pdf.ln(5)

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 2 — VALORES NOMINAIS DA MAQUINA
    # ══════════════════════════════════════════════════════════════════════
    section_title(pdf, "2. Valores Nominais da Máquina")

    # Cabeçalho da tabela
    pdf.set_fill_color(200, 210, 240)
    pdf.set_text_color(20, 20, 80)
    pdf.set_font("Helvetica", "B", 10)
    for lbl, w in [("  Parâmetro", 110), ("Valor", 35), ("Unidade", 25)]:
        pdf.cell(w, 7, lbl, border=0, fill=True)
    pdf.ln(7)

    param_rows = [
        ("Tensão de linha (V[sub]l[/sub])",                    f"{mp.Vl:.1f}",    "V"),
        ("Frequência (f)",                                      f"{mp.f:.1f}",     "Hz"),
        ("Resistência do estator (R[sub]s[/sub])",             f"{mp.Rs:.4f}",    "Ohm"),
        ("Resistência do rotor (R[sub]r[/sub])",               f"{mp.Rr:.4f}",    "Ohm"),
        ("Reatância de magnetização (X[sub]m[/sub])",          f"{mp.Xm:.4f}",    "Ohm"),
        ("Reatância de dispersão est. (X[sub]ls[/sub])",       f"{mp.Xls:.4f}",   "Ohm"),
        ("Reatância de dispersão rot. (X[sub]lr[/sub])",       f"{mp.Xlr:.4f}",   "Ohm"),
        ("Resistência de perdas no ferro (R[sub]fe[/sub])",    f"{mp.Rfe:.1f}",   "Ohm"),
        ("Número de polos (p)",                                 f"{mp.p}",         "-"),
        ("Momento de inércia (J)",                              f"{mp.J:.4f}",     "kg.m²"),
        ("Coeficiente de atrito (B)",                          f"{mp.B:.4f}",     "N.m.s/rad"),
    ]
    zebra_table(pdf, param_rows, col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])
    pdf.ln(6)

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 3 — CIRCUITO EQUIVALENTE
    # ══════════════════════════════════════════════════════════════════════
    import matplotlib.pyplot as plt

    section_title(pdf, "3. Circuito Equivalente Monofásico em T")
    pdf.ln(2)

    circ_fig = _build_circuit_figure(mp, dark=False, palette_fn=_palette)
    circ_buf = io.BytesIO()
    circ_fig.savefig(circ_buf, format="png", dpi=200, bbox_inches="tight",
                     facecolor="white")
    plt.close(circ_fig)
    circ_buf.seek(0)

    with tempfile_ctx() as tmp_circ:
        with open(tmp_circ, "wb") as f_tmp:
            f_tmp.write(circ_buf.read())
        circ_w = 170
        pdf.image(tmp_circ, x=(210 - circ_w) / 2, w=circ_w)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "Figura 1: Circuito Equivalente Monofásico em T do MIT",
             border=0, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 4 — DESTAQUES DO EXPERIMENTO
    # ══════════════════════════════════════════════════════════════════════
    pdf.add_page()
    section_title(pdf, "4. Destaques do Experimento")

    def _kpis_destaque_pdf() -> list[tuple]:
        ias_pk   = float(np.max(np.abs(res["ias"])))
        Te_max   = float(np.max(res["Te"]))
        n_ss     = res["n_ss"]
        ias_rms  = res["ias_rms"]
        s_val    = res.get("s", 0.0)
        fator_pk = ias_pk / ias_rms if ias_rms > 0 else 0.0

        if exp_type in ("dol", "yd", "comp", "soft"):
            items = [
                ("Corrente de Pico (i[sub]as,pk[/sub])",           f"{ias_pk:.4f}",    "A"),
                ("Fator de Pico  (I[sub]pk[/sub] / I[sub]rms[/sub])", f"{fator_pk:.4f}", "-"),
                ("Torque Máximo (T[sub]e,max[/sub])",               f"{Te_max:.4f}",    "N.m"),
                ("Velocidade Final",                                 f"{n_ss:.3f}",      "RPM"),
            ]
            if exp_type == "yd":
                t_ev = t_events[1] if len(t_events) > 1 else (t_events[0] if t_events else 0.0)
                t    = res["t"]
                idx  = int(np.searchsorted(t, t_ev))
                ias_pk2 = float(np.max(np.abs(res["ias"][idx:]))) if idx < len(t) else 0.0
                items.insert(1, ("Corrente de Pico pós-comutação Y-D (i[sub]as,pk2[/sub])", f"{ias_pk2:.4f}", "A"))

        elif exp_type == "carga":
            n_vazio = float(np.mean(res["n"][:max(1, len(res["n"])//5)]))
            delta_n = n_vazio - n_ss
            ias_vazio = float(np.sqrt(np.mean(res["ias"][:max(1, len(res["ias"])//5)]**2)))
            delta_i   = ias_rms - ias_vazio
            items = [
                ("Velocidade em Vazio",                             f"{n_vazio:.3f}",   "RPM"),
                ("Velocidade com Carga",                            f"{n_ss:.3f}",      "RPM"),
                ("Afundamento de Velocidade",                       f"{delta_n:.3f}",   "RPM"),
                ("Variação de Corrente RMS (i[sub]as[/sub])",       f"{delta_i:.4f}",   "A"),
            ]

        elif exp_type == "gerador":
            P_out = res.get("P_out", 0.0)
            eta_g = res.get("eta",   0.0)
            lbl_p = "kW" if abs(P_out) >= 1000 else "W"
            val_p = P_out / 1000 if abs(P_out) >= 1000 else P_out
            items = [
                ("Potência Gerada para a Rede (P[sub]out[/sub])",  f"{val_p:.3f}",     lbl_p),
                ("Escorregamento (s)",                              f"{s_val*100:.3f}", "%"),
                ("Rendimento (eta)",                                f"{eta_g:.3f}",     "%"),
                ("Corrente RMS de Geração (i[sub]as,rms[/sub])",   f"{ias_rms:.4f}",   "A"),
            ]
        else:
            items = []
        return items

    dest_rows = _kpis_destaque_pdf()
    if dest_rows:
        pdf.set_fill_color(200, 210, 240)
        pdf.set_text_color(20, 20, 80)
        pdf.set_font("Helvetica", "B", 10)
        for lbl, w in [("  Grandeza", 110), ("Valor", 35), ("Unidade", 25)]:
            pdf.cell(w, 7, lbl, border=0, fill=True)
        pdf.ln(7)
        zebra_table(pdf, dest_rows, col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])
        pdf.ln(6)

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 5 — INDICADORES DE REGIME PERMANENTE
    # ══════════════════════════════════════════════════════════════════════
    section_title(pdf, "5. Indicadores de Regime Permanente")

    # Cabeçalho
    pdf.set_fill_color(200, 210, 240)
    pdf.set_text_color(20, 20, 80)
    pdf.set_font("Helvetica", "B", 10)
    for lbl, w in [("  Grandeza", 110), ("Valor", 35), ("Unidade", 25)]:
        pdf.cell(w, 7, lbl, border=0, fill=True)
    pdf.ln(7)

    P_gap  = res.get("P_gap",  0.0)
    P_mec  = res.get("P_mec",  0.0)
    P_cu_r = res.get("P_cu_r", 0.0)
    eta    = res.get("eta",    0.0)
    s      = res.get("s",      0.0)
    P_in   = res.get("P_in",   0.0)
    v_in,   u_in   = fmt_power(P_in)
    v_gap,  u_gap  = fmt_power(P_gap)
    v_mec,  u_mec  = fmt_power(P_mec)
    v_cu_r, u_cu_r = fmt_power(P_cu_r)

    # grandezas de regime permanente pre-calculadas em EMS_PY
    n_ss    = res["n_ss"]
    wr_ss   = res["wr_ss"]
    Te_ss   = res["Te_ss"]
    ias_rms = res["ias_rms"]
    ibs_rms = res["ibs_rms"]
    ics_rms = res["ics_rms"]
    # correntes de pico (durante toda a simulação)
    ias_pk = float(np.max(np.abs(res["ias"])))
    ibs_pk = float(np.max(np.abs(res["ibs"])))
    ics_pk = float(np.max(np.abs(res["ics"])))
    kpi_rows = [
        # ── Mecanica ──────────────────────────────────────────────────────
        ("Velocidade de regime",                                   f"{n_ss:.3f}",                         "RPM"),
        ("Velocidade angular do rotor (w[sub]r[/sub])",           f"{wr_ss:.4f}",                        "rad/s"),
        ("Torque eletromagnético de regime (T[sub]e[/sub])",      f"{Te_ss:.4f}",                        "N.m"),
        ("Torque eletromagnético máximo (T[sub]e,max[/sub])",     f"{float(np.max(res['Te'])):.4f}",     "N.m"),
        ("Escorregamento (s)",                                     f"{s*100:.3f}",                        "%"),
        # ── Correntes por fase (RMS de regime) ───────────────────────────
        ("Corrente RMS de regime - fase A (i[sub]as,rms[/sub])",  f"{ias_rms:.4f}",                      "A"),
        ("Corrente RMS de regime - fase B (i[sub]bs,rms[/sub])",  f"{ibs_rms:.4f}",                      "A"),
        ("Corrente RMS de regime - fase C (i[sub]cs,rms[/sub])",  f"{ics_rms:.4f}",                      "A"),
        ("Corrente de pico - fase A (i[sub]as,pk[/sub])",         f"{ias_pk:.4f}",                       "A"),
        ("Corrente de pico - fase B (i[sub]bs,pk[/sub])",         f"{ibs_pk:.4f}",                       "A"),
        ("Corrente de pico - fase C (i[sub]cs,pk[/sub])",         f"{ics_pk:.4f}",                       "A"),
        # ── Potências e eficiência ────────────────────────────────────────
        ("Potência de entrada (P[sub]in[/sub])",                  v_in,                                   u_in),
        ("Potência no entreferro (P[sub]gap[/sub])",              v_gap,                                  u_gap),
        ("Potência mecânica (P[sub]mec[/sub])",                   v_mec,                                  u_mec),
        ("Perdas no cobre do rotor (P[sub]cu,r[/sub])",           v_cu_r,                                 u_cu_r),
        ("Rendimento (eta)",                                      f"{eta:.3f}",                           "%"),
    ]
    zebra_table(pdf, kpi_rows, col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])
    pdf.ln(6)

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 6 — GRAFICOS DE SIMULACAO (agrupados por afinidade)
    # ══════════════════════════════════════════════════════════════════════
    import matplotlib.pyplot as plt

    # grupos de afinidade — variáveis correlatas ficam na mesma página
    AFFINITY_GROUPS = [
        ["Te", "n", "wr"],           # mecânicas
        ["ias", "ibs", "ics"],       # correntes estator abc
        ["iar", "ibr", "icr"],       # correntes rotor abc
        ["ids", "iqs"],              # correntes estator dq
        ["idr", "iqr"],              # correntes rotor dq
        ["Va", "Vb", "Vc"],          # tensoes abc
    ]

    # distribui as var_keys selecionadas nos grupos, na ordem dos grupos
    def _make_chunks(keys, labels):
        key_to_lbl = dict(zip(keys, labels))
        chunks_out = []
        assigned   = set()
        for grp in AFFINITY_GROUPS:
            ck = [k for k in grp if k in key_to_lbl and k not in assigned]
            if ck:
                chunks_out.append((ck, [key_to_lbl[k] for k in ck]))
                assigned.update(ck)
        # variaveis nao pertencentes a nenhum grupo: chunks de 4
        rest_k = [k for k in keys if k not in assigned]
        rest_l = [key_to_lbl[k] for k in rest_k]
        for i in range(0, len(rest_k), 4):
            chunks_out.append((rest_k[i:i+4], rest_l[i:i+4]))
        return chunks_out if chunks_out else [(keys, labels)]

    chunks = _make_chunks(var_keys, var_labels)

    for page_idx, (chunk_keys, chunk_labels) in enumerate(chunks):
        pdf.add_page()
        suffix = f" ({page_idx+1}/{len(chunks)})" if len(chunks) > 1 else ""
        section_title(pdf, f"6. Curvas Características de Operação{suffix}")
        pdf.ln(2)

        page_fig = _build_pdf_page_fig(res, chunk_keys, chunk_labels,
                                        t_events, color_offset=page_idx * 4)
        img_buf = io.BytesIO()
        page_fig.savefig(img_buf, format="png", dpi=200, bbox_inches="tight",
                         facecolor="white")
        plt.close(page_fig)
        img_buf.seek(0)

        with tempfile_ctx() as tmp_path:
            with open(tmp_path, "wb") as f_tmp:
                f_tmp.write(img_buf.read())
            img_print_w = 170
            pdf.image(tmp_path, x=(210 - img_print_w) / 2, w=img_print_w)

        fig_num = page_idx + 2   # Figura 1 é o circuito
        lbl_vars = ", ".join(chunk_labels)
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, f"Figura {fig_num}: {lbl_vars}",
                 border=0, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 6 — RESULTADOS PRINCIPAIS (caixa de destaque)
    # ══════════════════════════════════════════════════════════════════════
    if pdf.get_y() > 210:
        pdf.add_page()

    BOX_X  = 20
    BOX_W  = 170
    BOX_H  = 38          # altura total da caixa
    BOX_Y  = pdf.get_y() + 4
    PAD    = 5
    col_w3 = BOX_W / 3   # tres colunas iguais sem padding lateral extra

    v_perd, u_perd = fmt_power(P_cu_r)

    highlights = [
        ("Eficiencia",        f"{eta:.2f}",        "%",   "eta"),
        ("Perdas no Rotor",   v_perd,               u_perd,"P_cu_r"),
        ("Escorregamento",    f"{s*100:.3f}",        "%",   "s"),
    ]

    # ── borda externa azul-escura ─────────────────────────────────────────
    pdf.set_draw_color(25, 60, 140)
    pdf.set_fill_color(240, 244, 255)
    pdf.rect(BOX_X, BOX_Y, BOX_W, BOX_H, style="FD")

    # ── faixa de titulo azul solida ───────────────────────────────────────
    TITLE_H = 10
    pdf.set_fill_color(25, 60, 140)
    pdf.set_draw_color(25, 60, 140)
    pdf.rect(BOX_X, BOX_Y, BOX_W, TITLE_H, style="F")

    pdf.set_xy(BOX_X + PAD, BOX_Y + 1.5)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(BOX_W - PAD*2, 7, "7. Resultados Principais", border=0)

    # ── tres cards internos ───────────────────────────────────────────────
    CARD_Y    = BOX_Y + TITLE_H + 2
    INNER_PAD = 4

    for i, (label, value, unit, _) in enumerate(highlights):
        cx = BOX_X + i * col_w3

        # separador vertical entre cards (exceto no primeiro)
        if i > 0:
            pdf.set_draw_color(180, 195, 230)
            pdf.line(cx, BOX_Y + TITLE_H + 2, cx, BOX_Y + BOX_H - 2)

        # label + valor + unidade numa linha so
        pdf.set_xy(cx + INNER_PAD, CARD_Y + 2)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(60, 80, 140)
        pdf.cell(col_w3 - INNER_PAD*2, 4, label, border=0, align="C")

        pdf.set_xy(cx + INNER_PAD, CARD_Y + 7)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(15, 40, 100)
        pdf.cell(col_w3 - INNER_PAD*2, 8, f"{value} {unit}", border=0, align="C")

    # ── nota metodologica (fora da caixa) ────────────────────────────────
    pdf.set_xy(BOX_X, BOX_Y + BOX_H + 3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(110, 110, 130)
    pdf.cell(BOX_W, 5,
             "Valores calculados sobre o regime permanente (detecção automática de convergência) "
             "via integração RK4 do modelo 0dq de Krause.",
             border=0, align="C")

    def _mpl_fig_to_pdf(mpl_fig, pdf_obj, width_mm=170):
        """Salva figura matplotlib como PNG e insere no PDF."""
        buf = io.BytesIO()
        mpl_fig.savefig(buf, format="png", dpi=180, bbox_inches="tight", facecolor="white")
        plt.close(mpl_fig)
        buf.seek(0)
        with tempfile_ctx() as tmp:
            with open(tmp, "wb") as f_tmp:
                f_tmp.write(buf.read())
            pdf_obj.image(tmp, x=(210 - width_mm) / 2, w=width_mm)

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 8 — CURVA T×n
    # ══════════════════════════════════════════════════════════════════════
    from curva_tn import calc_curva_tn, _torque_array, _extract_params
    pdf.add_page()
    section_title(pdf, "8. Curva Caracteristica T×n")
    pdf.ln(2)
    tn = calc_curva_tn(mp)
    # Ponto de operação calculado pelo próprio modelo do circuito equivalente
    # (usando o escorregamento s da simulação), garantindo que fique na curva.
    s_op = float(res.get("s", 0.0)) if "s" in res else None
    if s_op is not None and abs(s_op) > 1e-9:
        V1, R1, X1, R2, X2, Xm, ws_mec, ns_param = _extract_params(mp)
        Te_op = float(_torque_array(np.array([s_op]), V1, R1, X1, R2, X2, Xm, ws_mec)[0])
        n_op  = ns_param * (1.0 - s_op)
    else:
        Te_op = None
        n_op  = None

    # figura matplotlib da curva T×n
    fig_tn, ax_tn = plt.subplots(figsize=(10, 4.2))
    fig_tn.patch.set_facecolor("white")
    ns      = tn["n_sinc"]
    s_arr   = tn["s"]
    Te_arr  = tn["Te"]
    n_pct   = tn["n_rpm"] / ns * 100.0
    mask_m  = (s_arr > 0) & (s_arr <= 1.0)
    mask_g  = s_arr < 0
    mask_b  = s_arr > 1.0
    ax_tn.plot(n_pct[mask_m], Te_arr[mask_m], color="#1d4ed8", lw=2,   label="Motor (0<s<=1)")
    ax_tn.plot(n_pct[mask_g], Te_arr[mask_g], color="#059669", lw=2,   label="Gerador (s<0)")
    ax_tn.plot(n_pct[mask_b], Te_arr[mask_b], color="#dc2626", lw=2,   label="Frenagem (s>1)")
    ax_tn.plot(tn["n_max"] / ns * 100.0, tn["Te_max"], "o", color="#1d4ed8", ms=8,
               label=f"Te,max = {tn['Te_max']:.1f} N.m")
    ax_tn.plot(0.0, tn["Te_part"], "s", color="#1d4ed8", ms=7, fillstyle="none",
               label=f"Te,p = {tn['Te_part']:.1f} N.m")
    if Te_op is not None and n_op is not None:
        ax_tn.plot(n_op / ns * 100.0, Te_op, "D", color="#d97706", ms=9,
                   label=f"Operacao: {Te_op:.1f} N.m")
    ax_tn.axvline(x=100.0, color="#9ca3af", lw=1, ls="--")
    ax_tn.set_xlabel("Velocidade (% da velocidade sincrona)", fontsize=9)
    ax_tn.set_ylabel("Torque eletromagnetico Te (N.m)", fontsize=9)
    ax_tn.set_title("Curva Caracteristica T×n — Tres Regioes de Operacao", fontsize=10)
    ax_tn.legend(fontsize=7, loc="upper right")
    ax_tn.grid(True, color="#e5e7eb", lw=0.5)
    ax_tn.set_facecolor("#f9fafc")
    ax_tn.spines[["top", "right"]].set_visible(False)
    fig_tn.tight_layout()
    _mpl_fig_to_pdf(fig_tn, pdf)

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5,
             f"Te,max = {tn['Te_max']:.2f} N.m | Te,partida = {tn['Te_part']:.2f} N.m | s(Te,max) = {tn['s_max']*100:.2f}%",
             border=0, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_fill_color(200, 210, 240)
    pdf.set_text_color(20, 20, 80)
    pdf.set_font("Helvetica", "B", 10)
    for lbl, w in [("  Grandeza", 110), ("Valor", 35), ("Unidade", 25)]:
        pdf.cell(w, 7, lbl, border=0, fill=True)
    pdf.ln(7)
    tn_rows = [
        ("Torque Maximo (pull-out)",      f"{tn['Te_max']:.4f}",     "N.m"),
        ("Torque de Partida (s=1)",        f"{tn['Te_part']:.4f}",    "N.m"),
        ("Escorregamento em Te,max",       f"{tn['s_max']*100:.3f}",  "%"),
        ("Velocidade em Te,max",           f"{tn['n_max']:.1f}",      "RPM"),
        ("Velocidade Sincrona",            f"{tn['n_sinc']:.1f}",     "RPM"),
    ]
    if Te_op is not None:
        tn_rows.append(("Torque de regime (simulacao)", f"{Te_op:.4f}", "N.m"))
    zebra_table(pdf, tn_rows, col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 9 — FLUXO DE POTENCIA
    # ══════════════════════════════════════════════════════════════════════
    from curva_tn import calc_fluxo_potencia
    s_op = float(res.get("s", 0.0))
    if abs(s_op) > 1e-6:
        pdf.add_page()
        section_title(pdf, "9. Fluxo de Potencia no Ponto de Operacao")
        pdf.ln(2)
        fp = calc_fluxo_potencia(s_op, mp)

        # figura matplotlib do fluxo de potência
        fp_labels = ["Pin", "Pcu1\n(cobre est.)", "Pag\n(entreferro)",
                     "Pcu2\n(cobre rot.)", "Pmec\n(mecanica)", "Pout\n(saida)"]
        fp_values = [fp["P_in"], fp["P_cu1"], fp["P_ag"], fp["P_cu2"], fp["P_mec"], fp["P_out"]]
        fp_colors = ["#64748b", "#dc2626", "#1d4ed8", "#dc2626", "#059669", "#065f46"]
        fig_fp, ax_fp = plt.subplots(figsize=(10, 3.2))
        fig_fp.patch.set_facecolor("white")
        bars = ax_fp.barh(fp_labels, fp_values, color=fp_colors, height=0.55)
        for bar, val in zip(bars, fp_values):
            ax_fp.text(bar.get_width() + max(fp_values) * 0.01, bar.get_y() + bar.get_height() / 2,
                       f"{val:,.1f} W", va="center", fontsize=8)
        ax_fp.set_xlabel("Potencia (W)", fontsize=9)
        ax_fp.set_title(f"Fluxo de Potencia — {fp['region']} | eta = {fp['eta']:.1f}%", fontsize=10)
        ax_fp.invert_yaxis()
        ax_fp.grid(True, axis="x", color="#e5e7eb", lw=0.5)
        ax_fp.set_facecolor("#f9fafc")
        ax_fp.spines[["top", "right"]].set_visible(False)
        fig_fp.tight_layout()
        _mpl_fig_to_pdf(fig_fp, pdf)

        pdf.ln(5)
        pdf.set_fill_color(200, 210, 240)
        pdf.set_text_color(20, 20, 80)
        pdf.set_font("Helvetica", "B", 10)
        for lbl, w in [("  Grandeza", 110), ("Valor", 35), ("Unidade", 25)]:
            pdf.cell(w, 7, lbl, border=0, fill=True)
        pdf.ln(7)
        v_in,  u_in  = fmt_power(fp["P_in"])
        v_ag,  u_ag  = fmt_power(fp["P_ag"])
        v_mec, u_mec = fmt_power(fp["P_mec"])
        v_out, u_out = fmt_power(fp["P_out"])
        fp_rows = [
            ("Regiao de Operacao",              fp["region"],              "-"),
            ("Escorregamento (s)",               f"{fp['slip']*100:.3f}",   "%"),
            ("Potencia de Entrada (Pin)",        v_in,                      u_in),
            ("Perda no Cobre Estator (Pcu1)",    f"{fp['P_cu1']:.2f}",      "W"),
            ("Potencia no Entreferro (Pag)",     v_ag,                      u_ag),
            ("Perda no Cobre Rotor (Pcu2)",      f"{fp['P_cu2']:.2f}",      "W"),
            ("Potencia Mecanica (Pmec)",          v_mec,                     u_mec),
            ("Potencia de Saida (Pout)",         v_out,                     u_out),
            ("Rendimento (eta)",                 f"{fp['eta']:.2f}",        "%"),
            ("Corrente de Estator I1 (RMS)",     f"{fp['I1_rms']:.4f}",     "A"),
            ("Corrente de Rotor I2 (RMS)",       f"{fp['I2_rms']:.4f}",     "A"),
        ]
        zebra_table(pdf, fp_rows, col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])

    # ══════════════════════════════════════════════════════════════════════
    # SECAO 10 — ANALISE HARMONICA (FFT)
    # ══════════════════════════════════════════════════════════════════════
    ac_keys = [k for k in var_keys
               if k in ("ias", "ibs", "ics", "iar", "ibr", "icr", "Va", "Vb", "Vc")]
    if ac_keys:
        pdf.add_page()
        section_title(pdf, "10. Analise Harmonica (FFT)")
        pdf.ln(2)
        key_to_lbl = dict(zip(var_keys, var_labels))
        ss_start = int(res.get("_ss_start", 0))
        for fft_key in ac_keys[:4]:
            lbl = _safe(key_to_lbl.get(fft_key, fft_key))
            y   = np.asarray(res[fft_key][ss_start:], dtype=float)
            t   = np.asarray(res["t"][ss_start:],     dtype=float)
            if len(y) < 4:
                continue
            dt   = float(t[1] - t[0]) if len(t) > 1 else 1e-3
            N    = len(y)
            yf   = np.abs(np.fft.rfft(y)) * 2.0 / N
            freq = np.fft.rfftfreq(N, d=dt)
            mask = freq <= 2000
            freq, yf = freq[mask], yf[mask]
            f1_idx     = int(np.argmax(yf[freq > 0.1])) + np.searchsorted(freq, 0.1)
            f1         = float(freq[f1_idx]) if f1_idx < len(freq) else 60.0
            harm_freqs = [f1 * k for k in [1, 3, 5, 7, 9] if f1 * k <= freq[-1]]

            fig_fft, ax_fft = plt.subplots(figsize=(10, 2.8))
            fig_fft.patch.set_facecolor("white")
            ax_fft.bar(freq, yf, width=(freq[1]-freq[0]) if len(freq)>1 else 1,
                       color="#1d4ed8", alpha=0.8)
            for hf in harm_freqs:
                ax_fft.axvline(x=hf, color="#dc2626", lw=1.0, ls="--")
                ax_fft.text(hf, ax_fft.get_ylim()[1] * 0.9, f"{hf:.0f}Hz",
                            color="#dc2626", fontsize=6, ha="center")
            ax_fft.set_xlabel("Frequencia (Hz)", fontsize=9)
            ax_fft.set_ylabel("Amplitude", fontsize=9)
            ax_fft.set_title(f"Espectro de Amplitudes — {lbl}", fontsize=9)
            ax_fft.set_facecolor("#f9fafc")
            ax_fft.grid(True, color="#e5e7eb", lw=0.5)
            ax_fft.spines[["top", "right"]].set_visible(False)
            fig_fft.tight_layout()
            _mpl_fig_to_pdf(fig_fft, pdf)

            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 5, f"Espectro — {lbl}",
                     border=0, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

    return bytes(pdf.output())


def tempfile_ctx():
    """Context manager simples para arquivo temporario PNG."""
    import tempfile, os
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            yield path
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
    return _ctx()
