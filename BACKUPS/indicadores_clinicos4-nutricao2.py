import pandas as pd
import logging

# Configurar o logging
logging.basicConfig(level=logging.INFO)

# --- FUNÇÃO 1: TAXA DE MORTALIDADE ---
def calculate_taxa_mortalidade_uti(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Mortalidade da UTI para o mês selecionado.
    VERSÃO LIMPA (SEM DEBUG)
    """
    
    df = df_clinico_raw.copy()
    df_geral_paciente = df 
    
    # --- 1. Filtragem de Instrumento ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    
    logging.info(f"Filtrado para {len(df_geral_paciente)} registros do instrumento 'geral_paciente'.")

    # --- 2. Definição das Colunas (Formato RAW) ---
    coluna_data_desfecho = 'data_do_desfecho_uti'
    coluna_desfecho = 'desfecho_uti'

    if coluna_data_desfecho not in df_geral_paciente.columns or coluna_desfecho not in df_geral_paciente.columns:
        logging.warning(f"Colunas de desfecho não encontradas. Retornando 0. (Procurando por '{coluna_data_desfecho}' e '{coluna_desfecho}')")
        return 0.0, 0, 0 

    # --- 3. Preparação dos Dados ---
    try:
        df_geral_paciente[coluna_data_desfecho] = pd.to_datetime(
            df_geral_paciente[coluna_data_desfecho].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_geral_paciente[coluna_data_desfecho] = pd.to_datetime(
                df_geral_paciente[coluna_data_desfecho].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data do desfecho: {e}. Verifique o formato.")
            return 0.0, 0, 0 

    df_geral_paciente[coluna_desfecho] = df_geral_paciente[coluna_desfecho].astype(str)

    # --- 4. Filtragem (A Lógica da Médica) ---
    df_com_desfecho = df_geral_paciente.dropna(subset=[coluna_data_desfecho])
    
    df_mes_corrente = df_com_desfecho[
        (df_com_desfecho[coluna_data_desfecho].dt.month == selected_month) &
        (df_com_desfecho[coluna_data_desfecho].dt.year == selected_year)
    ]

    # --- 5. Cálculos (Numerador e Denominador) ---
    denominador = len(df_mes_corrente)
    
    is_obito_raw_1 = df_mes_corrente[coluna_desfecho].eq('2')
    is_obito_raw_2 = df_mes_corrente[coluna_desfecho].eq('2.0')
    
    numerador = (is_obito_raw_1 | is_obito_raw_2).sum()

    # --- 6. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0

    logging.info(f"Cálculo Mortalidade (Formato RAW): Taxa={taxa:.1f}%, Num={numerador}, Denom={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 2: TAXA DE DESNUTRIÇÃO ---
def calculate_taxa_desnutricao(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Desnutrição (Perfil de Admissão).
    Lógica (baseada no doc):
    - Filtro: Mês de ADMISSÃO do paciente.
    - Numerador: Nº de pacientes com diagnostico_desnutricao = 'Sim' ('1').
    - Denominador: Nº Total de admissões no mês.
    """
    
    df = df_clinico_raw.copy()
    df_geral_paciente = df 

    # --- 1. Filtragem de Instrumento ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    
    logging.info(f"Desnutrição: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    # --- 2. Definição das Colunas (Formato RAW) ---
    coluna_data_admissao = 'data_e_hora_admissao_uti'
    coluna_desnutricao = 'diagnostico_desnutricao'

    if coluna_data_admissao not in df_geral_paciente.columns or coluna_desnutricao not in df_geral_paciente.columns:
        logging.warning("Colunas de desnutrição ou admissão não encontradas. Retornando 0.")
        return 0.0, 0, 0 

    # --- 3. Preparação dos Dados ---
    try:
        df_geral_paciente[coluna_data_admissao] = pd.to_datetime(
            df_geral_paciente[coluna_data_admissao].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_geral_paciente[coluna_data_admissao] = pd.to_datetime(
                df_geral_paciente[coluna_data_admissao].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data de admissão: {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_geral_paciente[coluna_desnutricao] = df_geral_paciente[coluna_desnutricao].astype(str)

    # --- 4. Filtragem (Lógica de "Mês de Admissão") ---
    df_com_admissao = df_geral_paciente.dropna(subset=[coluna_data_admissao])
    
    df_admitidos_no_mes = df_com_admissao[
        (df_com_admissao[coluna_data_admissao].dt.month == selected_month) &
        (df_com_admissao[coluna_data_admissao].dt.year == selected_year)
    ]

    # --- 5. Cálculos (Numerador e Denominador) ---
    denominador = len(df_admitidos_no_mes)
    
    is_desnutrido_raw_1 = df_admitidos_no_mes[coluna_desnutricao].eq('1')
    is_desnutrido_raw_2 = df_admitidos_no_mes[coluna_desnutricao].eq('1.0')
    
    numerador = (is_desnutrido_raw_1 | is_desnutrido_raw_2).sum()

    # --- 6. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0

    logging.info(f"Cálculo Desnutrição (Admissão): Taxa={taxa:.1f}%, Num={numerador}, Denom={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 3: RELAÇÃO DIETA ---
def calculate_relacao_dieta(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Relação Prescrito vs. Infundido (Operacional).
    Lógica (baseada no doc):
    - Filtro: Mês Corrente (baseado no 'data_diario' do formulário repetível).
    - Numerador: SOMA 'volume_infundido_ml' no mês.
    - Denominador: SOMA 'volume_prescrito' no mês.
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Filtragem de Instrumento ---
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Relação Dieta.")
        return 0.0, 0, 0
    
    logging.info(f"Relação Dieta: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    # --- 2. Definição das Colunas (Formato RAW) ---
    coluna_data_diario = 'data_diario'
    coluna_prescrito = 'volume_prescrito'
    coluna_infundido = 'volume_infundido_ml'

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_prescrito, coluna_infundido]):
        logging.warning("Colunas de dieta ('data_diario', 'volume_prescrito', 'volume_infundido_ml') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    # --- 3. Preparação dos Dados ---
    df_diario_preparado = df_diario.copy()
    
    # Converter a coluna de DATA DIÁRIO
    try:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_diario_preparado[coluna_data_diario] = pd.to_datetime(
                df_diario_preparado[coluna_data_diario].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data_diario: {e}. Verifique o formato.")
            return 0.0, 0, 0

    # Converter colunas de volume para numérico
    df_diario_preparado[coluna_prescrito] = pd.to_numeric(df_diario_preparado[coluna_prescrito], errors='coerce')
    df_diario_preparado[coluna_infundido] = pd.to_numeric(df_diario_preparado[coluna_infundido], errors='coerce')

    # --- 4. Filtragem (Lógica de "Mês Corrente" no formulário diário) ---
    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]

    # --- 5. Cálculos (Numerador e Denominador) ---
    denominador = df_diario_mes[coluna_prescrito].sum()
    numerador = df_diario_mes[coluna_infundido].sum()

    # --- 6. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Relação Dieta (Diário): Taxa={taxa:.1f}%, Num (Infundido)={numerador}, Denom (Prescrito)={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 4: TEMPO ATÉ A META (A NOVA) ---
def calculate_tempo_ate_meta(df_clinico_raw, selected_month, selected_year):
    """
    Calcula o Tempo Médio em dias até a meta nutricional.
    Lógica (baseada no doc):
    - Filtro: Mês de ADMISSÃO do paciente.
    - Numerador: SOMA dos dias (admissão -> 1º 'Sim' em 'esta_na_meta') para cada paciente.
    - Denominador: Nº Total de admissões no mês.
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Preparar Dados de Admissão (para a Coorte) ---
    df_geral_paciente = df.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    
    col_data_admissao = 'data_e_hora_admissao_uti'
    if col_data_admissao not in df_geral_paciente.columns:
        logging.warning("Coluna 'data_e_hora_admissao_uti' não encontrada. Não é possível calcular Tempo Meta.")
        return 0.0, 0, 0

    # Converter data de admissão
    try:
        df_geral_paciente[col_data_admissao] = pd.to_datetime(
            df_geral_paciente[col_data_admissao].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        try:
            df_geral_paciente[col_data_admissao] = pd.to_datetime(
                df_geral_paciente[col_data_admissao].str.strip(), format='%d/%m/%Y', errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data de admissão: {e}.")
            return 0.0, 0, 0

    # --- 2. Identificar a Coorte (Denominador) ---
    df_com_admissao = df_geral_paciente.dropna(subset=[col_data_admissao])
    df_admitidos_no_mes = df_com_admissao[
        (df_com_admissao[col_data_admissao].dt.month == selected_month) &
        (df_com_admissao[col_data_admissao].dt.year == selected_year)
    ]
    
    denominador = len(df_admitidos_no_mes)
    if denominador == 0:
        logging.info("Tempo Meta: Nenhum paciente admitido no mês. Retornando 0.")
        return 0.0, 0, 0 

    df_cohort = df_admitidos_no_mes[['record_id', col_data_admissao]].copy()

    # --- 3. Preparar Dados Diários (para o Numerador) ---
    df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    col_data_diario = 'data_diario'
    col_meta = 'esta_na_meta'
    
    if col_data_diario not in df_diario.columns or col_meta not in df_diario.columns:
        logging.warning("Colunas 'data_diario' ou 'esta_na_meta' não encontradas. Retornando 0.")
        return 0.0, 0, denominador 

    # Converter data diária
    try:
        df_diario[col_data_diario] = pd.to_datetime(df_diario[col_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce')
    except Exception:
        df_diario[col_data_diario] = pd.to_datetime(df_diario[col_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce')

    df_diario[col_meta] = df_diario[col_meta].astype(str).str.replace(r'\.0$', '', regex=True) 
    
    # --- 4. Encontrar a Primeira Data da Meta para cada paciente ---
    df_dias_meta_sim = df_diario[df_diario[col_meta] == '1'].dropna(subset=[col_data_diario])
    
    df_primeira_meta = df_dias_meta_sim.groupby('record_id')[col_data_diario].min().reset_index()
    df_primeira_meta.rename(columns={col_data_diario: 'data_primeira_meta'}, inplace=True)

    # --- 5. Calcular o Numerador ---
    df_merged = pd.merge(df_cohort, df_primeira_meta, on='record_id', how='left')
    
    df_merged['dias_ate_meta'] = (df_merged['data_primeira_meta'] - df_merged[col_data_admissao]).dt.days
    
    df_merged.loc[df_merged['dias_ate_meta'] < 0, 'dias_ate_meta'] = 0
    
    numerador = df_merged['dias_ate_meta'].fillna(0).sum()
    
    # --- 6. Resultado (Média) ---
    if denominador > 0:
        media_dias = numerador / denominador
    else:
        media_dias = 0.0

    logging.info(f"Cálculo Tempo Meta (Admissão): Média={media_dias:.1f} dias, Num (Total Dias)={numerador}, Denom (Pacientes)={denominador}")
    
    return media_dias, numerador, denominador