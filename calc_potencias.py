# -*- coding: utf-8 -*-
"""
calc_potencias.py — Calculo de potencias e rendimento apos simulacao
"""

import numpy as np
from EMS_PY import MachineParams, run_simulation, build_fns

mp = MachineParams()
config = {"exp_type": "dol", "Tl_final": 80.0, "t_carga": 1.5}
vfn, tfn, t_ev = build_fns(config, mp)

print("Rodando simulacao...")
res = run_simulation(mp, tmax=3.0, h=1e-4, voltage_fn=vfn, torque_fn=tfn)
print(f"Concluida. N = {len(res['t'])} pontos.\n")

# ── Extrai ultimo ponto ───────────────────────────────────────────────────────
wr  = res["wr"][-1]
n   = res["n"][-1]
Te  = res["Te"][-1]
ids = res["ids"][-1]
iqs = res["iqs"][-1]
idr = res["idr"][-1]
iqr = res["iqr"][-1]
ias = res["ias"][-1]
ibs = res["ibs"][-1]
ics = res["ics"][-1]
iar = res["iar"][-1]
ibr = res["ibr"][-1]
icr = res["icr"][-1]
Va  = res["Va"][-1]
Vb  = res["Vb"][-1]
Vc  = res["Vc"][-1]
Vds = res["Vds"][-1]
Vqs = res["Vqs"][-1]

# ── Regime permanente = ultimos 20% ──────────────────────────────────────────
ss = max(1, len(res["t"]) // 5)

# modulos RMS calculados apenas no regime permanente
Va_rms  = float(np.sqrt(np.mean(res["Va"][-ss:]**2)))
Vb_rms  = float(np.sqrt(np.mean(res["Vb"][-ss:]**2)))
Vc_rms  = float(np.sqrt(np.mean(res["Vc"][-ss:]**2)))
ias_rms = float(np.sqrt(np.mean(res["ias"][-ss:]**2)))
ibs_rms = float(np.sqrt(np.mean(res["ibs"][-ss:]**2)))
ics_rms = float(np.sqrt(np.mean(res["ics"][-ss:]**2)))
Te_med  = float(np.mean(res["Te"][-ss:]))
wr_med  = float(np.mean(res["wr"][-ss:]))
n_med   = float(np.mean(res["n"][-ss:]))

print("=== Modulos em regime permanente ===")
print(f"  Va_rms  = {Va_rms:.4f} V")
print(f"  Vb_rms  = {Vb_rms:.4f} V")
print(f"  Vc_rms  = {Vc_rms:.4f} V")
print(f"  ias_rms = {ias_rms:.4f} A  (corrente fisica)")
print(f"  ibs_rms = {ibs_rms:.4f} A")
print(f"  ics_rms = {ics_rms:.4f} A")
print(f"  Te      = {Te_med:.4f} N.m")
print(f"  wr      = {wr_med:.4f} rad/s")
print(f"  n       = {n_med:.2f} RPM")

# ── Calculos de potencia pelo escorregamento ─────────────────────────────────

# velocidade sincrona mecanica
ws = mp.wb / (mp.p / 2.0)   # rad/s mecanico

# escorregamento
s = (ws - wr_med) / ws

# potencia no entreferro (air gap): P_gap = Te * ws
P_gap = Te_med * ws

# perdas no cobre do rotor: P_cu_r = s * P_gap
P_cu_r = s * P_gap

# potencia mecanica: P_mec = (1 - s) * P_gap
P_mec = (1.0 - s) * P_gap

P_cu_s = 3.0 * mp.Rs * ias_rms**2
P_in   = P_gap + P_cu_s
eta    = (P_mec / P_in * 100.0) if P_in > 0 else 0.0

print()
print("=== Potencias ===")
print(f"  P_gap  = {P_gap:.2f} W")
print(f"  P_cu_r = {P_cu_r:.2f} W")
print(f"  P_cu_s = {P_cu_s:.2f} W")
print(f"  P_in   = {P_in:.2f} W")
print(f"  P_mec  = {P_mec:.2f} W")
print(f"  eta    = {eta:.2f} %")
