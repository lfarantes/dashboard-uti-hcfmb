import streamlit as st
import requests
import pandas as pd
import json

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="REDCap Project Viewer")
st.title("👁️ Visualizador de Projetos REDCap")
st.markdown("Insira suas credenciais da API para carregar os dados do projeto.")

# --- Funções da API (Backend) ---
# (Nenhuma alteração nas funções get_project_info ou get_project_records)

def get_project_info(api_url: str, api_token: str) -> dict:
    """Busca as informações básicas (metadados) de um projeto REDCap."""
    payload = {
        'token': api_token,
        'content': 'project',
        'format': 'json',
        'returnFormat': 'json'
    }
    
    try:
        response = requests.post(api_url, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'error' in data:
            st.error(f"Erro da API REDCap: {data['error']}")
            return None
        return data

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão/API: {e}")
        return None

def get_project_records(api_url: str, api_token: str) -> pd.DataFrame:
    """Busca TODOS os registros (dados) de um projeto REDCap."""
    payload = {
        'token': api_token,
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'rawOrLabel': 'label',
        'exportDataAccessGroups': 'false',
        'returnFormat': 'json'
    }
    
    try:
        response = requests.post(api_url, data=payload, timeout=30)
        response.raise_for_status()
        
        try:
            data = response.json()
            if isinstance(data, dict) and 'error' in data:
                st.error(f"Erro da API REDCap: {data['error']}")
                return None
        except json.JSONDecodeError:
            st.error(f"Resposta inesperada do servidor. Status: {response.status_code}")
            st.text(response.text[:200] + "...")
            return None

        df = pd.DataFrame(data)
        
        if df.empty:
            st.warning("Projeto carregado, mas nenhum registro foi encontrado.")
            return None
            
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão/API: {e}")
        return None

# --- Interface do Usuário (Streamlit) ---

st.sidebar.header("Credenciais da API")
default_url = st.secrets.get("REDCAP_API_URL", "")
default_token = st.secrets.get("REDCAP_TOKEN", "")

api_url = st.sidebar.text_input(
    "URL da API REDCap",
    value=default_url,
    placeholder="https://redcap.suainstituicao.edu/api/"
)

api_token = st.sidebar.text_input(
    "Token da API do Projeto",
    value=default_token,
    type="password",
    placeholder="Cole seu token de API aqui"
)

if not api_url or not api_token:
    st.info("Por favor, insira a URL da API e o Token na barra lateral para começar.")
    st.stop()

# --- Criação das Abas (Tabs) ---
tab1, tab2 = st.tabs(["📊 Informações do Projeto", "📋 Registros"])

with tab1:
    # (Nenhuma alteração na Aba 1)
    st.subheader("Visão Geral do Projeto")
    
    if st.button("Buscar Informações do Projeto"):
        with st.spinner("Conectando ao REDCap..."):
            project_data = get_project_info(api_url, api_token)
            
            if project_data:
                st.session_state.project_data = project_data
                st.success(f"Projeto '{project_data.get('project_title')}' carregado!")
                st.markdown(f"### {project_data.get('project_title', 'Título não encontrado')}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Project ID", project_data.get('project_id', 'N/A'))
                    in_prod = project_data.get('in_production', 0)
                    if in_prod == 1:
                        st.success("Status: Em Produção")
                    else:
                        st.warning("Status: Em Desenvolvimento")
                with col2:
                    creation_time = project_data.get('creation_time', 'N/A').split(' ')[0]
                    st.metric("Data de Criação", creation_time)
                    prod_time = project_data.get('production_time', '')
                    prod_time_display = prod_time.split(' ')[0] if prod_time else "N/A"
                    st.metric("Em Produção Desde", prod_time_display)
                with col3:
                    longitudinal = "Sim" if project_data.get('is_longitudinal', 0) == 1 else "Não"
                    st.metric("É Longitudinal?", longitudinal)
                    surveys = "Sim" if project_data.get('surveys_enabled', 0) == 1 else "Não"
                    st.metric("Pesquisas Habilitadas?", surveys)
                st.divider()
                st.write(f"**Custom Record Label:** `{project_data.get('custom_record_label', 'N/A')}`")
                st.write(f"**Linguagem:** {project_data.get('project_language', 'N/A')}")
                notes = project_data.get('project_notes', '')
                if notes:
                    st.caption(f"**Notas do Projeto:** {notes}")
                with st.expander("Ver todos os campos (JSON Bruto)"):
                    st.json(project_data)

# ### ---------------------------------------------------
# ### MUDANÇAS APENAS DENTRO DESTA ABA (tab2)
# ### ---------------------------------------------------
with tab2:
    st.subheader("Dados dos Registros (Participantes)")
    st.markdown("Isto irá carregar **todos** os registros do projeto.")
    
    # Campo de texto para a soma configurável (da última vez)
    column_to_sum = st.text_input("Nome da Coluna Numérica para Somar", "volume_infundido_ml")
    
    if st.button("Buscar Registros"):
        with st.spinner("Buscando registros... Isso pode levar um momento."):
            df_records = get_project_records(api_url, api_token)
            
            if df_records is not None:
                st.success(f"{len(df_records)} registros carregados com sucesso.")
                
                # --- INÍCIO DA LINHA DE KPIs ---
                
                # Criar colunas para os KPIs
                kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                
                # --- KPI 1: Contagem Total de Registros ---
                with kpi_col1:
                    st.metric(label="Total de Registros Carregados", value=len(df_records))

                # --- KPI 2: Soma da Coluna Configurável ---
                with kpi_col2:
                    if column_to_sum: 
                        if column_to_sum in df_records.columns:
                            numeric_column = pd.to_numeric(df_records[column_to_sum], errors='coerce')
                            total_sum = numeric_column.sum()
                            st.metric(
                                label=f"Soma de '{column_to_sum}'",
                                value=f"{total_sum:,.2f}" 
                            )
                        else:
                            st.warning(f"Coluna '{column_to_sum}' não encontrada para soma.")
                    else:
                        st.info("Insira um nome de coluna acima para ver a soma.")
                
                # --- KPI 3: Contagem de "Diagnóstico Desnutrição" = "Sim" (Seu novo pedido) ---
                with kpi_col3:
                    target_column = 'diagnostico_desnutricao'
                    target_value = 'sim' # Vamos padronizar para minúsculas
                    
                    if target_column in df_records.columns:
                        # Lógica de contagem robusta:
                        # 1. .fillna(''): Trata valores nulos (NaN) para não quebrar o .str
                        # 2. .astype(str): Garante que tudo seja string (caso haja números)
                        # 3. .str.lower(): Padroniza "Sim", "SIM", "sim" para "sim"
                        # 4. .str.strip(): Remove espaços em branco (" sim ")
                        standardized_col = df_records[target_column].fillna('').astype(str).str.lower().str.strip()
                        
                        # Compara com o valor padronizado e soma (True=1, False=0)
                        count = (standardized_col == target_value).sum()
                        
                        st.metric(
                            label=f"Contagem de '{target_column}' = 'Sim'",
                            value=f"{count} registros"
                        )
                    else:
                        # Se a coluna não existe, apenas informa
                        st.info(f"Coluna '{target_column}' não encontrada para contagem.")
                
                st.divider() # Linha horizontal
                # --- FIM DA LINHA DE KPIs ---
                
                
                # Exibe a tabela de dados
                st.dataframe(df_records, use_container_width=True, height=600)
                
                # Lógica do botão de download (sem alteração)
                @st.cache_data
                def convert_df_to_csv(df):
                    return df.to_csv(index=False).encode('utf-8')

                csv_data = convert_df_to_csv(df_records)
                project_id = st.session_state.get('project_data', {}).get('project_id', 'data')

                st.download_button(
                    label="Baixar dados como CSV",
                    data=csv_data,
                    file_name=f"redcap_export_{project_id}.csv",
                    mime='text/csv',
                )