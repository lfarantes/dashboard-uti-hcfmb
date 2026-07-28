import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime 
import altair as alt

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="REDCap Project Viewer")
st.title("Visualizador de Projetos REDCap")
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

def get_project_metadata(api_url: str, api_token: str) -> pd.DataFrame:
    """Busca o Dicionário de Dados (metadata) de um projeto REDCap."""
    payload = {
        'token': api_token,
        'content': 'metadata',
        'format': 'json',
        'returnFormat': 'json'
    }
    
    try:
        response = requests.post(api_url, data=payload, timeout=10)
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
            st.warning("Dicionário de dados carregado, mas está vazio.")
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
tab1, tab2, tab3 = st.tabs([
    "📊 Informações do Projeto", 
    "📋 Registros", 
    "📖 Dicionário de Dados"
])

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

with tab2:
    # (Nenhuma alteração na Aba 2, exceto na Seção de Gráfico de Barras)
    st.subheader("Dados dos Registros (Participantes)")
    st.markdown("Isto irá carregar **todos** os registros do projeto.")
        
    # 1. BOTÃO DE CARREGAMENTO
    if st.button("Buscar Registros"):
        with st.spinner("Buscando registros... Isso pode levar um momento."):
            st.session_state.df_records = get_project_records(api_url, api_token)
            
            if st.session_state.df_records is not None:
                st.success(f"{len(st.session_state.df_records)} registros carregados.")
            else:
                st.session_state.df_records = None 
    
    # 2. BLOCO DE EXIBIÇÃO
    if st.session_state.get('df_records') is not None:
        
        df_records = st.session_state.df_records
        
        # --- LINHA DE KPIs PRINCIPAIS ---
        st.write("#### Visão Geral dos Registros")
        kpi_col1, kpi_col2 = st.columns(2)
        
        with kpi_col1:
            st.metric(label="Total de Registros Carregados", value=len(df_records))
        
        with kpi_col2:
            target_column = 'diagnostico_desnutricao'
            target_value = 'sim' 
            if target_column in df_records.columns:
                standardized_col = df_records[target_column].fillna('').astype(str).str.lower().str.strip()
                count = (standardized_col == target_value).sum()
                st.metric(label=f"Total de '{target_column}' = 'Sim' (Geral)", value=f"{count} registros")
            else:
                st.info(f"Coluna '{target_column}' não encontrada para contagem.")
        st.divider() 
        
        # --- SEÇÃO INTERATIVA ---
        st.write("#### Análise Filtrada Interativa")
        
        month_map = {
            'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
            'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
            'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
        }
        month_names = list(month_map.keys())
        
        filter_widget_col1, filter_widget_col2 = st.columns(2)
        with filter_widget_col1:
            current_month_index = datetime.now().month - 1
            month_name = st.selectbox(
                "Selecione o Mês", 
                options=month_names,
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
        
        col_desnutricao = 'diagnostico_desnutricao'
        col_data = 'data_e_hora_admissao_uti'
        
        if col_desnutricao in df_records.columns and col_data in df_records.columns:
            
            date_series = pd.to_datetime(df_records[col_data], errors='coerce')
            cond1_desnutricao = (df_records[col_desnutricao].fillna('').astype(str).str.lower().str.strip() == 'sim')
            cond2_mes = (date_series.dt.month == target_month)
            cond3_ano = (date_series.dt.year == target_year)
            
            denominador = (cond2_mes & cond3_ano).sum()
            numerador = (cond1_desnutricao & cond2_mes & cond3_ano).sum()
            
            if denominador > 0:
                taxa_desnutricao = (numerador / denominador) * 100
            else:
                taxa_desnutricao = 0.0

            st.write(f"**Resultados para {month_name} de {target_year}**")
            filter_metric_col1, filter_metric_col2, filter_metric_col3 = st.columns(3)
            
            with filter_metric_col1:
                st.metric(label=f"Total de Admissões", value=denominador)
            with filter_metric_col2:
                st.metric(label=f"Total de Desnutridos", value=numerador)
            with filter_metric_col3:
                st.metric(label=f"Taxa de Desnutrição (%)", 
                          value=f"{taxa_desnutricao:.2f} %")

            # --- SEÇÃO DO GRÁFICO DE PIZZA ---
            if denominador > 0:
                nao_desnutridos = denominador - numerador
                perc_desnutridos = (numerador / denominador)
                perc_nao_desnutridos = (nao_desnutridos / denominador)
                
                df_pie = pd.DataFrame({
                    'Categoria': ['Desnutridos', 'Não Desnutridos'],
                    'Contagem': [numerador, nao_desnutridos],
                    'Percentual': [perc_desnutridos, perc_nao_desnutridos]
                })

                base = alt.Chart(df_pie).encode(
                   theta=alt.Theta("Contagem:Q", stack=True)
                ).properties(
                     title=f"Distribuição de Admissões ({month_name} {target_year})"
                )

                pie = base.mark_arc(outerRadius=120, innerRadius=0).encode(
                    color=alt.Color("Categoria:N",
                                    scale=alt.Scale(domain=['Desnutridos', 'Não Desnutridos'],
                                                    range=['#FF4B4B', '#0068C9'])),
                    order=alt.Order("Percentual", sort="descending"),
                    tooltip=["Categoria", "Contagem", alt.Tooltip("Percentual", format=".1%")]
                )
                
                text = base.mark_text(radius=140).encode(
                    text=alt.Text("Percentual", format=".1%"),
                    order=alt.Order("Percentual", sort="descending"),
                    color=alt.value("black")
                )

                final_pie_chart = pie + text
                st.altair_chart(final_pie_chart, use_container_width=True)
            
            else:
                st.info(f"Nenhum dado de admissão em {month_name} de {target_year} para gerar o gráfico de pizza.")
            
        else:
            st.warning(f"Não foi possível calcular a análise filtrada. Verifique se as colunas '{col_desnutricao}' e '{col_data}' existem no projeto.")
        
        # ### ---------------------------------------------------
        # ### SEÇÃO DE GRÁFICO DE BARRAS (MODIFICADA COM A CORREÇÃO)
        # ### ---------------------------------------------------
        st.divider()
        st.write(f"#### Visualização: Admissões por Mês em {target_year}")

        if col_data in df_records.columns:
            date_series = pd.to_datetime(df_records[col_data], errors='coerce')
            admissions_in_year = date_series[date_series.dt.year == target_year]
            
            month_counts = admissions_in_year.dt.month.value_counts() \
                            .reindex(range(1, 13), fill_value=0) \
                            .sort_index()
            
            month_counts.name = "Contagem de Admissões"
            
            # --- Início da Correção ---
            # 1. Força o nome do índice da Série
            month_counts.index.name = 'MonthNumber'
            
            # 2. Reseta o índice. Agora o DataFrame terá colunas:
            #    'MonthNumber' (de 1 a 12) e 'Contagem de Admissões'
            chart_data = month_counts.reset_index()
            # --- Fim da Correção ---

            # 3. Mapeia o número do mês para o nome do mês
            month_num_to_name_map = {i+1: name for i, name in enumerate(month_names)}
            chart_data['Mês'] = chart_data['MonthNumber'].map(month_num_to_name_map)

            # 4. Criar o gráfico com Altair
            chart = alt.Chart(chart_data).mark_bar().encode(
                # 5. Força a ordem cronológica
                x=alt.X('Mês', sort=month_names),
                
                y=alt.Y('Contagem de Admissões'),
                tooltip=['Mês', 'Contagem de Admissões']
            ).interactive()
            
            # 6. Exibir o gráfico
            st.altair_chart(chart, use_container_width=True)
            
        else:
            st.info(f"Não é possível gerar o gráfico. A coluna '{col_data}' não foi encontrada.")
        
        # --- TABELA DE DADOS ---
        st.divider()
        st.dataframe(df_records, use_container_width=True, height=400)
        
        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')
        csv_data = convert_df_to_csv(df_records)
        project_id = st.session_state.get('project_data', {}).get('project_id', 'data')
        st.download_button(label="Baixar dados como CSV", data=csv_data, file_name=f"redcap_export_{project_id}.csv", mime='text/csv')

with tab3:
    # (Nenhuma alteração na Aba 3)
    st.subheader("Dicionário de Dados (Metadata)")
    st.markdown("Busque todos os campos, formulários e lógica do seu projeto.")

    if st.button("Buscar Dicionário de Dados"):
        with st.spinner("Carregando metadata..."):
            st.session_state.df_metadata = get_project_metadata(api_url, api_token)
            
            if st.session_state.df_metadata is not None:
                st.success("Dicionário de dados carregado com sucesso.")
            else:
                st.session_state.df_metadata = None

    if st.session_state.get('df_metadata') is not None:
        df_metadata = st.session_state.df_metadata
        
        st.info(f"Dicionário carregado com **{len(df_metadata)}** campos (variáveis) definidos.")
        
        st.write("#### Colunas Essenciais do Dicionário")
        useful_cols = [
            'field_name', 'form_name', 'field_label', 
            'field_type', 'select_choices_or_calculations', 'required_field'
        ]
        display_cols = [col for col in useful_cols if col in df_metadata.columns]
        st.dataframe(df_metadata[display_cols], use_container_width=True, height=600)

        with st.expander("Ver Dicionário de Dados Completo (Todas as Colunas)"):
            st.dataframe(df_metadata, use_container_width=True)
            
        @st.cache_data
        def convert_metadata_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')
        csv_metadata = convert_metadata_to_csv(df_metadata)
        project_id = st.session_state.get('project_data', {}).get('project_id', 'data_dict')
        
        st.download_button(
            label="Baixar Dicionário como CSV",
            data = csv_metadata,
            file_name = f"REDCap_DataDictionary_{project_id}.csv",
            mime = 'text/csv',
        )