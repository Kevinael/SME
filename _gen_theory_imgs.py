# -*- coding: utf-8 -*-
"""Gera os PNG usados na aba Teoria do simulador.
Executa sem dependências do Streamlit — pode ser rodado diretamente.
"""

import os
import schemdraw
import schemdraw.elements as elm
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# CIRCUITOS EQUIVALENTES
# ─────────────────────────────────────────────────────────────────────────────

# ── Circuito Completo ──────────────────────────────────────────────────────
with schemdraw.Drawing() as d:
    d.config(unit=2)
    d.push()
    elm.Line().right(d.unit * 0.25)
    X2 = elm.Inductor().right().label("$j.X'_{2}$")
    I2 = elm.Line().right(d.unit * 0.5)
    elm.Line().down(d.unit * 0.375)
    R2 = elm.ResistorVar().down().label(r"$\dfrac{R'_{2}}{s}$", loc='bottom')
    elm.Line().down(d.unit * 0.375)
    elm.Line().left(d.unit * 0.5)
    elm.Line().left(d.unit * 1.25).dot(open=False)
    elm.Line().left(d.unit * 1.25)
    elm.Line().left()
    V1n = elm.Line().left(d.unit * 0.5).dot(open=True)
    elm.Gap().up(d.unit * 1.75).label(('-', '$V_1$', '+')).dot(open=True)
    V1p = elm.Line().right(d.unit * 0.5)
    R1 = elm.Resistor().right().label('$R_{1}$')
    X1 = elm.Inductor().right().label('j.$X_{1}$')
    elm.Line().right(d.unit * 0.25).dot(open=False)
    d.pop()
    d.push()
    Ifi = elm.Line().down(d.unit * 0.5).dot(open=False)
    elm.Line().right(d.unit * 0.25)
    Xm = elm.Inductor().down().label('$j.X_{m}$', loc='bottom')
    elm.Line().left(d.unit * 0.25).dot(open=False)
    elm.Line().down(d.unit * 0.25)
    d.pop()
    d.push()
    d.move(dx=0, dy=-0.5 * d.unit)
    elm.Line().left(d.unit * 0.25)
    Rc = elm.Resistor().down().label('$R_{c}$')
    elm.Line().right(d.unit * 0.25)
    d.pop()
    elm.CurrentLabel(top=True, length=1, ofst=.3).at(V1p).label('$I_1$')
    elm.CurrentLabel(top=True, length=1, ofst=.3).at(I2).label(r"$I'_{2}$")
    elm.CurrentLabel(top=True, length=0.75, ofst=.3).at(Ifi).label(r"$I_{\phi}$")
    elm.CurrentLabel(top=False, length=0.75, ofst=.75).at(Rc).label('$I_c$')
    elm.CurrentLabel(top=False, length=0.75, ofst=-1.25).at(Xm).label('$I_m$', loc='bottom')
    d.save(os.path.join(OUT, 'ind_completo.png'), dpi=150)
print("ind_completo.png OK")

# ── Circuito IEEE ──────────────────────────────────────────────────────────
with schemdraw.Drawing() as d:
    d.config(unit=2)
    d.push()
    elm.Line().right(d.unit * 0.25)
    X2 = elm.Inductor().right().label("$j.X'_{2}$")
    I2 = elm.Line().right(d.unit * 0.5)
    elm.Line().down(d.unit * 0.375)
    R2 = elm.ResistorVar().down().label(r"$\dfrac{R'_{2}}{s}$", loc='bottom')
    elm.Line().down(d.unit * 0.375)
    elm.Line().left(d.unit * 0.5)
    elm.Line().left(d.unit * 1.25).dot(open=False)
    elm.Line().left(d.unit * 1.25)
    elm.Line().left()
    V1n = elm.Line().left(d.unit * 0.5).dot(open=True)
    elm.Gap().up(d.unit * 1.75).label(('-', '$V_1$', '+')).dot(open=True)
    V1p = elm.Line().right(d.unit * 0.5)
    R1 = elm.Resistor().right().label('$R_{1}$')
    X1 = elm.Inductor().right().label('j.$X_{1}$')
    elm.Line().right(d.unit * 0.25).dot(open=False)
    d.pop()
    d.push()
    Ifi = elm.Line().down(d.unit * 0.375)
    Xm = elm.Inductor().down().label('$j.X_{m}$', loc='bottom')
    elm.Line().down(d.unit * 0.375)
    d.pop()
    elm.CurrentLabel(top=True, length=1, ofst=.3).at(V1p).label('$I_1$')
    elm.CurrentLabel(top=True, length=1, ofst=.3).at(I2).label(r"$I'_{2}$")
    elm.CurrentLabel(top=False, length=0.75, ofst=-1.25).at(Xm).label('$I_m$', loc='bottom')
    d.save(os.path.join(OUT, 'ind_ieee.png'), dpi=150)
print("ind_ieee.png OK")

# ── Circuito Thevenin ──────────────────────────────────────────────────────
with schemdraw.Drawing() as d:
    d.config(unit=2)
    d.push()
    elm.Line().right(d.unit * 0.25)
    X2 = elm.Inductor().right().label("$j.X'_{2}$")
    I2 = elm.Line().right(d.unit * 0.5)
    elm.Line().down(d.unit * 0.375)
    R2 = elm.ResistorVar().down().label(r"$\dfrac{R'_{2}}{s}$", loc='bottom')
    elm.Line().down(d.unit * 0.375)
    elm.Line().left(d.unit * 0.5)
    elm.Line().left(d.unit * 1.25)
    elm.Line().left(d.unit * 1.25)
    elm.Line().left()
    V1n = elm.Line().left(d.unit * 0.5).dot(open=True)
    elm.Gap().up(d.unit * 1.75).label(('-', '$V_{th}$', '+')).dot(open=True)
    V1p = elm.Line().right(d.unit * 0.5)
    R1 = elm.Resistor().right().label('$R_{th}$')
    X1 = elm.Inductor().right().label('j.$X_{th}$')
    elm.Line().right(d.unit * 0.25)
    d.pop()
    elm.CurrentLabel(top=True, length=1, ofst=.3).at(V1p).label('$I_1$')
    d.save(os.path.join(OUT, 'ind_thevenin.png'), dpi=150)
print("ind_thevenin.png OK")

# ── Circuito IEEE duplo ────────────────────────────────────────────────────
with schemdraw.Drawing() as d:
    d.config(unit=2)
    d.push()
    I2 = elm.Line().right(d.unit * 0.5)
    X2 = elm.Inductor().right().label("$j.X'_{2}$")
    elm.Line().right(d.unit * 0.25).dot()
    elm.Line().down(d.unit * 0.375)
    R2 = elm.ResistorVar().down().label(r"$\dfrac{R'_{2}}{s}$", loc='bottom')
    elm.Line().down(d.unit * 0.375)
    elm.Line().left(d.unit * 0.5)
    elm.Line().left(d.unit * 1.25).dot(open=False)
    elm.Line().left(d.unit * 1.25)
    elm.Line().left()
    V1n = elm.Line().left(d.unit * 0.5).dot(open=True)
    elm.Gap().up(d.unit * 1.75).label(('-', '$V_1$', '+')).dot(open=True)
    V1p = elm.Line().right(d.unit * 0.5)
    R1 = elm.Resistor().right().label('$R_{1}$')
    X1 = elm.Inductor().right().label('j.$X_{1}$')
    elm.Line().right(d.unit * 0.25).dot(open=False)
    d.pop()
    d.push()
    d.move(dx=1.75 * d.unit, dy=0)
    I22 = elm.Line().right(d.unit * 0.5)
    X22 = elm.Inductor().right().label("$j.X''_{2}$")
    elm.Line().right(d.unit * 0.25)
    elm.Line().down(d.unit * 0.375)
    R22 = elm.ResistorVar().down().label(r"$\dfrac{R''_{2}}{s}$", loc='bottom')
    elm.Line().down(d.unit * 0.375)
    elm.Line().left(d.unit * 0.75)
    elm.Line().left(d.unit * 1.0).dot(open=False)
    d.pop()
    d.push()
    Ifi = elm.Line().down(d.unit * 0.375)
    Xm = elm.Inductor().down().label('$j.X_{m}$', loc='bottom')
    elm.Line().down(d.unit * 0.375)
    d.pop()
    elm.CurrentLabel(top=True, length=1, ofst=.3).at(V1p).label('$I_1$')
    elm.CurrentLabel(top=True, length=1, ofst=.3).at(I2).label(r"$I'_{2}$")
    elm.CurrentLabel(top=True, length=1, ofst=.3).at(I22).label(r"$I''_{2}$")
    elm.CurrentLabel(top=False, length=0.75, ofst=-1.25).at(Xm).label('$I_m$', loc='bottom')
    d.save(os.path.join(OUT, 'ind_ieee_duplo.png'), dpi=150)
print("ind_ieee_duplo.png OK")

# ─────────────────────────────────────────────────────────────────────────────
# FLUXO DE POTÊNCIA
# ─────────────────────────────────────────────────────────────────────────────

# ── Motor ──────────────────────────────────────────────────────────────────
with schemdraw.Drawing() as d:
    d.config(unit=2)
    d.push()
    elm.Arrow().right(d.unit * 4.0)
    elm.Label().label('$P_{out}$', ofst=(.4, -.125))
    d.pop()
    d.push()
    d.move(dx=0, dy=-0.125 * d.unit)
    elm.Line().right(d.unit * 3.25)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{rot}$', ofst=(.125, -.125))
    d.pop()
    d.push()
    d.move(dx=2.5 * d.unit, dy=0.5 * d.unit)
    elm.Line().down(d.unit * 1.5).linestyle(':').color('lightgrey')
    elm.Label().label('$P_{mec}$', ofst=(-3.0, .5))
    elm.Label().label('$P_{ele}$', ofst=(-3.0, -.6))
    d.pop()
    d.push()
    d.move(dx=0, dy=-0.25 * d.unit)
    elm.Line().right(d.unit * 2.0)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{cu,2}$', ofst=(.125, -.125))
    d.pop()
    d.push()
    d.move(dx=1.25 * d.unit, dy=0.25 * d.unit)
    elm.Line().down(d.unit * 1.0).linestyle(':').color('lightgrey')
    elm.Label().label('$P_{ag}$', ofst=(0.25, .0))
    d.pop()
    d.push()
    d.move(dx=0, dy=-0.375 * d.unit)
    elm.Line().right(d.unit * 0.5)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{cu,1}$', ofst=(.125, -.125))
    d.pop()
    d.push()
    d.move(dx=-0.4 * d.unit, dy=-0.125 * d.unit)
    elm.Label().label('$P_{in}$', ofst=(.125, -.125))
    d.pop()
    d.save(os.path.join(OUT, 'fluxo_P_motor.png'), dpi=150)
print("fluxo_P_motor.png OK")

# ── Gerador ────────────────────────────────────────────────────────────────
with schemdraw.Drawing() as d:
    d.config(unit=2)
    d.push()
    elm.Arrow().right(d.unit * 4.0).reverse()
    elm.Label().label('$P_{in}$', ofst=(.4, -.4))
    d.pop()
    d.push()
    d.move(dx=4.0 * d.unit, dy=-0.125 * d.unit)
    elm.Line().left(d.unit * 3.25)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{cu,1}$', ofst=(.125, -.125))
    d.pop()
    d.push()
    d.move(dx=2.5 * d.unit, dy=0.5 * d.unit)
    elm.Line().down(d.unit * 1.5).linestyle(':').color('lightgrey')
    elm.Label().label('$P_{mec}$', ofst=(-3.0, .5))
    elm.Label().label('$P_{ele}$', ofst=(-3.0, -.6))
    d.pop()
    d.push()
    d.move(dx=4.0 * d.unit, dy=-0.25 * d.unit)
    elm.Line().left(d.unit * 2.0)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{cu,2}$', ofst=(.125, -.125))
    d.pop()
    d.push()
    d.move(dx=1.25 * d.unit, dy=0.25 * d.unit)
    elm.Line().down(d.unit * 1.0).linestyle(':').color('lightgrey')
    elm.Label().label('$P_{ag}$', ofst=(0.25, .0))
    d.pop()
    d.push()
    d.move(dx=4.0 * d.unit, dy=-0.375 * d.unit)
    elm.Line().left(d.unit * 0.5)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{rot}$', ofst=(.125, -.125))
    d.pop()
    d.push()
    d.move(dx=-0.4 * d.unit, dy=0)
    elm.Label().label('$P_{out}$', ofst=(.125, -.125))
    d.pop()
    d.save(os.path.join(OUT, 'fluxo_P_gerador.png'), dpi=150)
print("fluxo_P_gerador.png OK")

# ── Frenagem ───────────────────────────────────────────────────────────────
with schemdraw.Drawing() as d:
    d.config(unit=2)
    d.push()
    elm.Arrow().right(d.unit * 1.0)
    elm.Line().right(d.unit * 1.0).dot()
    elm.Line().right(d.unit * 1.0)
    elm.Arrow().right(d.unit * 1.0).reverse()
    elm.Label().label('$P_{eixo}$', ofst=(.5, -.125))
    d.pop()
    d.push()
    d.move(dx=0, dy=-0.125 * d.unit)
    elm.Line().right(d.unit * .5)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{cu,1}$', ofst=(.125, -.25))
    d.pop()
    d.push()
    d.move(dx=2.5 * d.unit, dy=0.5 * d.unit)
    elm.Line().down(d.unit * 1.5).linestyle(':').color('lightgrey')
    elm.Label().label('$P_{mec}$', ofst=(-3.0, .5))
    elm.Label().label('$P_{ele}$', ofst=(-3.0, -.6))
    d.pop()
    d.push()
    d.move(dx=2.0 * d.unit, dy=0)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{cu,2}$', ofst=(.125, -.125))
    d.pop()
    d.push()
    d.move(dx=1.25 * d.unit, dy=0.25 * d.unit)
    elm.Line().down(d.unit * 1.0).linestyle(':').color('lightgrey')
    elm.Label().label('$P_{ag}$', ofst=(0.25, .0))
    d.pop()
    d.push()
    d.move(dx=4.0 * d.unit, dy=-0.125 * d.unit)
    elm.Line().left(d.unit * 0.5)
    elm.Arrow().down(d.unit * 0.5)
    elm.Label().label('$P_{rot}$', ofst=(.125, -.125))
    d.pop()
    d.push()
    d.move(dx=-0.4 * d.unit, dy=0)
    elm.Label().label('$P_{terminal}$', ofst=(-.25, -.125))
    d.pop()
    d.save(os.path.join(OUT, 'fluxo_P_frenagem.png'), dpi=150)
print("fluxo_P_frenagem.png OK")

# ─────────────────────────────────────────────────────────────────────────────
# CURVAS TORQUE × ESCORREGAMENTO
# ─────────────────────────────────────────────────────────────────────────────

V1 = 220; f = 60; p = 4
R1 = 0.5; X1 = 1.0; R2 = 0.4; X2 = 1.0; Xm = 50
ns = 120 * f / p


def _torque(s, V1, R1, X1, R2, X2, Xm, ns):
    if abs(s) < 1e-4:
        s = 1e-4
    Z2  = R2 / s + 1j * X2
    Zeq = (1j * Xm * Z2) / (1j * Xm + Z2)
    Zt  = R1 + 1j * X1 + Zeq
    I1  = V1 / Zt
    Veq = I1 * Zeq
    I2  = Veq / Z2
    P2  = 3 * abs(I2) ** 2 * (R2 / s)
    return P2 / (2 * np.pi * ns / 60)


# ── Curva completa T×s (preto e branco) ──────────────────────────────────
s_all  = np.linspace(-2, 2, 2000)
s_all  = s_all[s_all != 0]
T_all  = [_torque(s, V1, R1, X1, R2, X2, Xm, ns) for s in s_all]
n_all  = ns * (1 - s_all)

fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(n_all, T_all, 'k-', linewidth=2.5)
ax1.axhline(0, color='k', linewidth=0.8)
ax1.axvline(ns, color='k', linestyle='--', linewidth=1, alpha=0.5)
ax1.axvline(0,  color='k', linestyle='--', linewidth=1, alpha=0.5)
ax1.text(-ns / 2,  min(T_all) * 0.6, 'REGIÃO 1', fontsize=12, fontweight='bold',
         ha='center', alpha=0.35, rotation=90)
ax1.text(ns / 2,   min(T_all) * 0.6, 'REGIÃO 2', fontsize=12, fontweight='bold',
         ha='center', alpha=0.35, rotation=90)
ax1.text(ns * 2,   max(T_all) * 0.4, 'REGIÃO 3', fontsize=12, fontweight='bold',
         ha='center', alpha=0.35, rotation=90)
ax1.set_xlabel('Velocidade (rpm)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Torque (N·m)',     fontsize=12, fontweight='bold')
ax1.set_title('Curva Característica — Máquina de Indução\nTorque × Velocidade / Escorregamento',
              fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.set_xlim(-ns, ns * 3)

ax2 = ax1.twiny()
ax2.set_xlim(ax1.get_xlim())
s_ticks = np.array([2, 1.5, 1, 0.5, 0, -0.5, -1])
ax2.set_xticks(ns * (1 - s_ticks))
ax2.set_xticklabels([f'{s:.1f}' for s in s_ticks])
ax2.set_xlabel('Escorregamento (s)', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUT, 'T_x_s.png'), dpi=150)
plt.close()
print("T_x_s.png OK")

# ── Efeito de R2 ──────────────────────────────────────────────────────────
R2_vals  = [0.2, 0.4, 0.6, 0.8, 1.0, 1.5]
estilos  = ['-', '--', '-.', ':', (0, (3, 1, 1, 1)), (0, (5, 1))]
marcad   = ['o', 's', 'D', '^', 'v', '>']
s_motor  = np.linspace(0.001, 1, 500)

fig, ax1 = plt.subplots(figsize=(10, 6))
Tmaxs, Ncriticos = [], []

for i, r2 in enumerate(R2_vals):
    Tv = [_torque(s, V1, R1, X1, r2, X2, Xm, ns) for s in s_motor]
    nv = ns * (1 - s_motor)
    idx = int(np.argmax(Tv))
    Tmaxs.append(Tv[idx]); Ncriticos.append(nv[idx])
    ax1.plot(nv, Tv, color='black', linewidth=1.5,
             linestyle=estilos[i], label=f"$R'_2$ = {r2} Ω")
    ax1.scatter(nv[idx], Tv[idx], color=str(0.15 * i), s=100,
                marker=marcad[i], zorder=5, edgecolors='black', linewidths=1.5)

ax1.axhline(0,  color='k', linewidth=1.0)
ax1.axvline(ns, color='k', linestyle='--', linewidth=1.5, alpha=0.8, label='$n_s$')
ax1.set_xlabel('Velocidade (rpm)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Torque (N·m)',     fontsize=12, fontweight='bold')
ax1.set_title("Curvas T×n — Variação de $R'_2$\n(Região de operação como motor)",
              fontsize=13, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle=':')
ax1.legend(fontsize=9, framealpha=1, edgecolor='black')
ax1.set_xlim(0, ns * 1.02)
ax1.set_ylim(0, max(Tmaxs) * 1.1)

ax2 = ax1.twiny()
ax2.set_xlim(ax1.get_xlim())
s_t = np.array([1.0, 0.8, 0.6, 0.4, 0.2, 0.0])
ax2.set_xticks(ns * (1 - s_t))
ax2.set_xticklabels([f'{s:.1f}' for s in s_t])
ax2.set_xlabel('Escorregamento (s)', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUT, 'TR2.png'), dpi=150)
plt.close()
print("TR2.png OK")

# ── Gaiola dupla ─────────────────────────────────────────────────────────
R2o, X2o = 4.0, 1.5   # externa
R2i, X2i = 0.5, 4.5   # interna

def _torque_dupla(s, V1, R1, X1, R2o, X2o, R2i, X2i, Xm, ns):
    if abs(s) < 1e-4: s = 1e-4
    Zo  = R2o / s + 1j * X2o
    Zi  = R2i / s + 1j * X2i
    Zeq_r = (Zo * Zi) / (Zo + Zi)
    Zeq = (1j * Xm * Zeq_r) / (1j * Xm + Zeq_r)
    I1  = V1 / (R1 + 1j * X1 + Zeq)
    Veq = I1 * Zeq
    ws  = 2 * np.pi * ns / 60
    return (3 * abs(Veq / Zo) ** 2 * (R2o / s) / ws,
            3 * abs(Veq / Zi) ** 2 * (R2i / s) / ws)

Tt, To, Ti = [], [], []
for s in s_motor:
    o, i = _torque_dupla(s, V1, R1, X1, R2o, X2o, R2i, X2i, Xm, ns)
    To.append(o); Ti.append(i); Tt.append(o + i)

nv = ns * (1 - s_motor)
fig, ax1 = plt.subplots(figsize=(7, 5))
ax1.plot(nv, Tt, 'k-',  linewidth=3,   label='Torque Total (Gaiola Dupla)')
ax1.plot(nv, To, 'k--', linewidth=2,   label='Gaiola Externa')
ax1.plot(nv, Ti, 'k:',  linewidth=2,   label='Gaiola Interna')
ax1.axhline(0,  color='k', linewidth=1)
ax1.axvline(ns, color='k', linestyle='--', linewidth=1.5, alpha=0.8)
ax1.set_xlabel('Velocidade (rpm)', fontsize=13, fontweight='bold')
ax1.set_ylabel('Torque (N·m)',     fontsize=13, fontweight='bold')
ax1.set_title('Motor com Gaiola de Esquilo Dupla\nComposição do Torque por Gaiola',
              fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3, linestyle=':')
ax1.legend(fontsize=11, framealpha=1, edgecolor='black')
ax1.set_xlim(0, ns * 1.02)
ax1.set_ylim(0, max(Tt) * 1.15)

ax2 = ax1.twiny()
ax2.set_xlim(ax1.get_xlim())
ax2.set_xticks(ns * (1 - s_t))
ax2.set_xticklabels([f'{s:.1f}' for s in s_t])
ax2.set_xlabel('Escorregamento (s)', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUT, 'SCdupla.png'), dpi=150)
plt.close()
print("SCdupla.png OK")

print("\nTodos os PNGs gerados com sucesso.")
