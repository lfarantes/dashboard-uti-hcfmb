import pandas as pd
import logging
import numpy as np

# Configurar o logging
logging.basicConfig(level=logging.INFO)

# --- FUNÇÃO 1: TAXA DE MORTALIDADE ---
def calculate_taxa_mortalidade_uti(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Mortalidade da UTI para o mês selecionado.
    """
    
    df = df_clinico_raw.copy()
    df_geral_paciente = df 
    
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    
    logging.info(f"Filtrado para {len(df_geral_paciente)} registros do instrumento 'geral_paciente'.")

    coluna_data_desfecho = 'data_do_desfecho_uti'
    coluna_desfecho = 'desfecho_uti'

    if coluna_data_desfecho not in df_geral_paciente.columns or coluna_desfecho not in df_geral_paciente.columns:
        logging.warning(f"Colunas de desfecho não encontradas. Retornando 0. (Procurando por '{coluna_data_desfecho}' e '{coluna_desfecho}')")
        return 0.0, 0, 0 

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

    df_com_desfecho = df_geral_paciente.dropna(subset=[coluna_data_desfecho])
    
    df_mes_corrente = df_com_desfecho[
        (df_com_desfecho[coluna_data_desfecho].dt.month == selected_month) &
        (df_com_desfecho[coluna_data_desfecho].dt.year == selected_year)
    ]

    denominador = len(df_mes_corrente)
    
    is_obito_raw_1 = df_mes_corrente[coluna_desfecho].eq('2')
    is_obito_raw_2 = df_mes_corrente[coluna_desfecho].eq('2.0')
    
    numerador = (is_obito_raw_1 | is_obito_raw_2).sum()

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
    """
    
    df = df_clinico_raw.copy()
    df_geral_paciente = df 

    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    
    logging.info(f"Desnutrição: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    coluna_data_admissao = 'data_e_hora_admissao_uti'
    coluna_desnutricao = 'diagnostico_desnutricao'

    if coluna_data_admissao not in df_geral_paciente.columns or coluna_desnutricao not in df_geral_paciente.columns:
        logging.warning("Colunas de desnutrição ou admissão não encontradas. Retornando 0.")
        return 0.0, 0, 0 

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

    df_com_admissao = df_geral_paciente.dropna(subset=[coluna_data_admissao])
    
    df_admitidos_no_mes = df_com_admissao[
        (df_com_admissao[coluna_data_admissao].dt.month == selected_month) &
        (df_com_admissao[coluna_data_admissao].dt.year == selected_year)
    ]

    denominador = len(df_admitidos_no_mes)
    
    is_desnutrido_raw_1 = df_admitidos_no_mes[coluna_desnutricao].eq('1')
    is_desnutrido_raw_2 = df_admitidos_no_mes[coluna_desnutricao].eq('1.0')
    
    numerador = (is_desnutrido_raw_1 | is_desnutrido_raw_2).sum()

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
    """
    
    df = df_clinico_raw.copy()
    
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Relação Dieta.")
        return 0.0, 0, 0
    
    logging.info(f"Relação Dieta: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    coluna_data_diario = 'data_diario'
    coluna_prescrito = 'volume_prescrito'
    coluna_infundido = 'volume_infundido_ml'

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_prescrito, coluna_infundido]):
        logging.warning("Colunas de dieta ('data_diario', 'volume_prescrito', 'volume_infundido_ml') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    
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

    df_diario_preparado[coluna_prescrito] = pd.to_numeric(df_diario_preparado[coluna_prescrito], errors='coerce')
    df_diario_preparado[coluna_infundido] = pd.to_numeric(df_diario_preparado[coluna_infundido], errors='coerce')

    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]

    denominador = df_diario_mes[coluna_prescrito].sum()
    numerador = df_diario_mes[coluna_infundido].sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Relação Dieta (Diário): Taxa={taxa:.1f}%, Num (Infundido)={numerador}, Denom (Prescrito)={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 4: TEMPO ATÉ A META ---
def calculate_tempo_ate_meta(df_clinico_raw, selected_month, selected_year):
    """
    Calcula o Tempo Médio em dias até a meta nutricional.
    """
    
    df = df_clinico_raw.copy()
    
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

    df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    col_data_diario = 'data_diario'
    col_meta = 'esta_na_meta'
    
    if col_data_diario not in df_diario.columns or col_meta not in df_diario.columns:
        logging.warning("Colunas 'data_diario' ou 'esta_na_meta' não encontradas. Retornando 0.")
        return 0.0, 0, denominador 

    try:
        df_diario[col_data_diario] = pd.to_datetime(df_diario[col_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce')
    except Exception:
        df_diario[col_data_diario] = pd.to_datetime(df_diario[col_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce')

    df_diario[col_meta] = df_diario[col_meta].astype(str).str.replace(r'\.0$', '', regex=True) 
    
    df_dias_meta_sim = df_diario[df_diario[col_meta] == '1'].dropna(subset=[col_data_diario])
    
    df_primeira_meta = df_dias_meta_sim.groupby('record_id')[col_data_diario].min().reset_index()
    df_primeira_meta.rename(columns={col_data_diario: 'data_primeira_meta'}, inplace=True)

    df_merged = pd.merge(df_cohort, df_primeira_meta, on='record_id', how='left')
    
    df_merged['dias_ate_meta'] = (df_merged['data_primeira_meta'] - df_merged[col_data_admissao]).dt.days
    
    df_merged.loc[df_merged['dias_ate_meta'] < 0, 'dias_ate_meta'] = 0
    
    numerador = df_merged['dias_ate_meta'].fillna(0).sum()
    
    if denominador > 0:
        media_dias = numerador / denominador
    else:
        media_dias = 0.0

    logging.info(f"Cálculo Tempo Meta (Admissão): Média={media_dias:.1f} dias, Num (Total Dias)={numerador}, Denom (Pacientes)={denominador}")
    
    return media_dias, numerador, denominador


# --- FUNÇÃO 5: TEMPO MÉDIO DE VM ---
def calculate_tempo_medio_vm(df_clinico_raw, selected_month, selected_year):
    """
    Calcula o Tempo Médio de Ventilação Mecânica (Operacional).
    """
    
    df = df_clinico_raw.copy()
    
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Tempo VM.")
        return 0.0, 0, 0
    
    logging.info(f"Tempo VM: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    coluna_data_diario = 'data_diario'
    coluna_vm = 'suporte_vm_ultimas_24h'
    coluna_paciente = 'record_id' 

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_vm, coluna_paciente]):
        logging.warning("Colunas de VM ('data_diario', 'suporte_vm_ultimas_24h', 'record_id') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    
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
            logging.error(f"Erro ao converter data_diario (VM): {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_diario_preparado[coluna_vm] = df_diario_preparado[coluna_vm].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]

    df_dias_em_vm = df_diario_mes[df_diario_mes[coluna_vm] == '1']
    
    numerador = len(df_dias_em_vm)
    denominador = df_dias_em_vm[coluna_paciente].nunique()

    if denominador > 0:
        media_dias = numerador / denominador
    else:
        media_dias = 0.0 

    logging.info(f"Cálculo Tempo Médio VM (Diário): Média={media_dias:.1f} dias, Num (Dias VM)={numerador}, Denom (Pacientes Únicos)={denominador}")
    
    return media_dias, numerador, denominador


# --- FUNÇÃO 6: TAXA UTILIZAÇÃO VM ---
def calculate_taxa_utilizacao_vm(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Utilização de VM (Operacional).
    """
    
    df = df_clinico_raw.copy()
    
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Taxa VM.")
        return 0.0, 0, 0
    
    logging.info(f"Taxa VM: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    coluna_data_diario = 'data_diario'
    coluna_vm = 'suporte_vm_ultimas_24h'
    coluna_leito = 'paciente_ocupando_leito'

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_vm, coluna_leito]):
        logging.warning("Colunas de Taxa VM ('data_diario', 'suporte_vm_ultimas_24h', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    
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
            logging.error(f"Erro ao converter data_diario (Taxa VM): {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_diario_preparado[coluna_vm] = df_diario_preparado[coluna_vm].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]
    
    numerador = (df_diario_mes[coluna_vm] == '1').sum()
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Taxa Utilização VM (Diário): Taxa={taxa:.1f}%, Num (VM-Dias)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 7: PROPORÇÃO EOT PALIATIVA ---
def calculate_taxa_eot_paliativa(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Proporção de EOT Paliativa (Evento Principal).
    """
    
    df = df_clinico_raw.copy()
    
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    logging.info(f"EOT Paliativa: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    coluna_data_eot = 'eot' 
    coluna_eot_sim_nao = 'eot_sim_nao' 
    coluna_eot_paliativa = 'eot_paliativa' 

    if any(col not in df_geral_paciente.columns for col in [coluna_data_eot, coluna_eot_sim_nao, coluna_eot_paliativa]):
        logging.warning("Colunas de EOT ('eot', 'eot_sim_nao', 'eot_paliativa') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_preparado = df_geral_paciente.copy()
    
    try:
        df_preparado[coluna_data_eot] = pd.to_datetime(
            df_preparado[coluna_data_eot].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_preparado[coluna_data_eot] = pd.to_datetime(
                df_preparado[coluna_data_eot].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data 'eot': {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_preparado[coluna_eot_sim_nao] = df_preparado[coluna_eot_sim_nao].astype(str).str.replace(r'\.0$', '', regex=True)
    df_preparado[coluna_eot_paliativa] = df_preparado[coluna_eot_paliativa].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_preparado.dropna(subset=[coluna_data_eot])
    
    df_eventos_mes = df_com_data[
        (df_com_data[coluna_data_eot].dt.month == selected_month) &
        (df_com_data[coluna_data_eot].dt.year == selected_year)
    ]

    denominador = (df_eventos_mes[coluna_eot_sim_nao] == '1').sum()
    numerador = (df_eventos_mes[coluna_eot_paliativa] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo EOT Paliativa (Evento): Taxa={taxa:.1f}%, Num (Paliativas)={numerador}, Denom (Total EOTs)={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 8: TAXA EOT ACIDENTAL ---
def calculate_taxa_eot_acidental(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de EOT Acidental (Evento Principal).
    """
    
    df = df_clinico_raw.copy()
    
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    logging.info(f"EOT Acidental: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    coluna_data_eot = 'eot' 
    coluna_eot_sim_nao = 'eot_sim_nao' 
    coluna_eot_acidental = 'eot_acidental' 

    if any(col not in df_geral_paciente.columns for col in [coluna_data_eot, coluna_eot_sim_nao, coluna_eot_acidental]):
        logging.warning("Colunas de EOT ('eot', 'eot_sim_nao', 'eot_acidental') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_preparado = df_geral_paciente.copy()
    
    try:
        df_preparado[coluna_data_eot] = pd.to_datetime(
            df_preparado[coluna_data_eot].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_preparado[coluna_data_eot] = pd.to_datetime(
                df_preparado[coluna_data_eot].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data 'eot': {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_preparado[coluna_eot_sim_nao] = df_preparado[coluna_eot_sim_nao].astype(str).str.replace(r'\.0$', '', regex=True)
    df_preparado[coluna_eot_acidental] = df_preparado[coluna_eot_acidental].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_preparado.dropna(subset=[coluna_data_eot])
    
    df_eventos_mes = df_com_data[
        (df_com_data[coluna_data_eot].dt.month == selected_month) &
        (df_com_data[coluna_data_eot].dt.year == selected_year)
    ]

    denominador = (df_eventos_mes[coluna_eot_sim_nao] == '1').sum()
    numerador = (df_eventos_mes[coluna_eot_acidental] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo EOT Acidental (Evento): Taxa={taxa:.1f}%, Num (Acidentais)={numerador}, Denom (Total EOTs)={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 9: TAXA RE-IOT 48H ---
def calculate_taxa_re_iot(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Re-IOT 48h (Evento Principal).
    """
    
    df = df_clinico_raw.copy()
    
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    logging.info(f"Re-IOT: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    coluna_data_eot = 'eot' 
    coluna_eot_sim_nao = 'eot_sim_nao' 
    coluna_eot_acidental = 'eot_acidental' 
    coluna_re_iot = 're_iot_sim_nao' 

    if any(col not in df_geral_paciente.columns for col in [coluna_data_eot, coluna_eot_sim_nao, coluna_eot_acidental, coluna_re_iot]):
        logging.warning("Colunas de Re-IOT ('eot', 'eot_sim_nao', 'eot_acidental', 're_iot_sim_nao') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_preparado = df_geral_paciente.copy()
    
    try:
        df_preparado[coluna_data_eot] = pd.to_datetime(
            df_preparado[coluna_data_eot].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_preparado[coluna_data_eot] = pd.to_datetime(
                df_preparado[coluna_data_eot].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data 'eot' (Re-IOT): {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_preparado[coluna_eot_sim_nao] = df_preparado[coluna_eot_sim_nao].astype(str).str.replace(r'\.0$', '', regex=True)
    df_preparado[coluna_eot_acidental] = df_preparado[coluna_eot_acidental].astype(str).str.replace(r'\.0$', '', regex=True)
    df_preparado[coluna_re_iot] = df_preparado[coluna_re_iot].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_preparado.dropna(subset=[coluna_data_eot])
    
    df_eventos_mes = df_com_data[
        (df_com_data[coluna_data_eot].dt.month == selected_month) &
        (df_com_data[coluna_data_eot].dt.year == selected_year)
    ]

    numerador = (df_eventos_mes[coluna_re_iot] == '1').sum()
    
    total_eots = (df_eventos_mes[coluna_eot_sim_nao] == '1').sum()
    eots_acidentais = (df_eventos_mes[coluna_eot_acidental] == '1').sum()
    denominador = total_eots - eots_acidentais

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Re-IOT (Evento): Taxa={taxa:.1f}%, Num (Re-IOTs)={numerador}, Denom (EOTs Planejadas)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 10: TAXA UTILIZAÇÃO CVC ---
def calculate_taxa_utilizacao_cvc(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Utilização de CVC (Operacional).
    """
    
    df = df_clinico_raw.copy()
    
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Taxa CVC.")
        return 0.0, 0, 0
    
    logging.info(f"Taxa CVC: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    coluna_data_diario = 'data_diario'
    coluna_cvc = 'uso_cvc_nas_ultimas_24h' 
    coluna_leito = 'paciente_ocupando_leito' 

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_cvc, coluna_leito]):
        logging.warning("Colunas de Taxa CVC ('data_diario', 'uso_cvc_nas_ultimas_24h', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    
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
            logging.error(f"Erro ao converter data_diario (Taxa CVC): {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_diario_preparado[coluna_cvc] = df_diario_preparado[coluna_cvc].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]
    
    numerador = (df_diario_mes[coluna_cvc] == '1').sum()
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Taxa Utilização CVC (Diário): Taxa={taxa:.1f}%, Num (CVC-Dias)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 11: TAXA UTILIZAÇÃO SVD ---
def calculate_taxa_utilizacao_svd(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Utilização de SVD (Operacional).
    """
    
    df = df_clinico_raw.copy()
    
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Taxa SVD.")
        return 0.0, 0, 0
    
    logging.info(f"Taxa SVD: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    coluna_data_diario = 'data_diario'
    coluna_svd = 'uso_de_svd_nas_ultimas_24h' 
    coluna_leito = 'paciente_ocupando_leito' 

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_svd, coluna_leito]):
        logging.warning("Colunas de Taxa SVD ('data_diario', 'uso_de_svd_nas_ultimas_24h', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    
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
            logging.error(f"Erro ao converter data_diario (Taxa SVD): {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_diario_preparado[coluna_svd] = df_diario_preparado[coluna_svd].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]
    
    numerador = (df_diario_mes[coluna_svd] == '1').sum()
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Taxa Utilização SVD (Diário): Taxa={taxa:.1f}%, Num (SVD-Dias)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 12: TAXA UTILIZAÇÃO DIALISE ---
def calculate_taxa_utilizacao_dialise(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Utilização de Diálise (Operacional).
    """
    
    df = df_clinico_raw.copy()
    
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Taxa Diálise.")
        return 0.0, 0, 0
    
    logging.info(f"Taxa Diálise: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    coluna_data_diario = 'data_diario'
    coluna_dialise = 'di_lise_nas_ultimas_24h' 
    coluna_leito = 'paciente_ocupando_leito' 

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_dialise, coluna_leito]):
        logging.warning("Colunas de Taxa Diálise ('data_diario', 'di_lise_nas_ultimas_24h', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    
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
            logging.error(f"Erro ao converter data_diario (Taxa Diálise): {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_diario_preparado[coluna_dialise] = df_diario_preparado[coluna_dialise].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]
    
    numerador = (df_diario_mes[coluna_dialise] == '1').sum()
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Taxa Utilização Diálise (Diário): Taxa={taxa:.1f}%, Num (Diálise-Dias)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 13: TAXA UTILIZAÇÃO DVA ---
def calculate_taxa_utilizacao_dva(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Utilização de DVA (Operacional).
    """
    
    df = df_clinico_raw.copy()
    
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Taxa DVA.")
        return 0.0, 0, 0
    
    logging.info(f"Taxa DVA: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    coluna_data_diario = 'data_diario'
    coluna_dva = 'dva_nas_ultimas_24h' 
    coluna_leito = 'paciente_ocupando_leito' 

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_dva, coluna_leito]):
        logging.warning("Colunas de Taxa DVA ('data_diario', 'dva_nas_ultimas_24h', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    
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
            logging.error(f"Erro ao converter data_diario (Taxa DVA): {e}. Verifique o formato.")
            return 0.0, 0, 0

    df_diario_preparado[coluna_dva] = df_diario_preparado[coluna_dva].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]
    
    numerador = (df_diario_mes[coluna_dva] == '1').sum()
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Taxa Utilização DVA (Diário): Taxa={taxa:.1f}%, Num (DVA-Dias)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 14: TAXA INCIDÊNCIA LPP ---
def calculate_taxa_incidencia_lpp(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Incidência de Lesão por Pressão (Híbrido).
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Cálculo do Denominador (Paciente-Dias) ---
    instrumento_diario = 'diario_paciente'
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Denom LPP.")
        return 0.0, 0, 0
        
    coluna_data_diario = 'data_diario'
    coluna_leito = 'paciente_ocupando_leito'

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_leito]):
        logging.warning("Colunas do Denominador LPP ('data_diario', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    try:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)
    df_com_data_diario = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data_diario[
        (df_com_data_diario[coluna_data_diario].dt.month == selected_month) &
        (df_com_data_diario[coluna_data_diario].dt.year == selected_year)
    ]
    
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    # --- 2. Cálculo do Numerador (Eventos LPP) ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    coluna_data_lpp = 'lesao_pressao_data'
    coluna_lpp_sim_nao = 'teve_lesao_por_pressao'
    
    if any(col not in df_geral_paciente.columns for col in [coluna_data_lpp, coluna_lpp_sim_nao]):
        logging.warning("Colunas de LPP ('lesao_pressao_data', 'teve_lesao_por_pressao') não encontradas. Retornando 0.")
        return 0.0, 0, denominador 

    df_lpp_preparado = df_geral_paciente.copy()

    try:
        df_lpp_preparado[coluna_data_lpp] = pd.to_datetime(
            df_lpp_preparado[coluna_data_lpp].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_lpp_preparado[coluna_data_lpp] = pd.to_datetime(
            df_lpp_preparado[coluna_data_lpp].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_lpp_preparado[coluna_lpp_sim_nao] = df_lpp_preparado[coluna_lpp_sim_nao].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data_lpp = df_lpp_preparado.dropna(subset=[coluna_data_lpp])
    
    df_lpp_eventos_mes = df_com_data_lpp[
        (df_com_data_lpp[coluna_data_lpp].dt.month == selected_month) &
        (df_com_data_lpp[coluna_data_lpp].dt.year == selected_year)
    ]
    
    numerador = (df_lpp_eventos_mes[coluna_lpp_sim_nao] == '1').sum()

    # --- 3. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Taxa Incidência LPP (Híbrido): Taxa={taxa:.1f}%, Num (Eventos LPP)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 15: TAXA INCIDÊNCIA FLEBITE ---
def calculate_taxa_incidencia_flebite(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Incidência de Flebite (Híbrido).
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Cálculo do Denominador (Paciente-Dias) ---
    instrumento_diario = 'diario_paciente'
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Denom Flebite.")
        return 0.0, 0, 0
        
    coluna_data_diario = 'data_diario'
    coluna_leito = 'paciente_ocupando_leito'

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_leito]):
        logging.warning("Colunas do Denom Flebite ('data_diario', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    try:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)
    df_com_data_diario = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data_diario[
        (df_com_data_diario[coluna_data_diario].dt.month == selected_month) &
        (df_com_data_diario[coluna_data_diario].dt.year == selected_year)
    ]
    
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    # --- 2. Cálculo do Numerador (Eventos Flebite) ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    coluna_data_flebite = 'flebite_data'
    coluna_flebite_sim_nao = 'teve_flebite'
    
    if any(col not in df_geral_paciente.columns for col in [coluna_data_flebite, coluna_flebite_sim_nao]):
        logging.warning("Colunas de Flebite ('flebite_data', 'teve_flebite') não encontradas. Retornando 0.")
        return 0.0, 0, denominador 

    df_flebite_preparado = df_geral_paciente.copy()

    try:
        df_flebite_preparado[coluna_data_flebite] = pd.to_datetime(
            df_flebite_preparado[coluna_data_flebite].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_flebite_preparado[coluna_data_flebite] = pd.to_datetime(
            df_flebite_preparado[coluna_data_flebite].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_flebite_preparado[coluna_flebite_sim_nao] = df_flebite_preparado[coluna_flebite_sim_nao].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_data_flebite = df_flebite_preparado.dropna(subset=[coluna_data_flebite])
    
    df_flebite_eventos_mes = df_com_data_flebite[
        (df_com_data_flebite[coluna_data_flebite].dt.month == selected_month) &
        (df_com_data_flebite[coluna_data_flebite].dt.year == selected_year)
    ]
    
    numerador = (df_flebite_eventos_mes[coluna_flebite_sim_nao] == '1').sum()

    # --- 3. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Taxa Incidência Flebite (Híbrido): Taxa={taxa:.1f}%, Num (Eventos Flebite)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 16: DENSIDADE INFECÇÃO CVC ---
def calculate_densidade_infeccao_cvc(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Densidade de Incidência de Infecção por CVC (Híbrido).
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Cálculo do Denominador (CVC-Dias) ---
    instrumento_diario = 'diario_paciente'
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Denom Infecção CVC.")
        return 0.0, 0, 0
        
    coluna_data_diario = 'data_diario'
    coluna_cvc = 'uso_cvc_nas_ultimas_24h'
    
    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_cvc]):
        logging.warning("Colunas do Denom Infecção CVC ('data_diario', 'uso_cvc_nas_ultimas_24h') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    try:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_diario_preparado[coluna_cvc] = df_diario_preparado[coluna_cvc].astype(str).str.replace(r'\.0$', '', regex=True)
    df_com_data_diario = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data_diario[
        (df_com_data_diario[coluna_data_diario].dt.month == selected_month) &
        (df_com_data_diario[coluna_data_diario].dt.year == selected_year)
    ]
    
    denominador = (df_diario_mes[coluna_cvc] == '1').sum() # Total CVC-dias

    # --- 2. Cálculo do Numerador (Eventos de Infecção) ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    coluna_data_infeccao = 'infeccoes_durante_uti_data' 
    coluna_ics_numero = 'ics_numero' 
    
    if any(col not in df_geral_paciente.columns for col in [coluna_data_infeccao, coluna_ics_numero]):
        logging.warning("Colunas de Infecção CVC ('infeccoes_durante_uti_data', 'ics_numero') não encontradas. Retornando 0.")
        return 0.0, 0, denominador

    df_infeccao_preparado = df_geral_paciente.copy()

    try:
        df_infeccao_preparado[coluna_data_infeccao] = pd.to_datetime(
            df_infeccao_preparado[coluna_data_infeccao].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_infeccao_preparado[coluna_data_infeccao] = pd.to_datetime(
            df_infeccao_preparado[coluna_data_infeccao].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_infeccao_preparado[coluna_ics_numero] = pd.to_numeric(df_infeccao_preparado[coluna_ics_numero], errors='coerce')

    df_com_data_infeccao = df_infeccao_preparado.dropna(subset=[coluna_data_infeccao])
    
    df_infeccao_eventos_mes = df_com_data_infeccao[
        (df_com_data_infeccao[coluna_data_infeccao].dt.month == selected_month) &
        (df_com_data_infeccao[coluna_data_infeccao].dt.year == selected_year)
    ]
    
    numerador = df_infeccao_eventos_mes[coluna_ics_numero].sum()

    # --- 3. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 1000
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Densidade Infecção CVC (Híbrido): Taxa={taxa:.1f} (x1000), Num (Infecções CVC)={numerador}, Denom (CVC-Dias)={denominador}")
    
    return taxa, numerador, denominador


# --- FUNÇÃO 17: DENSIDADE INFECÇÃO PAV ---
def calculate_densidade_infeccao_pav(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Densidade de Incidência de PAV (Híbrido).
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Cálculo do Denominador (VM-Dias) ---
    instrumento_diario = 'diario_paciente'
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Denom PAV.")
        return 0.0, 0, 0
        
    coluna_data_diario = 'data_diario'
    coluna_vm = 'suporte_vm_ultimas_24h' # <-- Denominador
    
    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_vm]):
        logging.warning("Colunas do Denom PAV ('data_diario', 'suporte_vm_ultimas_24h') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    try:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_diario_preparado[coluna_vm] = df_diario_preparado[coluna_vm].astype(str).str.replace(r'\.0$', '', regex=True)
    df_com_data_diario = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data_diario[
        (df_com_data_diario[coluna_data_diario].dt.month == selected_month) &
        (df_com_data_diario[coluna_data_diario].dt.year == selected_year)
    ]
    
    denominador = (df_diario_mes[coluna_vm] == '1').sum() # Total VM-dias

    # --- 2. Cálculo do Numerador (Eventos de Infecção) ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    coluna_data_infeccao = 'infeccoes_durante_uti_data' 
    coluna_pav_numero = 'pavm_numero' # <-- Numerador
    
    if any(col not in df_geral_paciente.columns for col in [coluna_data_infeccao, coluna_pav_numero]):
        logging.warning("Colunas de Infecção PAV ('infeccoes_durante_uti_data', 'pavm_numero') não encontradas. Retornando 0.")
        return 0.0, 0, denominador

    df_infeccao_preparado = df_geral_paciente.copy()

    try:
        df_infeccao_preparado[coluna_data_infeccao] = pd.to_datetime(
            df_infeccao_preparado[coluna_data_infeccao].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_infeccao_preparado[coluna_data_infeccao] = pd.to_datetime(
            df_infeccao_preparado[coluna_data_infeccao].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_infeccao_preparado[coluna_pav_numero] = pd.to_numeric(df_infeccao_preparado[coluna_pav_numero], errors='coerce')

    df_com_data_infeccao = df_infeccao_preparado.dropna(subset=[coluna_data_infeccao])
    
    df_infeccao_eventos_mes = df_com_data_infeccao[
        (df_com_data_infeccao[coluna_data_infeccao].dt.month == selected_month) &
        (df_com_data_infeccao[coluna_data_infeccao].dt.year == selected_year)
    ]
    
    numerador = df_infeccao_eventos_mes[coluna_pav_numero].sum()

    # --- 3. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 1000
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Densidade Infecção PAV (Híbrido): Taxa={taxa:.1f} (x1000), Num (Infecções PAV)={numerador}, Denom (VM-Dias)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 18: DENSIDADE INFECÇÃO ITU ---
def calculate_densidade_infeccao_itu(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Densidade de Incidência de ITU (Híbrido).
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Cálculo do Denominador (SVD-Dias) ---
    instrumento_diario = 'diario_paciente'
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Denom ITU.")
        return 0.0, 0, 0
        
    coluna_data_diario = 'data_diario'
    coluna_svd = 'uso_de_svd_nas_ultimas_24h' # <-- Denominador
    
    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_svd]):
        logging.warning("Colunas do Denom ITU ('data_diario', 'uso_de_svd_nas_ultimas_24h') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    try:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_diario_preparado[coluna_svd] = df_diario_preparado[coluna_svd].astype(str).str.replace(r'\.0$', '', regex=True)
    df_com_data_diario = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data_diario[
        (df_com_data_diario[coluna_data_diario].dt.month == selected_month) &
        (df_com_data_diario[coluna_data_diario].dt.year == selected_year)
    ]
    
    denominador = (df_diario_mes[coluna_svd] == '1').sum() # Total SVD-dias

    # --- 2. Cálculo do Numerador (Eventos de Infecção) ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    coluna_data_infeccao = 'infeccoes_durante_uti_data' 
    coluna_itu_numero = 'itu_numero' # <-- Numerador
    
    if any(col not in df_geral_paciente.columns for col in [coluna_data_infeccao, coluna_itu_numero]):
        logging.warning("Colunas de Infecção ITU ('infeccoes_durante_uti_data', 'itu_numero') não encontradas. Retornando 0.")
        return 0.0, 0, denominador

    df_infeccao_preparado = df_geral_paciente.copy()

    try:
        df_infeccao_preparado[coluna_data_infeccao] = pd.to_datetime(
            df_infeccao_preparado[coluna_data_infeccao].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_infeccao_preparado[coluna_data_infeccao] = pd.to_datetime(
            df_infeccao_preparado[coluna_data_infeccao].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_infeccao_preparado[coluna_itu_numero] = pd.to_numeric(df_infeccao_preparado[coluna_itu_numero], errors='coerce')

    df_com_data_infeccao = df_infeccao_preparado.dropna(subset=[coluna_data_infeccao])
    
    df_infeccao_eventos_mes = df_com_data_infeccao[
        (df_com_data_infeccao[coluna_data_infeccao].dt.month == selected_month) &
        (df_com_data_infeccao[coluna_data_infeccao].dt.year == selected_year)
    ]
    
    numerador = df_infeccao_eventos_mes[coluna_itu_numero].sum()

    # --- 3. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 1000
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Densidade Infecção ITU (Híbrido): Taxa={taxa:.1f} (x1000), Num (Infecções ITU)={numerador}, Denom (SVD-Dias)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 19: DIÁRIAS EVITÁVEIS ---
def calculate_diarias_evitaveis(df_clinico_raw, selected_month, selected_year):
    """
    Calcula as Diárias Evitáveis (Híbrido).
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Cálculo do Denominador (Paciente-Dias) ---
    instrumento_diario = 'diario_paciente'
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Denom Diárias Evitáveis.")
        return 0.0, 0, 0
        
    coluna_data_diario = 'data_diario'
    coluna_leito = 'paciente_ocupando_leito'

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_leito]):
        logging.warning("Colunas do Denom Diárias Evitáveis ('data_diario', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    try:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)
    df_com_data_diario = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data_diario[
        (df_com_data_diario[coluna_data_diario].dt.month == selected_month) &
        (df_com_data_diario[coluna_data_diario].dt.year == selected_year)
    ]
    
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    # --- 2. Cálculo do Numerador (Soma de Dias Evitáveis) ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    col_data_solicitacao = 'data_solicitacao_alta'
    col_data_desfecho = 'data_do_desfecho_uti'
    col_desfecho = 'desfecho_uti'
    
    cols_necessarias = [col_data_solicitacao, col_data_desfecho, col_desfecho]
    if any(col not in df_geral_paciente.columns for col in cols_necessarias):
        logging.warning(f"Colunas de Diárias Evitáveis ({cols_necessarias}) não encontradas. Retornando 0.")
        return 0.0, 0, denominador

    df_evitaveis_preparado = df_geral_paciente.copy()

    try:
        df_evitaveis_preparado[col_data_solicitacao] = pd.to_datetime(
            df_evitaveis_preparado[col_data_solicitacao].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
        df_evitaveis_preparado[col_data_desfecho] = pd.to_datetime(
            df_evitaveis_preparado[col_data_desfecho].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_evitaveis_preparado[col_data_solicitacao] = pd.to_datetime(
            df_evitaveis_preparado[col_data_solicitacao].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        df_evitaveis_preparado[col_data_desfecho] = pd.to_datetime(
            df_evitaveis_preparado[col_data_desfecho].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_evitaveis_preparado[col_desfecho] = df_evitaveis_preparado[col_desfecho].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_datas = df_evitaveis_preparado.dropna(subset=[col_data_solicitacao, col_data_desfecho])
    
    df_eventos_mes = df_com_datas[
        (df_com_datas[col_data_solicitacao].dt.month == selected_month) &
        (df_com_datas[col_data_solicitacao].dt.year == selected_year)
    ]
    
    df_altas_transf = df_eventos_mes[
        (df_eventos_mes[col_desfecho] == '1') | (df_eventos_mes[col_desfecho] == '3')
    ].copy()
    
    df_altas_transf['dias_evitados'] = (df_altas_transf[col_data_desfecho] - df_altas_transf[col_data_solicitacao]).dt.days
    
    df_altas_transf.loc[df_altas_transf['dias_evitados'] < 0, 'dias_evitados'] = 0
    
    numerador = df_altas_transf['dias_evitados'].sum()

    # --- 3. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Diárias Evitáveis (Híbrido): Taxa={taxa:.1f}%, Num (Dias Evitados)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 20: SAPS-3 MÉDIA ---
def calculate_saps3_media(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Média de SAPS-3 (Pontuação e %) para pacientes admitidos no mês.
    """
    
    df = df_clinico_raw.copy()
    
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    logging.info(f"SAPS-3: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    coluna_data_admissao = 'data_e_hora_admissao_uti'
    coluna_saps_pontos = 'saps_3_pontuacao'
    coluna_saps_perc = 'saps_3'

    cols_necessarias = [coluna_data_admissao, coluna_saps_pontos, coluna_saps_perc]
    if any(col not in df_geral_paciente.columns for col in cols_necessarias):
        logging.warning(f"Colunas de SAPS-3 ({cols_necessarias}) não encontradas. Retornando 0.")
        return 0.0, 0.0, 0

    df_preparado = df_geral_paciente.copy()
    
    try:
        df_preparado[coluna_data_admissao] = pd.to_datetime(
            df_preparado[coluna_data_admissao].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_preparado[coluna_data_admissao] = pd.to_datetime(
                df_preparado[coluna_data_admissao].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data de admissão (SAPS-3): {e}. Verifique o formato.")
            return 0.0, 0.0, 0
            
    df_preparado[coluna_saps_pontos] = pd.to_numeric(df_preparado[coluna_saps_pontos], errors='coerce')
    df_preparado[coluna_saps_perc] = pd.to_numeric(df_preparado[coluna_saps_perc], errors='coerce')

    df_com_admissao = df_preparado.dropna(subset=[coluna_data_admissao])
    
    df_admitidos_no_mes = df_com_admissao[
        (df_com_admissao[coluna_data_admissao].dt.month == selected_month) &
        (df_com_admissao[coluna_data_admissao].dt.year == selected_year)
    ]
    
    media_pontuacao = df_admitidos_no_mes[coluna_saps_pontos].mean()
    media_percentual = df_admitidos_no_mes[coluna_saps_perc].mean()
    
    count_pacientes = len(df_admitidos_no_mes.dropna(subset=[coluna_saps_pontos, coluna_saps_perc]))
    
    if pd.isna(media_pontuacao):
        media_pontuacao = 0.0
    if pd.isna(media_percentual):
        media_percentual = 0.0

    logging.info(f"Cálculo SAPS-3 (Admissão): Média Pontos={media_pontuacao:.1f}, Média %={media_percentual:.1f}, N={count_pacientes}")
    
    return media_pontuacao, media_percentual, count_pacientes

# --- FUNÇÃO 21: TEMPO MÉDIO DE PERMANÊNCIA ---
def calculate_tempo_medio_permanencia(df_clinico_raw, selected_month, selected_year):
    """
    Calcula o Tempo Médio de Permanência na UTI (Híbrido).
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Cálculo do Numerador (Paciente-Dias) ---
    instrumento_diario = 'diario_paciente'
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Num Permanência.")
        return 0.0, 0, 0
        
    coluna_data_diario = 'data_diario'
    coluna_leito = 'paciente_ocupando_leito'

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_leito]):
        logging.warning("Colunas do Num Permanência ('data_diario', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_diario_preparado = df_diario.copy()
    try:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_diario_preparado[coluna_data_diario] = pd.to_datetime(
            df_diario_preparado[coluna_data_diario].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)
    df_com_data_diario = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data_diario[
        (df_com_data_diario[coluna_data_diario].dt.month == selected_month) &
        (df_com_data_diario[coluna_data_diario].dt.year == selected_year)
    ]
    
    numerador = (df_diario_mes[coluna_leito] == '1').sum()

    # --- 2. Cálculo do Denominador (Nº de Desfechos) ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    coluna_data_desfecho = 'data_do_desfecho_uti'
    coluna_desfecho = 'desfecho_uti'
    
    if any(col not in df_geral_paciente.columns for col in [coluna_data_desfecho, coluna_desfecho]):
        logging.warning("Colunas de Desfecho ('data_do_desfecho_uti', 'desfecho_uti') não encontradas. Retornando 0.")
        return 0.0, numerador, 0

    df_desfecho_preparado = df_geral_paciente.copy()

    try:
        df_desfecho_preparado[coluna_data_desfecho] = pd.to_datetime(
            df_desfecho_preparado[coluna_data_desfecho].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        df_desfecho_preparado[coluna_data_desfecho] = pd.to_datetime(
            df_desfecho_preparado[coluna_data_desfecho].str.strip(), format='%d/%m/%Y', errors='coerce'
        )
        
    df_com_data_desfecho = df_desfecho_preparado.dropna(subset=[coluna_data_desfecho])
    
    df_desfechos_mes = df_com_data_desfecho[
        (df_com_data_desfecho[coluna_data_desfecho].dt.month == selected_month) &
        (df_com_data_desfecho[coluna_data_desfecho].dt.year == selected_year)
    ]
    
    denominador = len(df_desfechos_mes)

    # --- 3. Resultado ---
    if denominador > 0:
        media = (numerador / denominador)
    else:
        media = 0.0 

    logging.info(f"Cálculo Tempo Médio Permanência (Híbrido): Média={media:.1f} dias, Num (Paciente-Dias)={numerador}, Denom (Nº Desfechos)={denominador}")
    
    return media, numerador, denominador

# --- FUNÇÃO 22: TAXA DE MORTALIDADE HOSPITALAR ---
def calculate_taxa_mortalidade_hospitalar(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Mortalidade Hospitalar para o mês selecionado.
    """
    
    df = df_clinico_raw.copy()
    
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    logging.info(f"Mortalidade Hospitalar: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    coluna_data_desfecho = 'data_desfecho_hospitalar'
    coluna_desfecho = 'desfecho_hospitalar'

    if coluna_data_desfecho not in df_geral_paciente.columns or coluna_desfecho not in df_geral_paciente.columns:
        logging.warning(f"Colunas de desfecho hospitalar ('{coluna_data_desfecho}', '{coluna_desfecho}') não encontradas. Retornando 0.")
        return 0.0, 0, 0 

    df_preparado = df_geral_paciente.copy()
    try:
        df_preparado[coluna_data_desfecho] = pd.to_datetime(
            df_preparado[coluna_data_desfecho].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_preparado[coluna_data_desfecho] = pd.to_datetime(
                df_preparado[coluna_data_desfecho].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data do desfecho hospitalar: {e}. Verifique o formato.")
            return 0.0, 0, 0 

    df_preparado[coluna_desfecho] = df_preparado[coluna_desfecho].astype(str)

    df_com_desfecho = df_preparado.dropna(subset=[coluna_data_desfecho])
    
    df_mes_corrente = df_com_desfecho[
        (df_com_desfecho[coluna_data_desfecho].dt.month == selected_month) &
        (df_com_desfecho[coluna_data_desfecho].dt.year == selected_year)
    ]

    denominador = len(df_mes_corrente)
    
    is_obito_raw_1 = df_mes_corrente[coluna_desfecho].eq('2')
    is_obito_raw_2 = df_mes_corrente[coluna_desfecho].eq('2.0')
    
    numerador = (is_obito_raw_1 | is_obito_raw_2).sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0

    logging.info(f"Cálculo Mortalidade Hospitalar (Formato RAW): Taxa={taxa:.1f}%, Num={numerador}, Denom={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 23: TAXA DE REINTERNAÇÃO 48H ---
def calculate_taxa_reinternacao_48h(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Reinternação em 48h (Evento Principal).
    """
    
    df = df_clinico_raw.copy()
    
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    logging.info(f"Reinternação 48h: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    coluna_data_desfecho = 'data_do_desfecho_uti'
    coluna_desfecho = 'desfecho_uti'
    coluna_reinternacao = 'reinternacao_na_uti_48h'

    cols_necessarias = [coluna_data_desfecho, coluna_desfecho, coluna_reinternacao]
    if any(col not in df_geral_paciente.columns for col in cols_necessarias):
        logging.warning(f"Colunas de Reinternação 48h ({cols_necessarias}) não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_preparado = df_geral_paciente.copy()
    try:
        df_preparado[coluna_data_desfecho] = pd.to_datetime(
            df_preparado[coluna_data_desfecho].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_preparado[coluna_data_desfecho] = pd.to_datetime(
                df_preparado[coluna_data_desfecho].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data do desfecho (Reinternação): {e}. Verifique o formato.")
            return 0.0, 0, 0 

    df_preparado[coluna_desfecho] = df_preparado[coluna_desfecho].astype(str).str.replace(r'\.0$', '', regex=True)
    df_preparado[coluna_reinternacao] = df_preparado[coluna_reinternacao].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_desfecho = df_preparado.dropna(subset=[coluna_data_desfecho])
    
    df_mes_corrente = df_com_desfecho[
        (df_com_desfecho[coluna_data_desfecho].dt.month == selected_month) &
        (df_com_desfecho[coluna_data_desfecho].dt.year == selected_year)
    ]
    
    denominador = (df_mes_corrente[coluna_desfecho] == '1').sum()
    numerador = (df_mes_corrente[coluna_reinternacao] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0

    logging.info(f"Cálculo Reinternação 48h (Evento): Taxa={taxa:.1f}%, Num (Reinternações)={numerador}, Denom (Altas)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 24: TAXA DE RE-SOLICITAÇÃO 48H ---
def calculate_taxa_resolicitacao_48h(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Re-solicitação de UTI em 48h (Evento Principal).
    """
    
    df = df_clinico_raw.copy()
    
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    logging.info(f"Re-solicitação 48h: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    coluna_data_desfecho = 'data_do_desfecho_uti'
    coluna_desfecho = 'desfecho_uti'
    coluna_resolicitacao = 're_solicitacao_do_leito' 

    cols_necessarias = [coluna_data_desfecho, coluna_desfecho, coluna_resolicitacao]
    if any(col not in df_geral_paciente.columns for col in cols_necessarias):
        logging.warning(f"Colunas de Re-solicitação 48h ({cols_necessarias}) não encontradas. Retornando 0.")
        return 0.0, 0, 0

    df_preparado = df_geral_paciente.copy()
    try:
        df_preparado[coluna_data_desfecho] = pd.to_datetime(
            df_preparado[coluna_data_desfecho].str.strip(), 
            format='%Y-%m-%d', 
            errors='coerce'
        )
    except Exception:
        try:
            df_preparado[coluna_data_desfecho] = pd.to_datetime(
                df_preparado[coluna_data_desfecho].str.strip(), 
                format='%d/%m/%Y', 
                errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data do desfecho (Re-solicitação): {e}. Verifique o formato.")
            return 0.0, 0, 0 

    df_preparado[coluna_desfecho] = df_preparado[coluna_desfecho].astype(str).str.replace(r'\.0$', '', regex=True)
    df_preparado[coluna_resolicitacao] = df_preparado[coluna_resolicitacao].astype(str).str.replace(r'\.0$', '', regex=True)

    df_com_desfecho = df_preparado.dropna(subset=[coluna_data_desfecho])
    
    df_mes_corrente = df_com_desfecho[
        (df_com_desfecho[coluna_data_desfecho].dt.month == selected_month) &
        (df_com_desfecho[coluna_data_desfecho].dt.year == selected_year)
    ]

    denominador = (df_mes_corrente[coluna_desfecho] == '1').sum()
    numerador = (df_mes_corrente[coluna_resolicitacao] == '1').sum()

    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0

    logging.info(f"Cálculo Re-solicitação 48h (Evento): Taxa={taxa:.1f}%, Num (Re-solicitações)={numerador}, Denom (Altas)={denominador}")
    
    return taxa, numerador, denominador

# --- FUNÇÃO 25: SMR ---
import numpy as np

def calculate_smr(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # 1. Filtro do instrumento principal
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isna()) | (df['redcap_repeat_instrument'] == '')]
    else:
        df_geral = df

    # 2. Configuração de colunas conforme seu REDCap
    col_data = 'data_do_desfecho_uti'
    col_desfecho = 'desfecho_uti'
    col_saps = 'saps_3_pontuacao'

    df_geral[col_data] = pd.to_datetime(df_geral[col_data], errors='coerce')
    df_geral[col_saps] = pd.to_numeric(df_geral[col_saps], errors='coerce')
    
    # 3. Filtro pelo mês de desfecho
    df_mes = df_geral[
        (df_geral[col_data].dt.month == selected_month) & 
        (df_geral[col_data].dt.year == selected_year)
    ].copy()
    
    if df_mes.empty:
        return 0.0, 0.0, 0.0, 0.0

    # 4. Mortalidade Observada
    total_pacientes = len(df_mes)
    # 2 = Óbito no seu dicionário
    obitos_reais = len(df_mes[df_mes[col_desfecho].astype(str).str.contains('2', na=False)])
    taxa_obs = (obitos_reais / total_pacientes) * 100

    # 5. Mortalidade Esperada (CALIBRADA PARA A SUA PLANILHA)
    m_saps = df_mes[col_saps].mean()
    
    if m_saps > 0:
        # Novos coeficientes calibrados:
        # Para SAPS 72.5 -> Mort 61.31% (Logit 0.4604)
        # Para SAPS 100 -> Mort 91.31% (Logit 2.3515)
        # Resulta em: Beta1 = 0.06877 e Beta0 = -4.5254
        
        logit = -4.5254 + (0.06877 * m_saps)
        
        taxa_esp = (np.exp(logit) / (1 + np.exp(logit))) * 100
        smr = taxa_obs / taxa_esp if taxa_esp > 0 else 0
    else:
        taxa_esp, smr = 0.0, 0.0
    
    return smr, taxa_obs, taxa_esp, m_saps

# --- FUNÇÃO 26: SRU ---
def calculate_sru(df_clinico_raw, selected_month, selected_year):
    """
    Calcula o Uso Padronizado de Recursos (SRU).
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Definição da Tabela de Estratos (Tabela 5 do artigo) ---
    bins = [-float('inf'), 24, 34, 44, 54, 64, 74, 84, 94, float('inf')]
    labels = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    los_esperado_map = {
        1: 2.3, 2: 3.2, 3: 4.3, 4: 7.2, 5: 11.0,
        6: 16.6, 7: 22.2, 8: 29.4, 9: 39.0
    }
    
    # --- 2. Filtragem de Instrumento ---
    if 'redcap_repeat_instrument' in df.columns:
        df_geral_paciente = df[
            (df['redcap_repeat_instrument'].isnull()) | 
            (df['redcap_repeat_instrument'] == '')
        ]
    else:
        df_geral_paciente = df
    
    logging.info(f"SRU: Filtrado para {len(df_geral_paciente)} registros 'geral_paciente'.")

    # --- 3. Definição das Colunas ---
    col_data_desfecho = 'data_do_desfecho_uti'
    col_desfecho = 'desfecho_uti'
    col_data_admissao = 'data_e_hora_admissao_uti'
    col_saps_pontos = 'saps_3_pontuacao'

    cols_necessarias = [col_data_desfecho, col_desfecho, col_data_admissao, col_saps_pontos]
    if any(col not in df_geral_paciente.columns for col in cols_necessarias):
        logging.warning(f"Colunas do SRU ({cols_necessarias}) não encontradas. Retornando 0.")
        return 0.0, 0.0, 0.0

    # --- 4. Preparação dos Dados ---
    df_preparado = df_geral_paciente.copy()
    try:
        df_preparado[col_data_desfecho] = pd.to_datetime(df_preparado[col_data_desfecho].str.strip(), format='%Y-%m-%d', errors='coerce')
        df_preparado[col_data_admissao] = pd.to_datetime(df_preparado[col_data_admissao].str.strip(), format='%Y-%m-%d', errors='coerce')
    except Exception:
        try:
            df_preparado[col_data_desfecho] = pd.to_datetime(df_preparado[col_data_desfecho].str.strip(), format='%d/%m/%Y', errors='coerce')
            df_preparado[col_data_admissao] = pd.to_datetime(df_preparado[col_data_admissao].str.strip(), format='%d/%m/%Y', errors='coerce')
        except Exception as e:
            logging.error(f"Erro ao converter datas (SRU): {e}.")
            return 0.0, 0.0, 0.0

    df_preparado[col_desfecho] = df_preparado[col_desfecho].astype(str).str.replace(r'\.0$', '', regex=True)
    df_preparado[col_saps_pontos] = pd.to_numeric(df_preparado[col_saps_pontos], errors='coerce')

    # --- 5. Filtragem (Coorte de Sobreviventes do Mês) ---
    df_com_desfecho = df_preparado.dropna(subset=[col_data_desfecho, col_data_admissao, col_saps_pontos])
    
    df_mes_corrente = df_com_desfecho[
        (df_com_desfecho[col_data_desfecho].dt.month == selected_month) &
        (df_com_desfecho[col_data_desfecho].dt.year == selected_year)
    ]
    
    df_sobreviventes = df_mes_corrente[
        (df_mes_corrente[col_desfecho] == '1') | (df_mes_corrente[col_desfecho] == '3')
    ].copy()
    
    if df_sobreviventes.empty:
        logging.info("SRU: Nenhum sobrevivente com desfecho no mês.")
        return 0.0, 0.0, 0.0

    # --- 6. Cálculo do Numerador (Observado) ---
    df_sobreviventes['los_observado'] = (df_sobreviventes[col_data_desfecho] - df_sobreviventes[col_data_admissao]).dt.days
    df_sobreviventes.loc[df_sobreviventes['los_observado'] < 0, 'los_observado'] = 0
    numerador_observado = df_sobreviventes['los_observado'].sum()

    # --- 7. Cálculo do Denominador (Esperado) ---
    df_sobreviventes['estrato_saps'] = pd.cut(df_sobreviventes[col_saps_pontos], bins=bins, right=True, labels=labels)
    df_sobreviventes['los_esperado'] = df_sobreviventes['estrato_saps'].map(los_esperado_map)
    
    # --- CORREÇÃO AQUI ---
    df_sobreviventes['los_esperado'] = pd.to_numeric(df_sobreviventes['los_esperado'], errors='coerce')
    # --- FIM DA CORREÇÃO ---

    denominador_esperado = df_sobreviventes['los_esperado'].sum()

    # --- 8. Cálculo do SRU ---
    if denominador_esperado > 0:
        sru = numerador_observado / denominador_esperado
    else:
        sru = 0.0 

    logging.info(f"Cálculo SRU (Evento): SRU={sru:.2f}, Observado (dias)={numerador_observado}, Esperado (dias)={denominador_esperado}")
    
    return sru, numerador_observado, denominador_esperado