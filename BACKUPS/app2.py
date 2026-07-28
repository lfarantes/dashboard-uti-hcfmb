import streamlit as st
import requests
import pandas as pd
import json

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="REDCap Project Viewer")
st.title("👁️ Visualizador de Projetos REDCap")
st.markdown("Insira suas credenciais da API para carregar os dados do projeto.")

# --- Funções da API (Backend) ---

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
    placeholder="https://redcap.hcfmb.unesp.br/api/"
)

api_token = st.sidebar.text_input(
    "214FFE1567BA30B88DF4ED0A80D648F6",
    value=default_token,
    type="password",
    placeholder="Cole seu token de API aqui"
)

if not api_url or not api_token:
    st.info("Por favor, insira a URL da API e o Token na barra lateral para começar.")
    st.stop()

# --- Criação das Abas (Tabs) ---
tab1, tab2 = st.tabs(["📊 Informações do Projeto", "📋 Registros"])

# ### ---------------------------------------------------
# ### MUDANÇAS SOMENTE DENTRO DESTA ABA (tab1)
# ### ---------------------------------------------------
with tab1:
    st.subheader("Visão Geral do Projeto")
    
    if st.button("Buscar Informações do Projeto"):
        with st.spinner("Conectando ao REDCap..."):
            # 1. Buscamos o JSON, como antes
            project_data = get_project_info(api_url, api_token)
            
            if project_data:
                st.success(f"Projeto '{project_data.get('project_title')}' carregado!")
                
                # 2. Exibição Curada (Dashboard)
                st.markdown(f"### {project_data.get('project_title', 'Título não encontrado')}")
                
                # Usamos colunas para organizar as métricas
                col1, col2, col3 = st.columns(3)
                
                # Coluna 1: IDs e Status
                with col1:
                    st.metric("Project ID", project_data.get('project_id', 'N/A'))
                    
                    # Lógica para status de produção
                    in_prod = project_data.get('in_production', 0)
                    if in_prod == 1:
                        st.success("Status: Em Produção")
                    else:
                        st.warning("Status: Em Desenvolvimento")

                # Coluna 2: Datas
                with col2:
                    creation_time = project_data.get('creation_time', 'N/A').split(' ')[0] # Pega só a data
                    st.metric("Data de Criação", creation_time)
                    
                    prod_time = project_data.get('production_time', '')
                    prod_time_display = prod_time.split(' ')[0] if prod_time else "N/A"
                    st.metric("Em Produção Desde", prod_time_display)

                # Coluna 3: Configurações Chave
                with col3:
                    longitudinal = "Sim" if project_data.get('is_longitudinal', 0) == 1 else "Não"
                    st.metric("É Longitudinal?", longitudinal)
                    
                    surveys = "Sim" if project_data.get('surveys_enabled', 0) == 1 else "Não"
                    st.metric("Pesquisas Habilitadas?", surveys)

                st.divider() # Linha horizontal

                # Seção de Detalhes Adicionais
                st.write(f"**Custom Record Label:** `{project_data.get('custom_record_label', 'N/A')}`")
                st.write(f"**Linguagem:** {project_data.get('project_language', 'N/A')}")
                notes = project_data.get('project_notes', '')
                if notes:
                    st.caption(f"**Notas do Projeto:** {notes}")
                
                # 3. O "Data Dump" agora fica escondido aqui
                with st.expander("Ver todos os campos (JSON Bruto)"):
                    st.json(project_data) # st.json é perfeito para isso

# --- Conteúdo da Aba 2: Registros (Sem alterações) ---
with tab2:
    st.subheader("Dados dos Registros (Participantes)")
    st.markdown("Isto irá carregar **todos** os registros do projeto.")
    
    if st.button("Buscar Registros"):
        with st.spinner("Buscando registros... Isso pode levar um momento."):
            df_records = get_project_records(api_url, api_token)
            
            if df_records is not None:
                st.success(f"{len(df_records)} registros carregados com sucesso.")
                st.dataframe(df_records, use_container_width=True, height=600)
                
                @st.cache_data
                def convert_df_to_csv(df):
                    return df.to_csv(index=False).encode('utf-8')

                csv_data = convert_df_to_csv(df_records)
                st.download_button(
                    label="Baixar dados como CSV",
                    data=csv_data,
                    file_name=f"redcap_export_{project_data.get('project_id', 'data')}.csv",
                    mime='text/csv',
                )