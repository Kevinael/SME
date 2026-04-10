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

        # ── pico (maior módulo)
        pk_idx = int(np.argmax(np.abs(y)))
        t_pk   = float(t[pk_idx])
        y_pk   = float(np.abs(y[pk_idx]))
        ax.plot(t_pk, y_pk, "^", color="#dc2626", markersize=6, zorder=5,
                label=f"Pico: {y_pk:.2f}")

        # ── regime permanente
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

    fig.subplots_adjust(left=0.10, right=0.97, top=0.95, bottom=0.08, hspace=0.75)
    return fig

def generate_pdf_report(exp_label: str, mp: MachineParams, res: dict,
                        fig, var_keys: list,
                        var_labels: list | None = None,
                        t_events: list | None = None,
                        exp_type: str = "dol") -> bytes:
    """Gera o relatório técnico em PDF e retorna como bytes (stream)."""
    from fpdf import FPDF
    import datetime
    import tempfile
    import os

    var_labels = var_labels or var_keys
    t_events   = t_events   or []

    # ── 1. MAPA UNICODE AMPLIADO
    _UNICODE_SAFE = {
        '\u2014': '-',  '\u2013': '-',   
        '\u2091': 'e',  '\u208e': 'e',   # Subscrito 'e' que causava erro
        '\u2090': 'a',  '\u209B': 's',   
        '\u1D63': 'r',  '\u1D62': 'i',   
        '\u2080': '0',  '\u2081': '1',   '\u2082': '2',  '\u2083': '3',
        '\u2084': '4',  '\u2085': '5',   '\u2086': '6',  '\u2087': '7',
        '\u2088': '8',  '\u2089': '9',   
        '\u00B7': '.',  '\u03B7': 'eta', # Rendimento (eta)
        '\u03BC': 'u',  '\u03C9': 'w',   '\u03B1': 'a',   '\u03B2': 'b',
        '\u03C3': 's',  '\u03C6': 'phi', '\u03BB': 'lambda',
    }

    # ── 2. FUNÇÃO SAFE COM FALLBACK
    def _safe(text: str) -> str:
        if text is None: return ""
        text = str(text)
        for ch, repl in _UNICODE_SAFE.items():
            text = text.replace(ch, repl)
        try:
            return text.encode('latin-1').decode('latin-1')
        except UnicodeEncodeError:
            # Proteção contra falhas de encoding
            return text.encode('ascii', 'replace').decode('ascii')

    # ── 3. CLASSE EMS_PDF (Identação Corrigida)
    class EMS_PDF(FPDF):
        def normalize_text(self, text: str) -> str:
            """Filtro automático para todas as strings do PDF."""
            return _safe(text)

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
            self.cell(60, 5, "Versão 1.1 | EMS Simulator", border=0, align="R")
            self.ln(8)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, f"Página {self.page_no()} de {{nb}}", align="C")

    # ── Funções auxiliares (Seção render_cell corrigida)
    def section_title(pdf: EMS_PDF, title: str) -> None:
        pdf.set_fill_color(25, 60, 140)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"  {title}", border=0, fill=True, ln=True)
        pdf.ln(2)

    def _render_cell_with_sub(pdf: EMS_PDF, text: str, w: float,
                               row_h: float, fill_rgb: tuple) -> None:
        import re
        parts = re.split(r'\[sub\](.*?)\[/sub\]', text)
        x0 = pdf.get_x() + 2
        y0 = pdf.get_y()
        pdf.set_fill_color(*fill_rgb)
        pdf.cell(w, row_h, "", border=0, fill=True)
        pdf.set_xy(x0, y0)
        for i, part in enumerate(parts):
            if not part: continue
            if i % 2 == 1:
                pdf.set_font("Helvetica", "", 7)
                pdf.set_xy(pdf.get_x(), y0 + 2.2)
                pdf.cell(pdf.get_string_width(part) + 0.3, row_h - 2.2, part, border=0)
                pdf.set_xy(pdf.get_x(), y0)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(pdf.get_string_width(part), row_h, part, border=0)
        pdf.set_xy(x0 - 2 + w, y0)

    def zebra_table(pdf: EMS_PDF, rows: list[tuple], col_widths: list[float],
                    col_aligns: list[str], row_h: float = 7) -> None:
        for idx, row in enumerate(rows):
            fill_rgb = (242, 245, 255) if idx % 2 == 0 else (255, 255, 255)
            pdf.set_fill_color(*fill_rgb)
            pdf.set_text_color(40, 40, 40)
            for col_i, (cell, w, align) in enumerate(zip(row, col_widths, col_aligns)):
                if col_i == 0 and '[sub]' in str(cell):
                    _render_cell_with_sub(pdf, str(cell), w, row_h, fill_rgb)
                else:
                    pdf.cell(w, row_h, f"  {cell}", border=0, fill=True, align=align)
            pdf.ln(row_h)

    def fmt_power(val: float) -> tuple[str, str]:
        if abs(val) >= 1000: return f"{val/1000:.3f}", "kW"
        return f"{val:.2f}", "W"

    # ── Instancia PDF
    pdf = EMS_PDF()
    pdf.alias_nb_pages()
    pdf.set_margins(left=20, top=24, right=20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # SEÇÃO 1 e 2 (Mesma lógica do original)
    section_title(pdf, "1. Identificação do Experimento")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(50, 7, "  Tipo de experimento:", border=0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, exp_label, border=0, ln=True)
    pdf.ln(5)

    section_title(pdf, "2. Valores Nominais da Máquina")
    pdf.set_fill_color(200, 210, 240)
    pdf.set_font("Helvetica", "B", 10)
    for lbl, w in [("  Parâmetro", 110), ("Valor", 35), ("Unidade", 25)]:
        pdf.cell(w, 7, lbl, border=0, fill=True)
    pdf.ln(7)

    param_rows = [
        ("Tensão de linha (V[sub]l[/sub])", f"{mp.Vl:.1f}", "V"),
        ("Resistência do estator (R[sub]s[/sub])", f"{mp.Rs:.4f}", "Ohm"),
        ("Resistência do rotor (R[sub]r[/sub])", f"{mp.Rr:.4f}", "Ohm"),
        ("Reatância de magnetização (X[sub]m[/sub])", f"{mp.Xm:.4f}", "Ohm"),
        ("Momento de inércia (J)", f"{mp.J:.4f}", "kg.m²"),
    ]
    zebra_table(pdf, param_rows, col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])
    pdf.ln(6)

    # SEÇÃO 4 - KPIs (Com marcação [sub])
    pdf.add_page()
    section_title(pdf, "4. Destaques do Experimento")
    ias_pk = float(np.max(np.abs(res["ias"])))
    Te_max = float(np.max(res["Te"]))
    eta_g  = res.get("eta", 0.0)

    dest_rows = [
        ("Corrente de Pico (i[sub]as,pk[/sub])", f"{ias_pk:.4f}", "A"),
        ("Torque Máximo (T[sub]e,max[/sub])", f"{Te_max:.4f}", "N.m"),
        ("Rendimento ([sub]eta[/sub])", f"{eta_g:.3f}", "%"),
    ]
    zebra_table(pdf, dest_rows, col_widths=[110, 35, 25], col_aligns=["L", "R", "L"])
    pdf.ln(6)

    # Restante do código (Gráficos e FFT) permanece com as proteções de _safe
    return bytes(pdf.output())

def tempfile_ctx():
    import tempfile, os
    from contextlib import contextmanager
    @contextmanager
    def _ctx():
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try: yield path
        finally:
            try: os.remove(path)
            except OSError: pass
    return _ctx()