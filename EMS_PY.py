# -*- coding: utf-8 -*-
"""
EMS_PY.py — Núcleo físico do Simulador de Máquinas Elétricas
Modelo 0dq de Krause — Integração RK4 (scipy.odeint)

Exporta:
  MachineParams       — dataclass com todos os parâmetros da máquina
  run_simulation      — integra o ODE e retorna dict com séries temporais
  build_fns           — monta funções de tensão e torque para cada experimento
"""

from __future__ import annotations
import numpy as np
from scipy.integrate import odeint
from dataclasses import dataclass, field
from desequilibrio_falta import abc_voltages_deseq


# ═══════════════════════════════════════════════════════════════════════════
# BLOCO A — MODELO MATEMATICO
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MachineParams:
    Vl:    float = 220.0
    f:     float = 60.0
    Rs:    float = 0.435
    Rr:    float = 0.816
    Xm:    float = 26.13
    Xls:   float = 0.754
    Xlr:   float = 0.754
    Rfe:   float = 500.0   # resistência de perdas no ferro (Ω) — NOTA: parâmetro não utilizado no ODE (usado apenas no cálculo de potências)
    p:     int   = 4
    J:     float = 0.089
    B:     float = 0.005  # atrito + ventilação ≈ 1% de P_nom para motor ~15 kW
    # --- modo de entrada dos parâmetros magnéticos ---
    # input_mode = "X"  : Xm/Xls/Xlr são reatâncias (Ω) medidas em f_ref Hz
    # input_mode = "L"  : Xm/Xls/Xlr são na verdade indutâncias (H) — f_ref é ignorado
    input_mode: str   = "X"   # "X" ou "L"
    f_ref:      float = 60.0  # frequência em que as reatâncias foram ensaiadas (Hz)
    Xml:   float = field(init=False)
    wb:    float = field(init=False)
    Lm:    float = field(init=False)
    Lls:   float = field(init=False)
    Llr:   float = field(init=False)
    Xls_a: float = field(init=False)
    Xlr_a: float = field(init=False)

    def __post_init__(self) -> None:
        self.wb = 2.0 * np.pi * self.f
        if self.input_mode == "L":
            # Xm, Xls, Xlr já são indutâncias (H) — sem conversão necessária
            self.Lm  = self.Xm
            self.Lls = self.Xls
            self.Llr = self.Xlr
        else:
            # Xm, Xls, Xlr são reatâncias (Ω) medidas em f_ref Hz.
            # Convertemos para indutâncias usando a frequência de ensaio informada.
            _wb_ref  = 2.0 * np.pi * self.f_ref
            self.Lm  = self.Xm  / _wb_ref
            self.Lls = self.Xls / _wb_ref
            self.Llr = self.Xlr / _wb_ref
        # Reatâncias reais na frequência de operação configurada
        self.Xls_a = self.wb * self.Lls
        self.Xlr_a = self.wb * self.Llr
        _Xm_a      = self.wb * self.Lm
        self.Xml   = 1.0 / (1.0/_Xm_a + 1.0/self.Xls_a + 1.0/self.Xlr_a)

    @property
    def n_sync(self) -> float:
        return 120.0 * self.f / self.p


def induction_motor_ode(states, t, Vqs, Vds, Tl, w_ref, mp):
    PSIqs, PSIds, PSIqr, PSIdr, wr = states

    # fluxo de magnetização (reatâncias escalonadas para a frequência atual)
    PSImq = mp.Xml * (PSIqs / mp.Xls_a + PSIqr / mp.Xlr_a)
    PSImd = mp.Xml * (PSIds / mp.Xls_a + PSIdr / mp.Xlr_a)

    # correntes do estator (eixos dq)
    iqs = (1.0 / mp.Xls_a) * (PSIqs - PSImq)
    ids = (1.0 / mp.Xls_a) * (PSIds - PSImd)

    # derivadas de fluxo do estator (modelo Krause padrão)
    dPSIqs = mp.wb * (Vqs - (w_ref/mp.wb)*PSIds + (mp.Rs/mp.Xls_a)*(PSImq - PSIqs))
    dPSIds = mp.wb * (Vds + (w_ref/mp.wb)*PSIqs + (mp.Rs/mp.Xls_a)*(PSImd - PSIds))

    slip_ref = (w_ref - wr) / mp.wb

    # derivadas de fluxo do rotor
    dPSIqr = mp.wb * (-slip_ref*PSIdr + (mp.Rr/mp.Xlr_a)*(PSImq - PSIqr))
    dPSIdr = mp.wb * ( slip_ref*PSIqr + (mp.Rr/mp.Xlr_a)*(PSImd - PSIdr))

    Te  = (3.0/2.0)*(mp.p/2.0)*(1.0/mp.wb)*(PSIds*iqs - PSIqs*ids)
    dwr = (mp.p/(2.0*mp.J))*(Te - Tl) - (mp.B/mp.J)*wr
    return [dPSIqs, dPSIds, dPSIqr, dPSIdr, dwr]


def abc_voltages(t, Vl, f):
    """Gera tensões abc balanceadas — convenção dos arquivos de referência (pasta Base)."""
    tetae = 2.0*np.pi*f*t
    Va = np.sqrt(2.0/3.0)*Vl*np.sin(tetae)
    Vb = np.sqrt(2.0/3.0)*Vl*np.sin(tetae - 2.0*np.pi/3.0)
    Vc = np.sqrt(2.0/3.0)*Vl*np.sin(tetae + 2.0*np.pi/3.0)
    return Va, Vb, Vc


def clarke_park_transform(Va, Vb, Vc, tetae):
    """Transformada de Clarke (potência invariante) + Park — igual aos arquivos Base."""
    # Clarke potência-invariante: αβ
    k = np.sqrt(3.0/2.0)
    Vaf = k*(Va - 0.5*Vb - 0.5*Vc)
    Vbt = k*(np.sqrt(3.0)/2.0*Vb - np.sqrt(3.0)/2.0*Vc)
    # Park: αβ → dq síncrono
    Vds =  np.cos(tetae)*Vaf + np.sin(tetae)*Vbt
    Vqs = -np.sin(tetae)*Vaf + np.cos(tetae)*Vbt
    return Vds, Vqs


def reconstruct_abc_currents(PSIqs, PSIds, PSIqr, PSIdr, tetae, tetar, mp):
    PSImq = mp.Xml*(PSIqs/mp.Xls_a + PSIqr/mp.Xlr_a)
    PSImd = mp.Xml*(PSIds/mp.Xls_a + PSIdr/mp.Xlr_a)
    ids = (1.0/mp.Xls_a)*(PSIds - PSImd)
    iqs = (1.0/mp.Xls_a)*(PSIqs - PSImq)
    idr = (1.0/mp.Xlr_a)*(PSIdr - PSImd)
    iqr = (1.0/mp.Xlr_a)*(PSIqr - PSImq)
    # Inversa de Park: dq → αβ
    iafs = ids*np.cos(tetae) - iqs*np.sin(tetae)
    ibts = ids*np.sin(tetae) + iqs*np.cos(tetae)
    iafr = idr*np.cos(tetar) - iqr*np.sin(tetar)
    ibtr = idr*np.sin(tetar) + iqr*np.cos(tetar)
    # Inversa de Clarke potência-invariante: αβ → abc
    k = np.sqrt(3.0/2.0)
    ias = k*iafs
    ibs = k*(-0.5*iafs + (np.sqrt(3.0)/2.0)*ibts)
    ics = k*(-0.5*iafs - (np.sqrt(3.0)/2.0)*ibts)
    iar = k*iafr
    ibr = k*(-0.5*iafr + (np.sqrt(3.0)/2.0)*ibtr)
    icr = k*(-0.5*iafr - (np.sqrt(3.0)/2.0)*ibtr)
    return ids, iqs, idr, iqr, ias, ibs, ics, iar, ibr, icr


def voltage_reduced_start(t, Vl_nominal, Vl_reduced, t_switch):
    return Vl_nominal if t >= t_switch else Vl_reduced


def voltage_soft_starter(t, Vl_nominal, Vl_initial, t_start_ramp, t_full):
    if t < t_start_ramp:
        return Vl_initial
    elif t < t_full:
        return Vl_initial + (Vl_nominal - Vl_initial)*(t - t_start_ramp)/(t_full - t_start_ramp)
    return Vl_nominal


def torque_step(t, Tl_before, Tl_after, t_switch):
    return Tl_after if t >= t_switch else Tl_before


def torque_pulse(t, Tl, t_on, t_off):
    """Aplica Tl entre t_on e t_off; zero fora desse intervalo."""
    return Tl if t_on <= t < t_off else 0.0


def run_simulation(mp, tmax, h, voltage_fn, torque_fn, ref_code=1,
                   deseq_a=0.0, deseq_b=0.0, deseq_c=0.0,
                   falta_fase_a=False, falta_fase_b=False, falta_fase_c=False,
                   t_deseq=0.0, clamp_wr_at_zero=False):
    t_values = np.arange(0.0, tmax, h)
    N = len(t_values)
    keys = ["wr","n","Te","ids","iqs","idr","iqr",
            "ias","ibs","ics","iar","ibr","icr","Va","Vb","Vc","Vds","Vqs"]
    arr = {k: np.empty(N) for k in keys}
    states, last_wr, we, tetar = [0.0]*5, 0.0, mp.wb, 0.0
    for i, tv in enumerate(t_values):
        Vl_a   = voltage_fn(tv)
        Tl_a   = torque_fn(tv)
        tetae  = we * tv
        w_ref  = we if ref_code == 1 else (last_wr if ref_code == 2 else 0.0)
        _use_deseq = (deseq_a != 0.0 or deseq_b != 0.0 or deseq_c != 0.0
                      or falta_fase_a or falta_fase_b or falta_fase_c) and tv >= t_deseq
        if _use_deseq:
            Va, Vb, Vc = abc_voltages_deseq(
                tv, Vl_a, mp.f,
                deseq_a, deseq_b, deseq_c,
                falta_fase_a, falta_fase_b, falta_fase_c,
            )
        else:
            Va, Vb, Vc = abc_voltages(tv, Vl_a, mp.f)
        Vds, Vqs   = clarke_park_transform(Va, Vb, Vc, tetae)
        wr_before  = last_wr
        sol    = odeint(induction_motor_ode, states, [tv, tv+h],
                        args=(Vqs, Vds, Tl_a, w_ref, mp))
        states = list(sol[1])
        PSIqs, PSIds, PSIqr, PSIdr, wr = states
        if clamp_wr_at_zero and wr < 0.0:
            wr = 0.0; states[4] = 0.0
        tetar   += 0.5 * (wr_before + wr) * h   # integração trapezoidal do ângulo elétrico do rotor
        last_wr  = wr
        ids, iqs, idr, iqr, ias, ibs, ics, iar, ibr, icr = reconstruct_abc_currents(
            PSIqs, PSIds, PSIqr, PSIdr, tetae, tetar, mp)
        Te = (3.0/2.0)*(mp.p/2.0)*(1.0/mp.wb)*(PSIds*iqs - PSIqs*ids)

        arr["wr"][i]=wr/(mp.p/2.0);  arr["n"][i]=wr*60.0/(np.pi*mp.p)
        arr["Te"][i]=Te;  arr["ids"][i]=ids; arr["iqs"][i]=iqs
        arr["idr"][i]=idr; arr["iqr"][i]=iqr
        arr["ias"][i]=ias; arr["ibs"][i]=ibs; arr["ics"][i]=ics
        arr["iar"][i]=iar; arr["ibr"][i]=ibr; arr["icr"][i]=icr
        arr["Va"][i]=Va;  arr["Vb"][i]=Vb;  arr["Vc"][i]=Vc
        arr["Vds"][i]=Vds; arr["Vqs"][i]=Vqs
    arr["t"] = t_values

    # ── Deteccao automatica do inicio do regime permanente ───────────────────
    # Varre wr de tras pra frente: regime comeca onde a variacao relativa
    # supera o limiar (i.e., ainda ha transitorio). A janela e arredondada
    # para conter um numero inteiro de ciclos da fundamental.
    samples_per_cycle = max(1, int(round(1.0 / (mp.f * h))))
    min_ss = 5 * samples_per_cycle          # minimo: 5 ciclos completos

    wr_arr  = arr["wr"]
    wr_ref  = float(np.mean(wr_arr[-min_ss:]))   # referencia: media dos ultimos 5 ciclos
    tol     = 0.005                               # tolerancia: 0.5% de variacao relativa

    ss_start = 0   # indice de inicio do regime (padrao: inicio do sinal)
    for i in range(N - min_ss - 1, -1, -1):
        if wr_ref == 0 or abs((wr_arr[i] - wr_ref) / wr_ref) > tol:
            ss_start = i + 1
            break

    # primeiro passe: estima s com janela simples para calcular f_rotor
    ss_len_tmp = max(N - ss_start, min_ss)
    wr_med_tmp = float(np.mean(arr["wr"][max(0, N - ss_len_tmp):]))
    ws         = mp.wb / (mp.p / 2.0)
    s_tmp      = (ws - wr_med_tmp) / ws

    # ciclo do rotor: f_r = |s| * f  (pode ser muito menor que f)
    f_rotor = max(abs(s_tmp) * mp.f, 0.01)   # evita divisao por zero
    samples_per_rotor_cycle = max(1, int(round(1.0 / (f_rotor * h))))

    # arredondar para MMC dos dois ciclos — garante inteiro de ciclos para estator E rotor
    from math import gcd
    lcm_samples = (samples_per_cycle * samples_per_rotor_cycle
                   // gcd(samples_per_cycle, samples_per_rotor_cycle))
    lcm_samples = min(lcm_samples, N // 2)   # nao usar mais que metade do sinal

    ss_len = N - ss_start
    ss_len = max(ss_len, min_ss)
    ss_len = max(ss_len // lcm_samples, 1) * lcm_samples
    ss_start = max(0, N - ss_len)

    Te_med = float(np.mean(arr["Te"][ss_start:]))
    wr_med = float(np.mean(arr["wr"][ss_start:]))
    n_med  = float(np.mean(arr["n"][ss_start:]))

    s      = (ws - wr_med) / ws
    P_gap  = Te_med * ws
    P_cu_r = s * P_gap
    P_mec  = (1.0 - s) * P_gap

    # RMS de todas as variaveis AC — janela de regime (inteiro de ciclos)
    def _rms(key): return float(np.sqrt(np.mean(arr[key][ss_start:]**2)))
    def _mean(key): return float(np.mean(arr[key][ss_start:]))

    ias_rms = _rms("ias");  ibs_rms = _rms("ibs");  ics_rms = _rms("ics")
    iar_rms = _rms("iar");  ibr_rms = _rms("ibr");  icr_rms = _rms("icr")
    ids_rms = _rms("ids");  iqs_rms = _rms("iqs")
    idr_rms = _rms("idr");  iqr_rms = _rms("iqr")
    Va_rms  = _rms("Va");   Vb_rms  = _rms("Vb");   Vc_rms  = _rms("Vc")
    Vds_rms = _rms("Vds");  Vqs_rms = _rms("Vqs")

    P_cu_s = 3.0 * mp.Rs * ias_rms**2

    if s >= 0:
        # modo motor: P_in elétrica → P_mec mecânica
        P_in  = P_gap + P_cu_s
        P_out = P_mec
        eta   = (P_out / P_in * 100.0) if P_in > 0 else 0.0
    else:
        # modo gerador: P_in mecânica (turbina) → P_out elétrica
        P_in  = abs(P_mec)                 # potência mecânica da turbina
        P_out = abs(P_gap) - P_cu_s        # potência elétrica entregue à rede
        eta   = (P_out / P_in * 100.0) if P_in > 0 else 0.0

    arr["P_gap"]   = P_gap
    arr["P_cu_r"]  = P_cu_r
    arr["P_mec"]   = P_mec
    arr["P_cu_s"]  = P_cu_s
    arr["P_in"]    = P_in
    arr["P_out"]   = P_out
    arr["eta"]     = eta
    arr["s"]       = s
    arr["n_ss"]    = n_med
    arr["wr_ss"]   = wr_med
    arr["Te_ss"]   = Te_med
    arr["ias_rms"]  = ias_rms;  arr["ibs_rms"]  = ibs_rms;  arr["ics_rms"]  = ics_rms
    arr["iar_rms"]  = iar_rms;  arr["ibr_rms"]  = ibr_rms;  arr["icr_rms"]  = icr_rms
    arr["ids_rms"]  = ids_rms;  arr["iqs_rms"]  = iqs_rms
    arr["idr_rms"]  = idr_rms;  arr["iqr_rms"]  = iqr_rms
    arr["Va_rms"]   = Va_rms;   arr["Vb_rms"]   = Vb_rms;   arr["Vc_rms"]   = Vc_rms
    arr["Vds_rms"]  = Vds_rms;  arr["Vqs_rms"]  = Vqs_rms
    arr["_ss_start"] = ss_start

    # ── Variáveis retornadas (todas np.ndarray shape (N,)) ──────────────────
    # t      — vetor de tempo (s)
    # wr     — velocidade angular do rotor (rad/s)
    # n      — rotação do rotor (RPM)
    # Te     — torque eletromagnético (N·m)
    # ids    — corrente do estator eixo d (A)
    # iqs    — corrente do estator eixo q (A)
    # idr    — corrente do rotor eixo d (A)
    # iqr    — corrente do rotor eixo q (A)
    # ias    — corrente do estator fase a (A)
    # ibs    — corrente do estator fase b (A)
    # ics    — corrente do estator fase c (A)
    # iar    — corrente do rotor fase a (A)
    # ibr    — corrente do rotor fase b (A)
    # icr    — corrente do rotor fase c (A)
    # Va     — tensão de fase a (V)
    # Vb     — tensão de fase b (V)
    # Vc     — tensão de fase c (V)
    # Vds    — tensão do estator eixo d (V)
    # Vqs    — tensão do estator eixo q (V)
    return arr


def build_fns(config: dict, mp: MachineParams):
    """Constrói as funções de tensão e torque para o experimento selecionado."""
    exp = config["exp_type"]
    t_ev = []
    if exp == "dol":
        Tl, tc = config["Tl_final"], config["t_carga"]
        vfn = lambda t: mp.Vl
        tfn = lambda t: torque_step(t, 0.0, Tl, tc)
        t_ev = [tc]
    elif exp == "yd":
        Vy = mp.Vl/np.sqrt(3.0); Tl=config["Tl_final"]; t2=config["t_2"]; tc=config["t_carga"]
        vfn = lambda t: voltage_reduced_start(t, mp.Vl, Vy, t2)
        tfn = lambda t: torque_step(t, 0.0, Tl, tc)
        t_ev = [t2, tc]
    elif exp == "comp":
        Vr=mp.Vl*config["voltage_ratio"]; Tl=config["Tl_final"]; t2=config["t_2"]; tc=config["t_carga"]
        vfn = lambda t: voltage_reduced_start(t, mp.Vl, Vr, t2)
        tfn = lambda t: torque_step(t, 0.0, Tl, tc)
        t_ev = [t2, tc]
    elif exp == "soft":
        Vi=mp.Vl*config["voltage_ratio"]; t2=config["t_2"]; tp=config["t_pico"]
        Tl=config["Tl_final"]; tc=config["t_carga"]
        vfn = lambda t: voltage_soft_starter(t, mp.Vl, Vi, t2, tp)
        tfn = lambda t: torque_step(t, 0.0, Tl, tc)
        t_ev = [t2, tp, tc]
    elif exp == "carga":
        Tl=config["Tl_final"]; tc=config["t_carga"]
        vfn = lambda t: mp.Vl
        tfn = lambda t: torque_step(t, 0.0, Tl, tc)
        t_ev = [tc]
    elif exp == "pulso_carga":
        Tl=config["Tl_final"]; ton=config["t_carga"]; toff=config["t_retirada"]
        vfn = lambda t: mp.Vl
        tfn = lambda t, _Tl=Tl, _ton=ton, _toff=toff: torque_pulse(t, _Tl, _ton, _toff)
        t_ev = [ton, toff]
    elif exp == "gerador":
        Tn=-config["Tl_mec"]
        vfn = lambda t: mp.Vl
        tfn = lambda t: Tn
        t_ev = [config["t_2"]]
    elif exp == "shutdown":
        Tl    = config["Tl_final"]
        tc    = config["t_carga"]
        t_cut = config["t_cutoff"]
        vfn = lambda t, _Vl=mp.Vl, _tc=t_cut: _Vl if t < _tc else 0.0
        tfn = lambda t, _Tl=Tl, _tc=tc: torque_step(t, 0.0, _Tl, _tc)
        t_ev = [tc, t_cut]
    else:
        vfn = lambda t: mp.Vl
        tfn = lambda t: 0.0
    return vfn, tfn, t_ev



