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

    st.markdown("---") 

    if st.button("Recarregar Dados (Limpar Cache)"):
        st.cache_data.clear()
        st.rerun()

# --- Carregamento dos Dados ---
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

# --- Aba 3: Enfermagem ---
with tab_enfermagem:
    st.subheader("Indicadores de Enfermagem")
    st.info("Em desenvolvimento...")

# --- Aba 4: Fisioterapia (COM A NOVA FUNÇÃO) ---
with tab_fisioterapia:
    st.subheader("Indicadores de Fisioterapia")
    
    if not df_clinical_data.empty:
        
        # --- NOSSO NOVO BLOCO DE CÓDIGO ---
        media_dias_vm, total_dias_vm, total_pac_vm = indicadores_clinicos26.calculate_tempo_medio_vm(
            df_clinical_data, selected_month, selected_year
        )
        
        st.metric(
            label="Tempo Médio de VM",
            value=f"{media_dias_vm:.1f} dias",
            help=f"Baseado em {total_dias_vm} dias totais de VM, dividido por {total_pac_vm} pacientes únicos em VM no período. Filtro pelos registros diários do mês."
        )
        # --- FIM DO NOVO BLOCO ---

        st.markdown("---")
        st.markdown("*Indicadores de Taxa de Utilização de VM, EOT... em breve.*")
    else:
        st.warning("Não foi possível carregar os dados clínicos.")

# --- Aba 5: Nutrição ---
with tab_nutricao:
    st.subheader("Indicadores de Nutrição")
    
    if not df_clinical_data.empty:
        
        # --- Cálculo dos Indicadores ---
        taxa_desnutricao, num_desnutridos, num_admissoes = indicadores_clinicos26.calculate_taxa_desnutricao(
            df_clinical_data, selected_month, selected_year
        )
        taxa_dieta, vol_infundido, vol_prescrito = indicadores_clinicos26.calculate_relacao_dieta(
            df_clinical_data, selected_month, selected_year
        )
        media_dias_meta, total_dias, total_pac_meta = indicadores_clinicos26.calculate_tempo_ate_meta(
            df_clinical_data, selected_month, selected_year
        )

        # --- Exibição dos Indicadores ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Taxa de Desnutrição (Admissão)",
                value=f"{taxa_desnutricao:.1f} %",
                help=f"Baseado em {num_desnutridos} paciente(s) desnutridos e {num_admissoes} admissão(ões) total(is) no período. Filtro pelo mês de admissão."
            )
        
        with col2:
            st.metric(
                label="Relação Prescrito vs. Infundido",
                value=f"{taxa_dieta:.1f} %",
                help=f"Total Infundido: {vol_infundido:,.0f} mL / Total Prescrito: {vol_prescrito:,.0f} mL. Filtro pelos registros diários do mês."
            )
        
        with col3:
            st.metric(
                label="Tempo Médio até a Meta",
                value=f"{media_dias_meta:.1f} dias",
                help=f"Soma de {total_dias:,.0f} dias até a meta, dividido por {total_pac_meta} pacientes admitidos no período. Filtro pelo mês de admissão."
            )

        st.markdown("---")
        st.markdown("*Todos os indicadores de Nutrição implementados.*")
    else:
        st.warning("Não foi possível carregar os dados clínicos.")