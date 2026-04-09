    # ── DEBUG: RMS de todas as variáveis no regime permanente ────────────────
    st.divider()
    st.markdown("**[DEBUG] RMS das variáveis no regime permanente**")
    _rms_keys = [
        ("ias","ias_rms"), ("ibs","ibs_rms"), ("ics","ics_rms"),
        ("iar","iar_rms"), ("ibr","ibr_rms"), ("icr","icr_rms"),
        ("ids","ids_rms"), ("iqs","iqs_rms"), ("idr","idr_rms"), ("iqr","iqr_rms"),
        ("Va","Va_rms"),   ("Vb","Vb_rms"),   ("Vc","Vc_rms"),
        ("Vds","Vds_rms"), ("Vqs","Vqs_rms"),
    ]
    _debug_rows = [{"Variável": k, "RMS (regime)": f"{res[rk]:.6f}"}
                   for k, rk in _rms_keys if rk in res]
    st.dataframe(_debug_rows, width='stretch')