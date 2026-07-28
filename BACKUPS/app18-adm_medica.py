import streamlit as st
import pandas as pd
import datetime
import logging

# Módulos do projeto
from data_loader import load_redcap_data 
import admin_report 
import indicadores_clinicos26 

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard UTI Clínica",
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
    selected_year = st.selectbox(
        "Ano", 
        options=year_options, 
        index=len(year_options) - 1
    )
    months = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, 
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8, 
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    month_name = st.selectbox(
        "Mês", 
        options=months.keys(), 
        index=default_month - 1
    )
    selected_month = months[month_name]

    st.markdown("---") # Uma linha divisória

    # --- NOSSA NOVA IMPLEMENTAÇÃO DO BOTÃO ---
    if st.button("Recarregar Dados (Limpar Cache)"):
        # Limpa o cache de TODAS as funções que usam @st.cache_data
        st.cache_data.clear()
        # Força a página a recarregar imediatamente
        st.rerun()

# --- Carregamento dos Dados ---
# ATUALIZADO: Removi o ttl="10m". O cache agora é permanente
# até que o botão "Recarregar Dados" seja pressionado.
@st.cache_data 
def get_data(api_key_geral, api_key_enfermagem):
    try:
        df_admin, df_clinico = load_redcap_data(api_key_geral, api_key_enfermagem)
        logging.info(f"Dados admin carregados: {df_admin.shape[0]} linhas")
        logging.info(f"Dados clínicos carregados: {df_clinico.shape[0]} linhas") 
        return df_admin, df_clinico
    except Exception as e:
        logging.error(f"Falha ao carregar dados do REDCap: {e}")
        raise e 

try:
    df_admin_data, df_clinical_data = get_data(
        st.secrets["api_key_geral"], 
        st.secrets["api_key_enfermagem"]
    )
except Exception as e:
    st.error(f"Erro ao carregar dados do REDCap: {e}")
    st.error("Verifique suas chaves de API, URLs e permissões.")
    st.stop()


# --- Título Principal ---
st.title(f"Dashboard de Gestão – UTI Clínica")
st.markdown(f"### Análise de {month_name} de {selected_year}")

# --- Criação das Abas ---
tab_admin, tab_medica, tab_enfermagem, tab_fisioterapia, tab_nutricao = st.tabs(
    ["Administrativo", "Médica", "Enfermagem", "Fisioterapia", "Nutrição"]
)

# --- Aba 1: Administrativo ---
with tab_admin:
    if not df_admin_data.empty:
        admin_report.display_admin_metrics(df_admin_data, selected_month, selected_year)
    else:
        st.warning("Não foi possível carregar os dados administrativos.")

# --- Aba 2: Médica ---
with tab_medica:
    st.subheader("Indicadores Médicos")
    if not df_clinical_data.empty:
        
        # Agora isso deve receber os 3 valores corretamente
        taxa_mortalidade, num_obitos, num_desfechos = indicadores_clinicos26.calculate_taxa_mortalidade_uti(
            df_clinical_data, selected_month, selected_year
        )
        
        st.metric(
            label="Taxa de Mortalidade UTI",
            value=f"{taxa_mortalidade:.1f} %",
            help=f"Baseado em {num_obitos} óbito(s) e {num_desfechos} desfecho(s) total(is) no período selecionado."
        )
        
        st.markdown("---")
        st.markdown("*Indicadores SAPS-3, Mortalidade Hospitalar, Reinternação... em breve.*")
    else:
        st.warning("Não foi possível carregar os dados clínicos.")

# --- Abas Restantes (Placeholders) ---
with tab_enfermagem:
    st.subheader("Indicadores de Enfermagem")
    st.info("Em desenvolvimento...")

with tab_fisioterapia:
    st.subheader("Indicadores de Fisioterapia")
    st.info("Em desenvolvimento...")

with tab_nutricao:
    st.subheader("Indicadores de Nutrição")
    st.info("Em desenvolvimento...")