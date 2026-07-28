import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime 

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
# ### MUDANÇA ESTRUTURAL NA ABA 2
# ### ---------------------------------------------------
with tab2:
    st.subheader("Dados dos Registros (Participantes)")
    st.markdown("Isto irá carregar **todos** os registros do projeto.")
    
    column_to_sum = st.text_input("Nome da Coluna Numérica para Somar", "volume_infundido_ml")
    
    # 1. BOTÃO DE CARREGAMENTO
    # A única função deste botão é carregar os dados para o st.session_state
    if st.button("Buscar Registros"):
        with st.spinner("Buscando registros... Isso pode levar um momento."):
            # Salva os dados no 'session_state'
            st.session_state.df_records = get_project_records(api_url, api_token)
            
            if st.session_state.df_records is not None:
                st.success(f"{len(st.session_state.df_records)} registros carregados.")
            else:
                # Se a busca falhar ou retornar vazio, limpamos o state
                st.session_state.df_records = None 
    
    
    # 2. BLOCO DE EXIBIÇÃO
    # Este bloco SÓ é executado se 'df_records' existir no session_state
    # Ele será re-executado toda vez que um widget (como o selectbox) for alterado
    
    if st.session_state.get('df_records') is not None:
        
        # Puxa os dados do state para uma variável local para facilitar
        df_records = st.session_state.df_records
        
        # --- INÍCIO DA LINHA DE KPIs PRINCIPAIS ---
        st.write("#### Visão Geral dos Registros")
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        with kpi_col1:
            st.metric(label="Total de Registros Carregados", value=len(df_records))

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
        
        with kpi_col3:
            target_column = 'diagnostico_desnutricao'
            target_value = 'sim' 
            if target_column in df_records.columns:
                standardized_col = df_records[target_column].fillna('').astype(str).str.lower().str.strip()
                count = (standardized_col == target_value).sum()
                st.metric(
                    label=f"Total de '{target_column}' = 'Sim'",
                    value=f"{count} registros"
                )
            else:
                st.info(f"Coluna '{target_column}' não encontrada para contagem.")
        
        st.divider() 
        # --- FIM DA LINHA DE KPIs PRINCIPAIS ---

        
        # --- INÍCIO DA SEÇÃO INTERATIVA ---
        st.write("#### Análise Filtrada Interativa")
        
        filter_widget_col1, filter_widget_col2 = st.columns(2)
        
        with filter_widget_col1:
            month_map = {
                'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
                'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
                'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
            }
            current_month_index = datetime.now().month - 1
            
            month_name = st.selectbox(
                "Selecione o Mês", 
                options=list(month_map.keys()),
                index=current_month_index 
            )
            target_month = month_map[month_name] 

        with filter_widget_col2:
            current_year = datetime.now().year
            target_year = st.number_input(
                "Digite o Ano",
                min_value=2010, 
                max_value=2050, 
                value=current_year
            )
        
        # --- LÓGICA DE FILTRO DINÂMICO ---
        col_desnutricao = 'diagnostico_desnutricao'
        col_data = 'data_e_hora_admissao_uti'
        
        if col_desnutricao in df_records.columns and col_data in df_records.columns:
            
            cond1_desnutricao = (
                df_records[col_desnutricao].fillna('').astype(str).str.lower().str.strip() == 'sim'
            )
            date_series = pd.to_datetime(df_records[col_data], errors='coerce')
            cond2_mes = (date_series.dt.month == target_month)
            cond3_ano = (date_series.dt.year == target_year)
            
            combined_filter = (cond1_desnutricao & cond2_mes & cond3_ano)
            
            # --- EXIBIÇÃO DAS MÉTRICAS FILTRADAS ---
            filter_metric_col1, filter_metric_col2, filter_metric_col3 = st.columns(3)
            
            with filter_metric_col1:
                st.metric(label=f"Total de Desnutrição ('Sim')", 
                          value=cond1_desnutricao.sum())
            
            with filter_metric_col2:
                st.metric(label=f"Total de Admissões em {month_name}/{target_year}", 
                          value=(cond2_mes & cond3_ano).sum())
            
            with filter_metric_col3:
                st.metric(label=f"COMBINADO ({month_name}/{target_year})", 
                          value=combined_filter.sum())

        else:
            st.warning(f"Não foi possível calcular a análise filtrada. Verifique se as colunas '{col_desnutricao}' e '{col_data}' existem no projeto.")
        
        st.divider()
        # --- FIM DA SEÇÃO INTERATIVA ---

        
        # --- EXIBIÇÃO DA TABELA E DOWNLOAD ---
        st.dataframe(df_records, use_container_width=True, height=400)
        
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