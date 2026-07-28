import pandas as pd
import logging

# Configurar o logging
logging.basicConfig(level=logging.INFO)

def calculate_taxa_mortalidade_uti(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Mortalidade da UTI para o mês selecionado.
    VERSÃO LIMPA (SEM DEBUG)
    """
    
    df = df_clinico_raw.copy()
    df_geral_paciente = df 
    
    # --- 1. Filtragem de Instrumento ---
    # O export list[dict] usa '' (string vazia) ou None para o instrumento base
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
        return 0.0, 0, 0 # Retorna 3 valores

    # --- 3. Preparação dos Dados ---
    try:
        # Tentar o formato PADRÃO DA API (Y-m-d) PRIMEIRO
        df_geral_paciente[coluna_data_desfecho] = pd.to_datetime(
            df_geral_paciente[coluna_data_desfecho].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
         # Tentar o formato D/M/Y do seu dicionário como fallback
        try:
            df_geral_paciente[coluna_data_desfecho] = pd.to_datetime(
                df_geral_paciente[coluna_data_desfecho].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data do desfecho: {e}. Verifique o formato.")
            return 0.0, 0, 0 # Retorna 3 valores

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
    
    # --- MUDANÇA AQUI: Retornamos apenas os 3 valores ---
    return taxa, numerador, denominador


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
    # (Igual à função anterior, para isolar os dados de admissão)
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    
    logging.info(f"Desnutrição: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    # --- 2. Definição das Colunas (Formato RAW) ---
    coluna_data_admissao = 'data_e_hora_admissao_uti'
    coluna_desnutricao = 'diagnostico_desnutricao'

    # Verificar se as colunas-chave existem
    if coluna_data_admissao not in df_geral_paciente.columns or coluna_desnutricao not in df_geral_paciente.columns:
        logging.warning("Colunas de desnutrição ou admissão não encontradas. Retornando 0.")
        return 0.0, 0, 0 

    # --- 3. Preparação dos Dados ---
    # Converter a coluna de DATA DE ADMISSÃO
    try:
        # Tentar o formato PADRÃO DA API (Y-m-d) PRIMEIRO
        df_geral_paciente[coluna_data_admissao] = pd.to_datetime(
            df_geral_paciente[coluna_data_admissao].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
         # Tentar o formato D/M/Y do seu dicionário como fallback
        try:
            df_geral_paciente[coluna_data_admissao] = pd.to_datetime(
                df_geral_paciente[coluna_data_admissao].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data de admissão: {e}. Verifique o formato.")
            return 0.0, 0, 0

    # Converter coluna de desnutrição para string
    df_geral_paciente[coluna_desnutricao] = df_geral_paciente[coluna_desnutricao].astype(str)

    # --- 4. Filtragem (Lógica de "Mês de Admissão") ---
    
    # Remover linhas onde a data de admissão é nula
    df_com_admissao = df_geral_paciente.dropna(subset=[coluna_data_admissao])
    
    # **A GRANDE DIFERENÇA**: Filtramos o dataframe pela DATA DE ADMISSÃO
    df_admitidos_no_mes = df_com_admissao[
        (df_com_admissao[coluna_data_admissao].dt.month == selected_month) &
        (df_com_admissao[coluna_data_admissao].dt.year == selected_year)
    ]

    # --- 5. Cálculos (Numerador e Denominador) ---
    
    # O Denominador são TODOS os pacientes admitidos no mês
    denominador = len(df_admitidos_no_mes)
    
    # O Numerador são apenas os desnutridos ('1') DESSE grupo
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