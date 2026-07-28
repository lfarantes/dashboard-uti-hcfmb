import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
import altair as alt

# --- Configuração da Página ---
st.set_page_config(layout="wide", page_title="Dashboard Departamental UTI")
st.title("Dashboard Departamental UTI")
st.markdown("Indicadores de performance dos departamentos da UTI.")

# --- Funções da API (Backend) ---
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
        
        # --- Conversão de Tipo de Dados Importante ---
        # Converte colunas numéricas de forma robusta. 
        # Se um campo não existir, ele simplesmente o ignora.
        cols_numericas = ['numero_leitos_disponiveis', 'numero_leitos_ocupados', 'numero_enfermagem', 'numero_tecnico_enfermagem']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão/API: {e}")
        return None

# --- Interface do Usuário (Streamlit) ---
api_url = st.secrets.get("REDCAP_API_URL")

if not api_url:
    st.error("URL da API do REDCap não encontrada nos segredos.")
    st.stop()

# --- Criação das Abas (Tabs) ---
tab_nutri, tab_fisio, tab_med, tab_enf = st.tabs([
    "📊 Nutrição", 
    "🏃 Fisioterapia", 
    "👨‍⚕️ Médica", 
    "📋 Enfermagem"
])

# ### ---------------------------------------------------
# ### ABA DE NUTRIÇÃO (Estável)
# ### ---------------------------------------------------
with tab_nutri:
    st.subheader("Indicadores de Desempenho - Nutrição")
    
    # 1. BOTÃO DE CARREGAMENTO (para o projeto GERAL)
    if st.button("Buscar Dados de Nutrição / Gerais"):
        token_geral = st.secrets.get("TOKEN_PROJETO_GERAL")
        if not token_geral:
            st.error("TOKEN_PROJETO_GERAL não encontrado nos segredos.")
            st.stop()
        
        with st.spinner("Buscando registros gerais..."):
            st.session_state.df_geral = get_project_records(api_url, token_geral)
            if st.session_state.df_geral is not None:
                st.success(f"{len(st.session_state.df_geral)} registros gerais carregados.")
            else:
                st.session_state.df_geral = None

    # 2. BLOCO DE EXIBIÇÃO (só roda se os dados gerais existirem)
    if st.session_state.get('df_geral') is not None:
        
        df_records = st.session_state.df_geral 
        
        # --- LINHA DE KPIs PRINCIPAIS ---
        st.write("#### Visão Geral dos Registros (Projeto Geral)")
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
        st.write("#### Análise Filtrada Interativa (Nutrição)")

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
                index=current_month_index,
                key='nutri_month' # Chave única para este widget
            )
            target_month = month_map[month_name]
        with filter_widget_col2:
            current_year = datetime.now().year
            target_year = st.number_input(
                "Digite o Ano",
                min_value=2010,
                max_value=2050,
                value=current_year,
                key='nutri_year' # Chave única
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
                df_pie = pd.DataFrame({
                    'Categoria': ['Desnutridos', 'Não Desnutridos'],
                    'Contagem': [numerador, nao_desnutridos]
                })
                df_pie['Percentual'] = (df_pie['Contagem'] / denominador)

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
            st.warning(f"Não foi possível calcular a análise. Verifique se as colunas '{col_desnutricao}' e '{col_data}' existem no projeto.")

        # --- SEÇÃO DE GRÁFICO DE TAXA (GRÁFICO DE BARRAS) ---
        st.divider()
        st.write(f"#### Visualização: Taxa de Desnutrição por Mês em {target_year}")
        if col_data in df_records.columns and col_desnutricao in df_records.columns:
            date_series_full = pd.to_datetime(df_records[col_data], errors='coerce')
            df_year = df_records[date_series_full.dt.year == target_year].copy()
            if df_year.empty:
                st.info(f"Nenhum dado de admissão encontrado para {target_year}.")
            else:
                df_year['month'] = pd.to_datetime(df_year[col_data], errors='coerce').dt.month
                denominador_por_mes = df_year['month'].value_counts().reindex(range(1, 13), fill_value=0).sort_index()
                cond_desnutricao_year = (df_year[col_desnutricao].fillna('').astype(str).str.lower().str.strip() == 'sim')
                numerador_por_mes = df_year[cond_desnutricao_year]['month'].value_counts().reindex(range(1, 13), fill_value=0).sort_index()
                
                taxa_por_mes = (numerador_por_mes / denominador_por_mes) * 100
                taxa_por_mes = taxa_por_mes.replace([pd.NA, float('inf'), -float('inf')], 0)
                
                taxa_por_mes.name = "Taxa de Desnutrição (%)"
                taxa_por_mes.index.name = "MonthNumber"
                chart_data = taxa_por_mes.reset_index()

                month_num_to_name_map = {i+1: name for i, name in enumerate(month_names)}
                chart_data['Mês'] = chart_data['MonthNumber'].map(month_num_to_name_map)

                chart = alt.Chart(chart_data).mark_bar().encode(
                    x=alt.X('Mês', sort=month_names),
                    y=alt.Y('Taxa de Desnutrição (%)'),
                    tooltip=['Mês', alt.Tooltip('Taxa de Desnutrição (%)', format='.2f')]
                ).interactive()

                st.altair_chart(chart, use_container_width=True)
        else:
            st.info(f"Não é possível gerar o gráfico. Colunas '{col_data}' ou '{col_desnutricao}' não encontradas.")
    else:
        st.info("Por favor, clique no botão 'Buscar Dados de Nutrição / Gerais' para carregar os indicadores.")

# ### ---------------------------------------------------
# ### ABA DE FISIOTERAPIA (Placeholder)
# ### ---------------------------------------------------
with tab_fisio:
    st.subheader("Indicadores de Desempenho - Fisioterapia")
    
    if st.session_state.get('df_geral') is None:
        st.warning("Os dados gerais ainda não foram carregados. Por favor, carregue os dados na aba 'Nutrição' primeiro.")
    else:
        df_records = st.session_state.df_geral
        st.success(f"Dados gerais ({len(df_records)} registros) carregados.")
        st.info("KPIs e gráficos de Fisioterapia estão em construção.")

# ### ---------------------------------------------------
# ### ABA MÉDICA (Placeholder)
# ### ---------------------------------------------------
with tab_med:
    st.subheader("Indicadores de Desempenho - Médica")
    
    if st.session_state.get('df_geral') is None:
        st.warning("Os dados gerais ainda não foram carregados. Por favor, carregue os dados na aba 'Nutrição' primeiro.")
    else:
        df_records = st.session_state.df_geral
        st.success(f"Dados gerais ({len(df_records)} registros) carregados.")
        st.info("KPIs e gráficos da equipe Médica estão em construção.")

# ### ---------------------------------------------------
# ### ABA DE ENFERMAGEM (NOSSO NOVO SPRINT)
# ### ---------------------------------------------------
with tab_enf:
    st.subheader("Indicadores de Desempenho - Enfermagem")
    
    # 1. BOTÃO DE CARREGAMENTO (para o projeto de ENFERMAGEM)
    if st.button("Buscar Dados de Enfermagem"):
        token_enf = st.secrets.get("TOKEN_PROJETO_ENFERMAGEM")
        if not token_enf:
            st.error("TOKEN_PROJETO_ENFERMAGEM não encontrado nos segredos.")
            st.stop()
            
        with st.spinner("Buscando registros de enfermagem..."):
            st.session_state.df_enfermagem = get_project_records(api_url, token_enf)
            
            if st.session_state.df_enfermagem is not None:
                st.success(f"{len(st.session_state.df_enfermagem)} registros de enfermagem carregados.")
            else:
                st.session_state.df_enfermagem = None

    # 2. BLOCO DE EXIBIÇÃO (só roda se os dados de ENFERMAGEM existirem)
    if st.session_state.get('df_enfermagem') is not None:
        
        df_enf = st.session_state.df_enfermagem
        
        # --- SEÇÃO INTERATIVA (REUTILIZADA DA NUTRIÇÃO) ---
        st.write("#### Análise Filtrada (Enfermagem)")

        month_map_enf = {
            'Janeiro': 1, 'Fevereiro': 2, 'Março': 3, 'Abril': 4,
            'Maio': 5, 'Junho': 6, 'Julho': 7, 'Agosto': 8,
            'Setembro': 9, 'Outubro': 10, 'Novembro': 11, 'Dezembro': 12
        }
        month_names_enf = list(month_map_enf.keys())

        filter_widget_col1, filter_widget_col2 = st.columns(2)
        with filter_widget_col1:
            current_month_index_enf = datetime.now().month - 1
            month_name_enf = st.selectbox(
                "Selecione o Mês",
                options=month_names_enf,
                index=current_month_index_enf,
                key='enf_month' # Chave única
            )
            target_month_enf = month_map_enf[month_name_enf]
        with filter_widget_col2:
            current_year_enf = datetime.now().year
            target_year_enf = st.number_input(
                "Digite o Ano",
                min_value=2010,
                max_value=2050,
                value=current_year_enf,
                key='enf_year' # Chave única
            )

        # Nomes das colunas do seu dicionário
        col_data_enf = 'data'
        col_ocupados = 'numero_leitos_ocupados'
        col_disponiveis = 'numero_leitos_disponiveis'

        # Verifica se as colunas essenciais existem
        if col_data_enf in df_enf.columns and col_ocupados in df_enf.columns and col_disponiveis in df_enf.columns:

            # 1. Filtra o DataFrame pelo Mês e Ano selecionados
            date_series_enf = pd.to_datetime(df_enf[col_data_enf], errors='coerce')
            filtro_mes = (date_series_enf.dt.month == target_month_enf)
            filtro_ano = (date_series_enf.dt.year == target_year_enf)
            
            df_filtrado_enf = df_enf[filtro_mes & filtro_ano]

            if df_filtrado_enf.empty:
                st.warning(f"Nenhum registro de enfermagem encontrado para {month_name_enf} de {target_year_enf}.")
            else:
                # 2. Calcula os "Leitos-dia" (Soma)
                denominador_enf = df_filtrado_enf[col_disponiveis].sum()
                numerador_enf = df_filtrado_enf[col_ocupados].sum()

                # 3. Calcula a Taxa
                if denominador_enf > 0:
                    taxa_ocupacao_enf = (numerador_enf / denominador_enf) * 100
                else:
                    taxa_ocupacao_enf = 0.0

                # 4. Exibe os KPIs
                st.write(f"**Resultados para {month_name_enf} de {target_year_enf}**")
                kpi_enf_1, kpi_enf_2, kpi_enf_3 = st.columns(3)

                with kpi_enf_1:
                    st.metric(label="Leitos-dia Disponíveis (Soma)", value=f"{denominador_enf:,.0f}")
                with kpi_enf_2:
                    st.metric(label="Leitos-dia Ocupados (Soma)", value=f"{numerador_enf:,.0f}")
                with kpi_enf_3:
                    st.metric(label="Taxa de Ocupação (%)", value=f"{taxa_ocupacao_enf:.2f} %")

        else:
            st.error(f"Não foi possível calcular o KPI. Verifique se as colunas `{col_data_enf}`, `{col_ocupados}` e `{col_disponiveis}` existem no projeto de Enfermagem.")

    else:
        st.info("Por favor, clique no botão 'Buscar Dados de Enfermagem' para carregar os indicadores.")