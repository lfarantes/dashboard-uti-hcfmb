import pandas as pd
import logging

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
            df_geral_paciente[coluna_data_admissao].str.strip(), format='%Y-%m-%d', errors='coerce'
        )
    except Exception:
        try:
            df_geral_paciente[col_data_admissao] = pd.to_datetime(
                df_geral_paciente[coluna_data_admissao].str.strip(), format='%d/%m/%Y', errors='coerce'
            )
        except Exception as e:
            logging.error(f"Erro ao converter data de admissão: {e}.")
            return 0.0, 0, 0

    df_com_admissao = df_geral_paciente.dropna(subset=[coluna_data_admissao])
    df_admitidos_no_mes = df_com_admissao[
        (df_com_admissao[coluna_data_admissao].dt.month == selected_month) &
        (df_com_admissao[coluna_data_admissao].dt.year == selected_year)
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

# --- FUNÇÃO 11: TAXA UTILIZAÇÃO SVD (A NOVA) ---
def calculate_taxa_utilizacao_svd(df_clinico_raw, selected_month, selected_year):
    """
    Calcula a Taxa de Utilização de SVD (Operacional).
    Lógica (baseada no doc):
    - Filtro: Mês Corrente (baseado no 'data_diario').
    - Numerador (SVD-dias): SOMA 'uso_de_svd_nas_ultimas_24h' = '1'.
    - Denominador (Paciente-dias): SOMA 'paciente_ocupando_leito' = '1'.
    """
    
    df = df_clinico_raw.copy()
    
    # --- 1. Filtragem de Instrumento ---
    instrumento_diario = 'diario_paciente'
    
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == instrumento_diario]
    else:
        logging.warning("Coluna 'redcap_repeat_instrument' não encontrada. Não é possível calcular Taxa SVD.")
        return 0.0, 0, 0
    
    logging.info(f"Taxa SVD: Filtrado para {len(df_diario)} registros do instrumento '{instrumento_diario}'.")

    # --- 2. Definição das Colunas (Formato RAW) ---
    coluna_data_diario = 'data_diario'
    coluna_svd = 'uso_de_svd_nas_ultimas_24h' # <-- Numerador (MUDOU)
    coluna_leito = 'paciente_ocupando_leito' # <-- Denominador (Igual)

    if any(col not in df_diario.columns for col in [coluna_data_diario, coluna_svd, coluna_leito]):
        logging.warning("Colunas de Taxa SVD ('data_diario', 'uso_de_svd_nas_ultimas_24h', 'paciente_ocupando_leito') não encontradas. Retornando 0.")
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
            logging.error(f"Erro ao converter data_diario (Taxa SVD): {e}. Verifique o formato.")
            return 0.0, 0, 0

    # Converter colunas de 'Sim' ('1') para string
    df_diario_preparado[coluna_svd] = df_diario_preparado[coluna_svd].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_preparado[coluna_leito] = df_diario_preparado[coluna_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    # --- 4. Filtragem (Lógica de "Mês Corrente" no formulário diário) ---
    df_com_data = df_diario_preparado.dropna(subset=[coluna_data_diario])
    
    df_diario_mes = df_com_data[
        (df_com_data[coluna_data_diario].dt.month == selected_month) &
        (df_com_data[coluna_data_diario].dt.year == selected_year)
    ]
    
    # --- 5. Cálculos (Numerador e Denominador) ---
    
    # Numerador (SVD-dias): Contagem de 'Sim' ('1')
    numerador = (df_diario_mes[coluna_svd] == '1').sum()
    
    # Denominador (Paciente-dias): Contagem de 'Sim' ('1')
    denominador = (df_diario_mes[coluna_leito] == '1').sum()

    # --- 6. Resultado ---
    if denominador > 0:
        taxa = (numerador / denominador) * 100
    else:
        taxa = 0.0 

    logging.info(f"Cálculo Taxa Utilização SVD (Diário): Taxa={taxa:.1f}%, Num (SVD-Dias)={numerador}, Denom (Paciente-Dias)={denominador}")
    
    return taxa, numerador, denominador