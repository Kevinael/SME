from __future__ import annotations
import io
import numpy as np
from EMS_PY import MachineParams
from eqcircuit_plotter import build_figure as _build_circuit_figure
from theme import _palette


_DASH_MAP = {"dash": "--", "dot": ":", "solid": "-"}


def _build_pdf_page_fig(res: dict, var_keys: list, var_labels: list,
                         t_events: list, color_offset: int = 0,
                         ref_list=None) -> "matplotlib.figure.Figure":
    """Gera uma figura matplotlib com até N subplots para uma página do PDF.

    ref_list: lista de {"res", "color", "dash", "label"} para sobreposição.
    Quando presente, suprime as anotações de pico/regime e mostra legenda.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    COLORS = ["#1d4ed8","#ea580c","#16a34a","#7c3aed",
              "#db2777","#0d9488","#d97706","#4f46e5",
              "#65a30d","#dc2626","#0891b2","#c026d3"]

    has_refs = bool(ref_list)
    n   = max(1, len(var_keys))
    t   = res["t"]
    fig, axes = plt.subplots(n, 1, figsize=(11, 3.2 * n), sharex=True)
    if n == 1:
        axes = [axes]

    fig.patch.set_facecolor("white")

    for i, (key, lbl, ax) in enumerate(zip(var_keys, var_labels, axes)):
        color = COLORS[(i + color_offset) % len(COLORS)]

        # ── referências (atrás da curva principal) ────────────────────────
        for ref_item in (ref_list or []):
            res_ref   = ref_item.get("res")
            ref_color = ref_item.get("color", "#888888")
            ref_dash  = ref_item.get("dash", "dash")
            ref_label = ref_item.get("label", "Referência")
            if res_ref is not None and key in res_ref and "t" in res_ref:
                ls = _DASH_MAP.get(ref_dash, "--")
                ax.plot(res_ref["t"], np.asarray(res_ref[key]),
                        color=ref_color, linewidth=0.9, linestyle=ls,
                        label=ref_label, alpha=0.85)

        # ── curva principal ───────────────────────────────────────────────
        y = np.asarray(res[key])
        ax.plot(t, y, color=color, linewidth=1.2, solid_capstyle="round",
                label="Atual" if has_refs else "_nolegend_")

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

        if has_refs:
            # modo sobreposição: legenda compacta, sem anotações de pico
            ax.legend(fontsize=6, loc="upper right", framealpha=0.85,
                      ncol=min(len(ref_list) + 1, 3))
        else:
            # modo isolado: anotações de pico e regime permanente
            pk_idx = int(np.argmax(np.abs(y)))
            t_pk   = float(t[pk_idx])
            y_pk   = float(np.abs(y[pk_idx]))
            ax.plot(t_pk, y_pk, "^", color="#dc2626", markersize=6, zorder=5,
                    label=f"Pico: {y_pk:.2f}")
            rms_key  = key + "_rms"
            y_ss_rms = float(res[rms_key]) if rms_key in res else float(np.abs(y[-1]))
            ss_start = int(res.get("_ss_start", len(y) - 1))
            y_ss_mid = float(np.mean(y[ss_start:]))
            t_ss     = float(t[ss_start + (len(y) - ss_start) // 2])
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
                        exp_type: str = "dol",
                        ref_list: list | None = None) -> bytes:
    """Gera o relatório técnico em PDF e retorna como bytes (stream).

    Estrutura:
      • Bloco completo para a simulação atual (Identificação → Curvas)
      • Bloco completo para cada referência salva (mesma estrutura)
      • Seção final: todos os gráficos sobrepostos (atual + referências)
    """
    from fpdf import FPDF
    import datetime
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    var_labels = var_labels or var_keys
    t_events   = t_events   or []

    # ── Mapa de substituição Unicode → latin-1 ───────────────────────────────
    _UNICODE_SAFE = {
        '\u2014': '-',  '\u2013': '-',
        '\u2091': 'e',  '\u2090': 'a',
        '\u209B': 's',  '\u1D63': 'r',
        '\u2080': '0',  '\u2081': '1',  '\u2082': '2',  '\u2083': '3',
        '\u2084': '4',  '\u2085': '5',  '\u2086': '6',  '\u2087': '7',
        '\u2088': '8',  '\u2089': '9',
        '\u00B7': '.',
        '\u03C9': 'w',  '\u03B1': 'a',  '\u03B2': 'b',  '\u03B7': 'n',
        '\u03C3': 's',  '\u03C6': 'phi', '\u03BB': 'lambda',
    }

    def _safe(text: str) -> str:
        for ch, repl in _UNICODE_SAFE.items():
            text = text.replace(ch, repl)
        return text.encode('latin-1', errors='ignore').decode('latin-1')

    # ── Subclasse com cabeçalho e rodapé automáticos ─────────────────────
    class EMS_PDF(FPDF):
        def normalize_text(self, text: str) -> str:
            return super().normalize_text(_safe(text))

        def header(self):
            self.set_fill_color(230, 230, 230)
            self.rect(0, 0, 210, 18, style="F")
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(30, 30, 30)
            self.set_xy(20, 4)
            self.cell(120, 10, "EMS - RELATÓRIO TÉCNICO DE SIMULAÇÃO", border=0)
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

    # ── Helpers ───────────────────────────────────────────────────────────
    def fmt_power(val: float) -> tuple[str, str]:
        if abs(val) >= 1000:
            return f"{val/1000:.3f}", "kW"
        return f"{val:.2f}", "W"

    AFFINITY_GROUPS = [
        ["Te", "n", "wr"],
        ["ias", "ibs", "ics"],
        ["iar", "ibr", "icr"],
        ["ids", "iqs"],
        ["idr", "iqr"],
        ["Va", "Vb", "Vc"],
    ]

    def _make_chunks(keys, labels):
        key_to_lbl = dict(zip(keys, labels))
        chunks_out, assigned = [], set()
        for grp in AFFINITY_GROUPS:
            ck = [k for k in grp if k in key_to_lbl and k not in assigned]
            if ck:
                chunks_out.append((ck, [key_to_lbl[k] for k in ck]))
                assigned.update(ck)
        rest_k = [k for k in keys if k not in assigned]
        rest_l = [key_to_lbl[k] for k in rest_k]
        for i in range(0, len(rest_k), 4):
            chunks_out.append((rest_k[i:i+4], rest_l[i:i+4]))
        return chunks_out if chunks_out else [(keys, labels)]

    def _mpl_to_pdf(mpl_fig, width_mm=170):
        buf = io.BytesIO()
        mpl_fig.savefig(buf, format="png", dpi=200, bbox_inches="tight",
                        facecolor="white")
        plt.close(mpl_fig)
        buf.seek(0)
        with tempfile_ctx() as tmp:
            with open(tmp, "wb") as f_tmp:
                f_tmp.write(buf.read())
            pdf.image(tmp, x=(210 - width_mm) / 2, w=width_mm)

    # ── Banner separador de bloco ─────────────────────────────────────────
    def _block_banner(text: str) -> None:
        pdf.add_page()
        pdf.set_fill_color(15, 40, 100)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 14, f"  {text}", border=0, fill=True, ln=True)
        pdf.ln(4)

    # ══════════════════════════════════════════════════════════════════════
    # BLOCO DE SIMULAÇÃO — escreve identificação + valores + circuito +
    #                      destaques + regime + curvas para um resultado
    # ══════════════════════════════════════════════════════════════════════
    def _write_block(b_res, b_mp, b_exp_label, b_exp_type, b_t_events,
                     b_var_keys, b_var_labels):

        # ── Identificação ──────────────────────────────────────────────────
        section_title(pdf, "Identificação do Experimento")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(50, 7, "  Tipo de experimento:", border=0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, b_exp_label, border=0, ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(50, 7, "  Velocidade síncrona:", border=0)
        pdf.cell(0, 7,
                 f"{b_mp.n_sync:.1f} RPM  |  {b_mp.wb/(b_mp.p/2.0):.3f} rad/s",
                 border=0, ln=True)
        pdf.cell(50, 7, "  Frequência nominal:", border=0)
        pdf.cell(0, 7,
                 f"{b_mp.f:.1f} Hz  |  n_s = {b_mp.n_sync:.1f} RPM",
                 border=0, ln=True)
        pdf.ln(5)

        # ── Valores Nominais ───────────────────────────────────────────────
        section_title(pdf, "Valores Nominais da Máquina")
        pdf.set_fill_color(200, 210, 240)
        pdf.set_text_color(20, 20, 80)
        pdf.set_font("Helvetica", "B", 10)
        for lbl, w in [("  Parâmetro", 110), ("Valor", 35), ("Unidade", 25)]:
            pdf.cell(w, 7, lbl, border=0, fill=True)
        pdf.ln(7)
        zebra_table(pdf, [
            ("Tensão de linha (V[sub]l[/sub])",                 f"{b_mp.Vl:.1f}",  "V"),
            ("Frequência (f)",                                   f"{b_mp.f:.1f}",   "Hz"),
            ("Resistência do estator (R[sub]s[/sub])",          f"{b_mp.Rs:.4f}",  "Ohm"),
            ("Resistência do rotor (R[sub]r[/sub])",            f"{b_mp.Rr:.4f}",  "Ohm"),
            ("Reatância de magnetização (X[sub]m[/sub])",       f"{b_mp.Xm:.4f}",  "Ohm"),
            ("Reatância de dispersão est. (X[sub]ls[/sub])",    f"{b_mp.Xls:.4f}", "Ohm"),
            ("Reatância de dispersão rot. (X[sub]lr[/sub])",    f"{b_mp.Xlr:.4f}", "Ohm"),
            ("Resistência de perdas no ferro (R[sub]fe[/sub])", f"{b_mp.Rfe:.1f}", "Ohm"),
            ("Número de polos (p)",                              f"{b_mp.p}",       "-"),
            ("Momento de inércia (J)",                           f"{b_mp.J:.4f}",   "kg.m²"),
            ("Coeficiente de atrito (B)",                        f"{b_mp.B:.4f}",   "N.m.s/rad"),
        ], col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])
        pdf.ln(6)

        # ── Circuito Equivalente ───────────────────────────────────────────
        # Mantém o circuito na mesma página que identificação e valores nominais.
        # Só quebra página se o espaço restante for insuficiente.
        CIRCUIT_MIN_HEIGHT = 85  # mm estimados: título + imagem + legenda
        space_left = (pdf.h - pdf.b_margin) - pdf.get_y()
        if space_left < CIRCUIT_MIN_HEIGHT:
            pdf.add_page()
        section_title(pdf, "Circuito Equivalente Monofásico em T")
        pdf.ln(2)
        circ_fig = _build_circuit_figure(b_mp, dark=False, palette_fn=_palette)
        circ_buf = io.BytesIO()
        circ_fig.savefig(circ_buf, format="png", dpi=200, bbox_inches="tight",
                         facecolor="white")
        plt.close(circ_fig)
        circ_buf.seek(0)
        with tempfile_ctx() as tmp_c:
            with open(tmp_c, "wb") as f_tmp:
                f_tmp.write(circ_buf.read())
            pdf.image(tmp_c, x=(210 - 170) / 2, w=170)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, "Circuito Equivalente Monofásico em T do MIT",
                 border=0, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # ── Destaques do Experimento ───────────────────────────────────────
        pdf.add_page()
        section_title(pdf, "Destaques do Experimento")

        def _kpis():
            ias_pk_  = float(np.max(np.abs(b_res["ias"])))
            Te_max_  = float(np.max(b_res["Te"]))
            n_ss_    = b_res["n_ss"]
            ias_rms_ = b_res["ias_rms"]
            s_val_   = b_res.get("s", 0.0)
            fator_   = ias_pk_ / ias_rms_ if ias_rms_ > 0 else 0.0
            if b_exp_type in ("dol", "yd", "comp", "soft"):
                rows_ = [
                    ("Corrente de Pico (i[sub]as,pk[/sub])",              f"{ias_pk_:.4f}",  "A"),
                    ("Fator de Pico (I[sub]pk[/sub]/I[sub]rms[/sub])",    f"{fator_:.4f}",   "-"),
                    ("Torque Máximo (T[sub]e,max[/sub])",                  f"{Te_max_:.4f}",  "N.m"),
                    ("Velocidade Final",                                    f"{n_ss_:.3f}",    "RPM"),
                ]
                if b_exp_type == "yd" and b_t_events:
                    t_ev_ = b_t_events[1] if len(b_t_events) > 1 else b_t_events[0]
                    idx_  = int(np.searchsorted(b_res["t"], t_ev_))
                    pk2_  = float(np.max(np.abs(b_res["ias"][idx_:]))) if idx_ < len(b_res["t"]) else 0.0
                    rows_.insert(1, ("Corrente de Pico pós Y-D (i[sub]as,pk2[/sub])", f"{pk2_:.4f}", "A"))
            elif b_exp_type == "carga":
                n_v_ = float(np.mean(b_res["n"][:max(1, len(b_res["n"])//5)]))
                iv_  = float(np.sqrt(np.mean(b_res["ias"][:max(1, len(b_res["ias"])//5)]**2)))
                rows_ = [
                    ("Velocidade em Vazio",           f"{n_v_:.3f}",             "RPM"),
                    ("Velocidade com Carga",           f"{n_ss_:.3f}",           "RPM"),
                    ("Afundamento de Velocidade",       f"{n_v_-n_ss_:.3f}",     "RPM"),
                    ("Variação de Corrente RMS",        f"{ias_rms_-iv_:.4f}",   "A"),
                ]
            elif b_exp_type == "gerador":
                P_o_ = b_res.get("P_out", 0.0)
                e_g_ = b_res.get("eta", 0.0)
                u_p_ = "kW" if abs(P_o_) >= 1000 else "W"
                v_p_ = P_o_ / 1000 if abs(P_o_) >= 1000 else P_o_
                rows_ = [
                    ("Potência Gerada (P[sub]out[/sub])",      f"{v_p_:.3f}",      u_p_),
                    ("Escorregamento (s)",                      f"{s_val_*100:.3f}", "%"),
                    ("Rendimento (eta)",                        f"{e_g_:.3f}",      "%"),
                    ("Corrente RMS (i[sub]as,rms[/sub])",       f"{ias_rms_:.4f}",  "A"),
                ]
            else:
                rows_ = []
            return rows_

        dest_rows = _kpis()
        if dest_rows:
            pdf.set_fill_color(200, 210, 240)
            pdf.set_text_color(20, 20, 80)
            pdf.set_font("Helvetica", "B", 10)
            for lbl, w in [("  Grandeza", 110), ("Valor", 35), ("Unidade", 25)]:
                pdf.cell(w, 7, lbl, border=0, fill=True)
            pdf.ln(7)
            zebra_table(pdf, dest_rows, col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])
            pdf.ln(6)

        # ── Indicadores de Regime Permanente ──────────────────────────────
        section_title(pdf, "Indicadores de Regime Permanente")
        pdf.set_fill_color(200, 210, 240)
        pdf.set_text_color(20, 20, 80)
        pdf.set_font("Helvetica", "B", 10)
        for lbl, w in [("  Grandeza", 110), ("Valor", 35), ("Unidade", 25)]:
            pdf.cell(w, 7, lbl, border=0, fill=True)
        pdf.ln(7)
        P_gap_  = b_res.get("P_gap",  0.0)
        P_mec_  = b_res.get("P_mec",  0.0)
        P_cu_r_ = b_res.get("P_cu_r", 0.0)
        eta_    = b_res.get("eta",    0.0)
        s_      = b_res.get("s",      0.0)
        P_in_   = b_res.get("P_in",   0.0)
        vi, ui   = fmt_power(P_in_)
        vg, ug   = fmt_power(P_gap_)
        vm, um   = fmt_power(P_mec_)
        vcr, ucr = fmt_power(P_cu_r_)
        zebra_table(pdf, [
            ("Velocidade de regime",                                  f"{b_res['n_ss']:.3f}",                       "RPM"),
            ("Vel. angular do rotor (w[sub]r[/sub])",                 f"{b_res['wr_ss']:.4f}",                      "rad/s"),
            ("Torque eletromagnético de regime (T[sub]e[/sub])",      f"{b_res['Te_ss']:.4f}",                      "N.m"),
            ("Torque eletromagnético máximo (T[sub]e,max[/sub])",     f"{float(np.max(b_res['Te'])):.4f}",          "N.m"),
            ("Escorregamento (s)",                                     f"{s_*100:.3f}",                              "%"),
            ("Corrente RMS fase A (i[sub]as,rms[/sub])",              f"{b_res['ias_rms']:.4f}",                    "A"),
            ("Corrente RMS fase B (i[sub]bs,rms[/sub])",              f"{b_res['ibs_rms']:.4f}",                    "A"),
            ("Corrente RMS fase C (i[sub]cs,rms[/sub])",              f"{b_res['ics_rms']:.4f}",                    "A"),
            ("Corrente de pico fase A (i[sub]as,pk[/sub])",           f"{float(np.max(np.abs(b_res['ias']))):.4f}", "A"),
            ("Corrente de pico fase B (i[sub]bs,pk[/sub])",           f"{float(np.max(np.abs(b_res['ibs']))):.4f}", "A"),
            ("Corrente de pico fase C (i[sub]cs,pk[/sub])",           f"{float(np.max(np.abs(b_res['ics']))):.4f}", "A"),
            ("Potência de entrada (P[sub]in[/sub])",                  vi, ui),
            ("Potência no entreferro (P[sub]gap[/sub])",              vg, ug),
            ("Potência mecânica (P[sub]mec[/sub])",                   vm, um),
            ("Perdas no cobre do rotor (P[sub]cu,r[/sub])",           vcr, ucr),
            ("Rendimento (eta)",                                       f"{eta_:.3f}", "%"),
        ], col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])
        pdf.ln(6)

        # ── Curvas Características ─────────────────────────────────────────
        b_chunks = _make_chunks(b_var_keys, b_var_labels)
        for pg, (ck, cl) in enumerate(b_chunks):
            pdf.add_page()
            sfx = f" ({pg+1}/{len(b_chunks)})" if len(b_chunks) > 1 else ""
            section_title(pdf, f"Curvas Características{sfx}")
            pdf.ln(2)
            _mpl_to_pdf(_build_pdf_page_fig(b_res, ck, cl, b_t_events, color_offset=pg * 4))
            pdf.ln(2)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 5, ", ".join(cl),
                     border=0, align="C", new_x="LMARGIN", new_y="NEXT")

    # ══════════════════════════════════════════════════════════════════════
    # INICIALIZA PDF
    # ══════════════════════════════════════════════════════════════════════
    pdf = EMS_PDF()
    pdf.alias_nb_pages()
    pdf.set_margins(left=20, top=24, right=20)
    pdf.set_auto_page_break(auto=True, margin=18)

    # ── Bloco: Simulação Atual ─────────────────────────────────────────────
    _block_banner("Simulação Atual")
    _write_block(res, mp, exp_label, exp_type, t_events, var_keys, var_labels)

    # ── Bloco: cada Referência ─────────────────────────────────────────────
    for ref_i, r in enumerate(ref_list or []):
        ref_res = r.get("res")
        if ref_res is None:
            continue
        ref_mp        = r.get("mp", mp)
        ref_label     = r.get("exp_label", f"Referência {ref_i+1}")
        ref_exp_type  = r.get("exp_type", "dol")
        ref_t_events  = r.get("t_events", [])
        ref_var_keys  = r.get("var_keys") or var_keys
        ref_var_labels= r.get("var_labels") or var_labels
        _block_banner(f"Referência {ref_i+1} — {ref_label}")
        _write_block(ref_res, ref_mp, ref_label, ref_exp_type, ref_t_events,
                     ref_var_keys, ref_var_labels)

    # ── Seção Final: Gráficos Sobrepostos ─────────────────────────────────
    if ref_list:
        chart_refs = [
            {
                "res":   r["res"],
                "color": r.get("color", "#888888"),
                "dash":  r.get("dash", "dash"),
                "label": r.get("exp_label", "Referência"),
            }
            for r in ref_list if r.get("res") is not None
        ]
        if chart_refs:
            main_chunks = _make_chunks(var_keys, var_labels)
            for pg, (ck, cl) in enumerate(main_chunks):
                valid_k = [k for k in ck if k in res]
                if not valid_k:
                    continue
                valid_l = [cl[ck.index(k)] for k in valid_k]
                pdf.add_page()
                sfx = f" ({pg+1}/{len(main_chunks)})" if len(main_chunks) > 1 else ""
                section_title(pdf, f"Curvas Comparativas — Sobrepostas{sfx}")
                pdf.ln(2)
                _mpl_to_pdf(_build_pdf_page_fig(
                    res, valid_k, valid_l, t_events,
                    color_offset=pg * 4, ref_list=chart_refs,
                ))
                pdf.ln(2)
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(80, 80, 80)
                names = "Atual vs. " + ", ".join(r["label"] for r in chart_refs)
                pdf.cell(0, 5, names,
                         border=0, align="C", new_x="LMARGIN", new_y="NEXT")

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
