"""
clean_view.py
=============
Visualização limpa dos parâmetros de configuração para captura de tela / artigo.
Lê os dados de st.session_state (sim_result) — funciona somente após uma simulação.
"""
from __future__ import annotations
import streamlit as st


# ── helpers de formatação ────────────────────────────────────────────────────

def _row(name: str, symbol: str, value: str, unit: str = "", shade: bool = False) -> str:
    bg = "#f7f7f7" if shade else "#ffffff"
    sym = f'<span style="font-style:italic;">{symbol}</span>' if symbol else ""
    return (
        f'<tr style="background:{bg};">'
        f'  <td style="padding:7px 14px;border:1px solid #d0d0d0;">{name}</td>'
        f'  <td style="padding:7px 14px;border:1px solid #d0d0d0;text-align:center;width:60px;">{sym}</td>'
        f'  <td style="padding:7px 14px;border:1px solid #d0d0d0;text-align:right;width:110px;'
        f'      font-family:monospace;font-size:14px;">{value}</td>'
        f'  <td style="padding:7px 14px;border:1px solid #d0d0d0;width:50px;color:#555;">{unit}</td>'
        f'</tr>'
    )


def _section(title: str) -> str:
    return (
        f'<tr>'
        f'  <td colspan="4" style="padding:9px 14px;background:#1e293b;color:#ffffff;'
        f'      font-weight:600;font-size:13px;letter-spacing:0.06em;'
        f'      border:1px solid #1e293b;text-transform:uppercase;">'
        f'      {title}'
        f'  </td>'
        f'</tr>'
    )


def _fmt(v, decimals: int = 3) -> str:
    if isinstance(v, float):
        return f"{v:.{decimals}f}"
    return str(v)


# ── experimento → linhas de parâmetros ───────────────────────────────────────

def _exp_rows(cfg: dict) -> list[str]:
    rows = []
    et = cfg.get("exp_type", "dol")
    labels = {
        "dol":        "Partida Direta (DOL)",
        "yd":         "Estrela-Triângulo (Y-D)",
        "comp":       "Autotransformador",
        "soft":       "Soft-Starter (Rampa de Tensão)",
        "carga":      "Aplicação de Carga",
        "pulso_carga":"Pulso de Carga",
        "gerador":    "Operação como Gerador",
    }
    rows.append(_row("Tipo de experimento", "", labels.get(et, et), "", shade=False))

    if et in ("dol", "yd", "comp", "soft", "carga"):
        rows.append(_row("Torque de carga", "T<sub>L</sub>",
                         _fmt(cfg.get("Tl_final", 0.0), 2), "N·m", shade=True))
        rows.append(_row("Instante de aplicação da carga", "t<sub>c</sub>",
                         _fmt(cfg.get("t_carga", 0.0), 3), "s", shade=False))

    if et in ("yd", "comp", "soft", "gerador"):
        rows.append(_row("Instante de comutação / aplicação", "t<sub>2</sub>",
                         _fmt(cfg.get("t_2", 0.0), 3), "s", shade=True))

    if et in ("comp", "soft"):
        vr = cfg.get("voltage_ratio", 1.0)
        rows.append(_row("Tensão inicial (tap / rampa)", "V<sub>i</sub>",
                         f"{vr*100:.0f}", "%", shade=False))

    if et == "soft":
        rows.append(_row("Tempo para tensão nominal", "t<sub>p</sub>",
                         _fmt(cfg.get("t_pico", 0.0), 2), "s", shade=True))

    if et == "pulso_carga":
        rows.append(_row("Torque do pulso", "T<sub>L</sub>",
                         _fmt(cfg.get("Tl_final", 0.0), 2), "N·m", shade=True))
        rows.append(_row("Início do pulso", "t<sub>on</sub>",
                         _fmt(cfg.get("t_carga", 0.0), 3), "s", shade=False))
        rows.append(_row("Fim do pulso", "t<sub>off</sub>",
                         _fmt(cfg.get("t_retirada", 0.0), 3), "s", shade=True))

    if et == "gerador":
        rows.append(_row("Torque mecânico (turbina)", "T<sub>mec</sub>",
                         _fmt(cfg.get("Tl_mec", 0.0), 2), "N·m", shade=False))

    return rows


# ── renderizador principal ───────────────────────────────────────────────────

def render_clean_view() -> None:
    sr  = st.session_state.get("sim_result")
    if sr is None:
        st.info("Execute uma simulação primeiro para visualizar os parâmetros.")
        return

    mp       = sr["mp"]
    exp_cfg  = sr.get("exp_config", {})
    tmax     = sr.get("tmax", 0.0)
    h        = sr.get("h", 0.0)

    # ── modo de entrada dos parâmetros magnéticos ─────────────────────────
    im = getattr(mp, "input_mode", "X")
    if im == "L":
        mag_rows = [
            _row("Indutância de magnetização",         "L<sub>m</sub>",   f"{mp.Lm*1000:.4f}",  "mH",  shade=False),
            _row("Indutância de dispersão do estator", "L<sub>ls</sub>",  f"{mp.Lls*1000:.4f}", "mH",  shade=True),
            _row("Indutância de dispersão do rotor",   "L<sub>lr</sub>",  f"{mp.Llr*1000:.4f}", "mH",  shade=False),
        ]
    else:
        f_ref = getattr(mp, "f_ref", 60.0)
        mag_rows = [
            _row(f"Reatância de magnetização (a {f_ref:.0f} Hz)",         "X<sub>m</sub>",   f"{mp.Xm:.4f}",  "Ω",  shade=False),
            _row(f"Reatância de dispersão do estator (a {f_ref:.0f} Hz)", "X<sub>ls</sub>",  f"{mp.Xls:.4f}", "Ω",  shade=True),
            _row(f"Reatância de dispersão do rotor (a {f_ref:.0f} Hz)",   "X<sub>lr</sub>",  f"{mp.Xlr:.4f}", "Ω",  shade=False),
        ]

    # ── síntese dos dados derivados ───────────────────────────────────────
    ns = mp.n_sync

    # ── monta as linhas ────────────────────────────────────────────────────
    elec_rows = [
        _row("Tensão de linha (RMS)",         "V<sub>l</sub>",  f"{mp.Vl:.1f}",   "V",   shade=False),
        _row("Frequência da rede",            "f",              f"{mp.f:.1f}",    "Hz",  shade=True),
        _row("Resistência do estator",        "R<sub>s</sub>",  f"{mp.Rs:.4f}",   "Ω",   shade=False),
        _row("Resistência do rotor",          "R<sub>r</sub>",  f"{mp.Rr:.4f}",   "Ω",   shade=True),
        *mag_rows,
        _row("Resistência de perdas no ferro","R<sub>fe</sub>", f"{mp.Rfe:.1f}",  "Ω",   shade=True),
    ]
    mec_rows = [
        _row("Número de polos",               "p",              str(mp.p),                   "",      shade=False),
        _row("Momento de inércia",            "J",              f"{mp.J:.4f}",               "kg·m²", shade=True),
        _row("Coeficiente de atrito viscoso", "B",              f"{mp.B:.4f}",               "N·m·s", shade=False),
        _row("Velocidade síncrona",           "n<sub>s</sub>",  f"{ns:.1f}",                 "RPM",   shade=True),
    ]
    exp_rows = _exp_rows(exp_cfg)
    num_rows = [
        _row("Tempo total de simulação",      "t<sub>max</sub>",f"{tmax:.3f}",    "s",   shade=False),
        _row("Passo de integração",           "h",              f"{h:.6f}",       "s",   shade=True),
    ]

    all_rows = (
        [_section("Parâmetros Elétricos")]       + elec_rows +
        [_section("Parâmetros Mecânicos")]       + mec_rows  +
        [_section("Configuração do Experimento")]+ exp_rows  +
        [_section("Parâmetros Numéricos")]       + num_rows
    )

    table_body = "\n".join(all_rows)

    html = f"""
<div style="
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    color: #111111;
    background: #ffffff;
    padding: 28px 32px;
    max-width: 720px;
    margin: 0 auto;
">
  <div style="border-bottom:2px solid #1e293b;padding-bottom:10px;margin-bottom:18px;">
    <div style="font-size:18px;font-weight:700;letter-spacing:0.02em;color:#1e293b;">
      Simulador de Máquina de Indução Trifásica
    </div>
    <div style="font-size:13px;color:#555;margin-top:4px;">
      Parâmetros de configuração
    </div>
  </div>

  <table style="
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      line-height: 1.5;
  ">
    <colgroup>
      <col style="width:46%">
      <col style="width:12%">
      <col style="width:22%">
      <col style="width:10%">
    </colgroup>
    <thead>
      <tr style="background:#f0f0f0;">
        <th style="padding:7px 14px;border:1px solid #d0d0d0;text-align:left;font-weight:600;">
          Parâmetro
        </th>
        <th style="padding:7px 14px;border:1px solid #d0d0d0;text-align:center;font-weight:600;">
          Símbolo
        </th>
        <th style="padding:7px 14px;border:1px solid #d0d0d0;text-align:right;font-weight:600;">
          Valor
        </th>
        <th style="padding:7px 14px;border:1px solid #d0d0d0;font-weight:600;">
          Unidade
        </th>
      </tr>
    </thead>
    <tbody>
      {table_body}
    </tbody>
  </table>
</div>
"""
    st.html(html, unsafe_allow_javascript=False)
