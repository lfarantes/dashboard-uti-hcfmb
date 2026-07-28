import streamlit as st
import pandas as pd
import datetime
import logging
import numpy as np

# Módulos do projeto
import indicadores_clinicos 
from data_loader import load_redcap_data 
import admin_report

# --- Configuração da Página ---
st.set_page_config(
    page_title="Gestão UTI Clínica HCFMB",
    page_icon="🏥",
    layout="wide"
)

# --- Sidebar de Filtros ---
with st.sidebar:
    st.title("Filtros de Análise")
    today = datetime.date.today()
    default_year = today.year
    default_month = today.month
    year_options = list(range(default_year - 5, default_year + 1))
    selected_year = st.selectbox("Ano", options=year_options, index=len(year_options) - 1)
    
    months = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, 
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8, 
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    month_name = st.selectbox("Mês", options=months.keys(), index=default_month - 1)
    selected_month = months[month_name]

    st.markdown("---") 
    if st.button("Recarregar Dados (Limpar Cache)"):
        st.cache_data.clear()
        st.rerun()

# --- Carregamento dos Dados ---
@st.cache_data
def get_data(api_key_geral, api_key_enfermagem):
    try:
        df_admin, df_clinico = load_redcap_data(api_key_geral, api_key_enfermagem)
        return df_admin, df_clinico
    except Exception as e:
        st.error(f"Erro na conexão com REDCap: {e}")
        st.stop()

try:
    df_admin_data, df_clinical_data = get_data(
        st.secrets["api_key_geral"], 
        st.secrets["api_key_enfermagem"]
    )
except Exception as e:
    st.error("Verifique as chaves de API nos Secrets do Streamlit.")
    st.stop()

# --- Título Principal ---
st.title(f"Dashboard de Gestão – UTI Clínica")
st.markdown(f"### Análise de {month_name} de {selected_year}")

# --- Criação das Abas ---
tab_medica, tab_enfermagem, tab_fisioterapia, tab_nutricao = st.tabs(
    ["Médica", "Enfermagem", "Fisioterapia", "Nutrição"]
)

# --- Aba 1: Médica ---
with tab_medica:
    st.subheader("Indicadores Médicos")
    if not df_clinical_data.empty:
        # Cálculos Médicos de Resultado
        taxa_mortalidade, num_obitos, num_desfechos = indicadores_clinicos.calculate_taxa_mortalidade_uti(df_clinical_data, selected_month, selected_year)
        taxa_mort_hosp, num_obitos_hosp, num_desfechos_hosp = indicadores_clinicos.calculate_taxa_mortalidade_hospitalar(df_clinical_data, selected_month, selected_year)
        media_permanencia, num_pac_dias, num_desfechos_perm = indicadores_clinicos.calculate_tempo_medio_permanencia(df_clinical_data, selected_month, selected_year)
        taxa_reint_48h, num_reint, num_altas_reint = indicadores_clinicos.calculate_taxa_reinternacao_48h(df_clinical_data, selected_month, selected_year)
        taxa_resol_48h, num_resol, num_altas_resol = indicadores_clinicos.calculate_taxa_resolicitacao_48h(df_clinical_data, selected_month, selected_year)
        
        # Cálculos de Desempenho (SMR e SRU)
        smr_val, tx_obs, tx_esp, m_saps_val, den_val, num_val, ids_den, ids_num = indicadores_clinicos.calculate_smr(df_clinical_data, selected_month, selected_year)
        sru_val, dias_obs, dias_esp = indicadores_clinicos.calculate_sru(df_clinical_data, selected_month, selected_year)

        # --- EXIBIÇÃO: SMR / SRU ---
        st.markdown("---")
        st.write("#### 📊 Desempenho Clínico (SMR / SRU)")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SMR (Padronizado)", f"{smr_val:.2f}", delta=f"{smr_val - 1:.2f}", delta_color="inverse")
        c2.metric("SRU (Recursos)", f"{sru_val:.2f}", delta=f"{sru_val - 1:.2f}", delta_color="inverse")
        c3.metric("Admitidos (Denom.)", f"{den_val}")
        c4.metric("Média SAPS 3", f"{m_saps_val:.1f} pts")

        with st.expander("🔍 Auditoria SMR: Lista de IDs Processados"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.write(f"**IDs Admitidos ({len(ids_den)}):**")
                st.code(", ".join(map(str, ids_den)))
            with col_b:
                st.write(f"**IDs com Desfecho Hosp. ({len(ids_num)}):**")
                st.code(", ".join(map(str, ids_num)))

        # --- EXIBIÇÃO: RESULTADOS ---
        st.markdown("---")
        st.write("#### Indicadores de Resultado")
        colR1, colR2, colR3 = st.columns(3)
        colR1.metric("Mortalidade UTI", f"{taxa_mortalidade:.1f} %")
        colR2.metric("Mortalidade Hospitalar", f"{taxa_mort_hosp:.1f} %")
        colR3.metric("Permanência Média", f"{media_permanencia:.1f} dias")

        colR4, colR5, _ = st.columns(3)
        colR4.metric("Reinternação 48h", f"{taxa_reint_48h:.1f} %")
        colR5.metric("Re-solicitação 48h", f"{taxa_resol_48h:.1f} %")

# --- Aba 2: Enfermagem ---
with tab_enfermagem:
    st.subheader("Indicadores de Enfermagem")
    if not df_admin_data.empty:
        admin_report.display_admin_metrics(df_admin_data, selected_month, selected_year)
    
    st.markdown("---")
    if not df_clinical_data.empty:
        st.write("#### Utilização de Dispositivos (Diário)")
        t_cvc, n_cvc, _ = indicadores_clinicos.calculate_taxa_utilizacao_cvc(df_clinical_data, selected_month, selected_year)
        t_svd, n_svd, _ = indicadores_clinicos.calculate_taxa_utilizacao_svd(df_clinical_data, selected_month, selected_year)
        t_dial, n_dial, _ = indicadores_clinicos.calculate_taxa_utilizacao_dialise(df_clinical_data, selected_month, selected_year)
        t_dva, n_dva, _ = indicadores_clinicos.calculate_taxa_utilizacao_dva(df_clinical_data, selected_month, selected_year)
        
        ce1, ce2, ce3, ce4 = st.columns(4)
        ce1.metric("Taxa Utilização CVC", f"{t_cvc:.1f} %")
        ce2.metric("Taxa Utilização SVD", f"{t_svd:.1f} %")
        ce3.metric("Taxa Utilização Diálise", f"{t_dial:.1f} %")
        ce4.metric("Taxa Utilização DVA", f"{t_dva:.1f} %")

        st.markdown("---")
        st.write("#### Indicadores de Incidência (Evento)")
        t_lpp, n_lpp, _ = indicadores_clinicos.calculate_taxa_incidencia_lpp(df_clinical_data, selected_month, selected_year)
        t_fleb, n_fleb, _ = indicadores_clinicos.calculate_taxa_incidencia_flebite(df_clinical_data, selected_month, selected_year)
        
        ce5, ce6 = st.columns(2)
        ce5.metric("Taxa Incidência LPP", f"{t_lpp:.1f} %")
        ce6.metric("Taxa Incidência Flebite", f"{t_fleb:.1f} %")

# --- Aba 3: Fisioterapia ---
with tab_fisioterapia:
    st.subheader("Indicadores de Fisioterapia")
    if not df_clinical_data.empty:
        m_vm, t_vm, p_vm = indicadores_clinicos.calculate_tempo_medio_vm(df_clinical_data, selected_month, selected_year)
        t_util_vm, _, _ = indicadores_clinicos.calculate_taxa_utilizacao_vm(df_clinical_data, selected_month, selected_year)
        
        st.write("#### Ventilação Mecânica")
        cf1, cf2 = st.columns(2)
        cf1.metric("Tempo Médio de VM", f"{m_vm:.1f} dias")
        cf2.metric("Taxa de Utilização de VM", f"{t_util_vm:.1f} %")

        st.markdown("---")
        st.write("#### Extubação (EOT)")
        t_pal, n_pal, _ = indicadores_clinicos.calculate_taxa_eot_paliativa(df_clinical_data, selected_month, selected_year)
        t_acid, n_acid, _ = indicadores_clinicos.calculate_taxa_eot_acidental(df_clinical_data, selected_month, selected_year)
        t_iot, n_iot, _ = indicadores_clinicos.calculate_taxa_re_iot(df_clinical_data, selected_month, selected_year)
        
        cf3, cf4, cf5 = st.columns(3)
        cf3.metric("EOT Paliativa", f"{t_pal:.1f} %")
        cf4.metric("EOT Acidental", f"{t_acid:.1f} %")
        cf5.metric("Re-IOT 48h", f"{t_iot:.1f} %")

# --- Aba 4: Nutrição ---
with tab_nutricao:
    st.subheader("Indicadores de Nutrição")
    if not df_clinical_data.empty:
        t_desn, n_desn, _ = indicadores_clinicos.calculate_taxa_desnutricao(df_clinical_data, selected_month, selected_year)
        t_dieta, v_inf, v_pres = indicadores_clinicos.calculate_relacao_dieta(df_clinical_data, selected_month, selected_year)
        m_meta, _, _ = indicadores_clinicos.calculate_tempo_ate_meta(df_clinical_data, selected_month, selected_year)
        
        cn1, cn2, cn3 = st.columns(3)
        cn1.metric("Taxa de Desnutrição", f"{t_desn:.1f} %")
        cn2.metric("Prescrito vs Infundido", f"{t_dieta:.1f} %")
        cn3.metric("Média até a Meta", f"{m_meta:.1f} dias")