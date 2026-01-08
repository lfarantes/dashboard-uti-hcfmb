import pandas as pd
import streamlit as st
import logging

def display_admin_metrics(df, selected_month, selected_year):
    """
    Calcula e exibe os indicadores administrativos (Ocupação e Profissionais).
    """
    
    st.subheader("Indicadores Administrativos")

    if df.empty:
        st.warning("Dados administrativos não disponíveis.")
        return

    # --- 1. Verificação de Coluna Crítica ---
    if 'data' not in df.columns:
        st.error(
            "Erro Crítico: A coluna 'data' não foi encontrada no projeto Admin.\n\n"
            "**Ação Necessária:** Verifique as **permissões de exportação da API** "
            "para o campo `[data]` no seu projeto REDCap (UTI Geral)."
        )
        logging.error("Coluna 'data' não encontrada. Verifique as permissões da API.")
        return

    # --- 2. Preparação dos Dados ---
    df_admin = df.copy()
    try:
        # Usar o formato YYYY-MM-DD que é o padrão do export list[dict] do REDCap
        df_admin['data'] = pd.to_datetime(df_admin['data'], format='%Y-%m-%d', errors='coerce')
    except Exception as e:
        # Se falhar, tentar o D/M/Y do seu dicionário
        try:
            df_admin['data'] = pd.to_datetime(df_admin['data'], format='%d/%m/%Y', errors='coerce')
        except Exception as e_inner:
            logging.error(f"Erro ao converter data no admin_report: {e_inner}")
            st.error("Formato de data dos dados administrativos é inválido.")
            return

    # Garantir que as colunas de cálculo são numéricas
    colunas_numericas = ['numero_leitos_ocupados', 'numero_leitos_disponiveis', 'numero_enfermagem', 'numero_tecnico_enfermagem']
    for col in colunas_numericas:
        if col in df_admin.columns:
            df_admin[col] = pd.to_numeric(df_admin[col], errors='coerce')
        else:
            st.error(f"Erro: A coluna numérica '{col}' não foi encontrada.")
            return

    # --- 3. Filtragem pelo Mês/Ano ---
    df_admin = df_admin.dropna(subset=['data'])
    df_filtrado = df_admin[
        (df_admin['data'].dt.month == selected_month) &
        (df_admin['data'].dt.year == selected_year)
    ]

    if df_filtrado.empty:
        st.warning(f"Não há dados administrativos para {selected_month}/{selected_year}.")
        return

    # --- 4. Cálculo e Exibição dos Indicadores ---
    col1, col2, col3 = st.columns(3)
    
    # ... (O restante do código de 'st.metric' permanece o mesmo) ...
    # --- Indicador 1: Taxa de Ocupação da UTI ---
    try:
        leitos_dia_ocupados = df_filtrado['numero_leitos_ocupados'].sum()
        leitos_dia_disponiveis = df_filtrado['numero_leitos_disponiveis'].sum()

        if leitos_dia_disponiveis > 0:
            taxa_ocupacao = (leitos_dia_ocupados / leitos_dia_disponiveis) * 100
        else:
            taxa_ocupacao = 0

        with col1:
            st.metric(
                label="Taxa de Ocupação da UTI",
                value=f"{taxa_ocupacao:.1f} %",
                help=f"Calculado com base em {leitos_dia_ocupados} leitos-dia ocupados e {leitos_dia_disponiveis} leitos-dia disponíveis no período."
            )
    except Exception as e:
        with col1:
            st.error(f"Erro ao calcular Taxa de Ocupação. Erro: {e}")

    # --- Indicador 2: Média de Profissionais de Enfermagem ---
    try:
        media_enfermagem = df_filtrado['numero_enfermagem'].mean()
        with col2:
            st.metric(
                label="Média Diária (Enfermagem)",
                value=f"{media_enfermagem:.1f} profissionais",
                help="Média de profissionais diurnos (Enfermagem) no período."
            )
    except Exception as e:
        with col2:
            st.error(f"Erro ao calcular Média de Enfermagem. Erro: {e}")

    # --- Indicador 3: Média de Profissionais Técnicos de Enfermagem ---
    try:
        media_tecnicos = df_filtrado['numero_tecnico_enfermagem'].mean()
        with col3:
            st.metric(
                label="Média Diária (Técnicos Enf.)",
                value=f"{media_tecnicos:.1f} profissionais",
                help="Média de profissionais diurnos (Técnico de enfermagem) no período."
            )
    except Exception as e:
        with col3:
            st.error(f"Erro ao calcular Média de Técnicos. Erro: {e}")