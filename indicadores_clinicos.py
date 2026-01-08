import pandas as pd
import logging

# Configurar o logging
logging.basicConfig(level=logging.INFO)

# --- FUNÇÃO 1: TAXA DE MORTALIDADE ---
def calculate_taxa_mortalidade_uti(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Filtra instrumento geral (onde estão os desfechos)
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else:
        df_geral = df.copy()

    col_data = 'data_do_desfecho_uti'
    col_desfecho = 'desfecho_uti'

    if col_data not in df_geral.columns:
        return 0.0, 0, 0 

    # Conversão de data
    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    df_geral[col_desfecho] = df_geral[col_desfecho].astype(str).str.replace(r'\.0$', '', regex=True)

    # Filtro de Mês/Ano
    df_mes = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]

    denominador = len(df_mes)
    numerador = (df_mes[col_desfecho] == '2').sum() # 2 = Óbito

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 2: TAXA DE DESNUTRIÇÃO ---
def calculate_taxa_desnutricao(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else:
        df_geral = df.copy()

    col_data = 'data_e_hora_admissao_uti'
    col_desnutri = 'diagnostico_desnutricao'

    if col_data not in df_geral.columns:
        return 0.0, 0, 0 

    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    df_geral[col_desnutri] = df_geral[col_desnutri].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]

    denominador = len(df_mes)
    numerador = (df_mes[col_desnutri] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 3: RELAÇÃO DIETA ---
def calculate_relacao_dieta(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Filtra Diário
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else:
        return 0.0, 0, 0

    col_data = 'data_diario'
    col_presc = 'volume_prescrito'
    col_inf = 'volume_infundido_ml'

    if col_data not in df_diario.columns:
        return 0.0, 0, 0

    try:
        df_diario[col_data] = pd.to_datetime(df_diario[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_data] = pd.to_datetime(df_diario[col_data], format='%d/%m/%Y', errors='coerce')

    df_diario[col_presc] = pd.to_numeric(df_diario[col_presc], errors='coerce').fillna(0)
    df_diario[col_inf] = pd.to_numeric(df_diario[col_inf], errors='coerce').fillna(0)

    df_mes = df_diario[
        (df_diario[col_data].dt.month == selected_month) &
        (df_diario[col_data].dt.year == selected_year)
    ]

    denominador = df_mes[col_presc].sum()
    numerador = df_mes[col_inf].sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 4: TEMPO ATÉ A META ---
def calculate_tempo_ate_meta(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Separa Geral e Diário
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else:
        return 0.0, 0, 0

    # Admissão (Geral)
    col_adm = 'data_e_hora_admissao_uti'
    if col_adm not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_adm] = pd.to_datetime(df_geral[col_adm], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_adm] = pd.to_datetime(df_geral[col_adm], format='%d/%m/%Y', errors='coerce')

    # Filtra pacientes admitidos no mês
    df_admitidos = df_geral[
        (df_geral[col_adm].dt.month == selected_month) &
        (df_geral[col_adm].dt.year == selected_year)
    ][['record_id', col_adm]]
    
    denominador = len(df_admitidos)
    if denominador == 0: return 0.0, 0, 0

    # Meta (Diário)
    col_dt_diario = 'data_diario'
    col_meta = 'esta_na_meta'
    try:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%d/%m/%Y', errors='coerce')
    
    df_diario[col_meta] = df_diario[col_meta].astype(str).str.replace(r'\.0$', '', regex=True)
    
    # Pega a primeira data de meta atingida para cada ID
    df_meta_sim = df_diario[df_diario[col_meta] == '1']
    df_primeira_meta = df_meta_sim.groupby('record_id')[col_dt_diario].min().reset_index()
    df_primeira_meta.rename(columns={col_dt_diario: 'data_meta'}, inplace=True)

    # Junta
    df_final = pd.merge(df_admitidos, df_primeira_meta, on='record_id', how='left')
    
    # Calcula dias
    df_final['dias'] = (df_final['data_meta'] - df_final[col_adm]).dt.days
    df_final.loc[df_final['dias'] < 0, 'dias'] = 0 # Correção se data for anterior
    
    numerador = df_final['dias'].fillna(0).sum()
    
    media = numerador / denominador
    return media, numerador, denominador

# --- FUNÇÃO 5: TEMPO MÉDIO VM ---
def calculate_tempo_medio_vm(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0

    col_dt = 'data_diario'
    col_vm = 'suporte_vm_ultimas_24h'
    
    try:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%d/%m/%Y', errors='coerce')

    df_diario[col_vm] = df_diario[col_vm].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_diario[
        (df_diario[col_dt].dt.month == selected_month) &
        (df_diario[col_dt].dt.year == selected_year) &
        (df_diario[col_vm] == '1')
    ]

    numerador = len(df_mes) # Dias totais de VM
    denominador = df_mes['record_id'].nunique() # Pacientes únicos em VM

    media = numerador / denominador if denominador > 0 else 0.0
    return media, numerador, denominador

# --- FUNÇÃO 6: TAXA UTILIZAÇÃO VM ---
def calculate_taxa_utilizacao_vm(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0

    col_dt = 'data_diario'
    col_vm = 'suporte_vm_ultimas_24h'
    col_leito = 'paciente_ocupando_leito'

    try:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%d/%m/%Y', errors='coerce')

    df_diario[col_vm] = df_diario[col_vm].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_diario[
        (df_diario[col_dt].dt.month == selected_month) &
        (df_diario[col_dt].dt.year == selected_year)
    ]

    numerador = (df_mes[col_vm] == '1').sum()
    denominador = (df_mes[col_leito] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 7: PROPORÇÃO EOT PALIATIVA ---
def calculate_taxa_eot_paliativa(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_dt = 'eot'
    col_sim = 'eot_sim_nao'
    col_pal = 'eot_paliativa'

    if col_dt not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_dt] = pd.to_datetime(df_geral[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_dt] = pd.to_datetime(df_geral[col_dt], format='%d/%m/%Y', errors='coerce')

    df_mes = df_geral[
        (df_geral[col_dt].dt.month == selected_month) &
        (df_geral[col_dt].dt.year == selected_year)
    ]
    
    # Tratamento string
    df_mes[col_sim] = df_mes[col_sim].astype(str).str.replace(r'\.0$', '', regex=True)
    df_mes[col_pal] = df_mes[col_pal].astype(str).str.replace(r'\.0$', '', regex=True)

    denominador = (df_mes[col_sim] == '1').sum()
    numerador = (df_mes[col_pal] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 8: TAXA EOT ACIDENTAL ---
def calculate_taxa_eot_acidental(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_dt = 'eot'
    col_sim = 'eot_sim_nao'
    col_aci = 'eot_acidental'

    if col_dt not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_dt] = pd.to_datetime(df_geral[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_dt] = pd.to_datetime(df_geral[col_dt], format='%d/%m/%Y', errors='coerce')

    df_mes = df_geral[
        (df_geral[col_dt].dt.month == selected_month) &
        (df_geral[col_dt].dt.year == selected_year)
    ]
    
    df_mes[col_sim] = df_mes[col_sim].astype(str).str.replace(r'\.0$', '', regex=True)
    df_mes[col_aci] = df_mes[col_aci].astype(str).str.replace(r'\.0$', '', regex=True)

    denominador = (df_mes[col_sim] == '1').sum()
    numerador = (df_mes[col_aci] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 9: TAXA RE-IOT 48H ---
def calculate_taxa_re_iot(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_dt = 'eot' # Baseado na data da extubação
    col_eot = 'eot_sim_nao'
    col_aci = 'eot_acidental'
    col_reiot = 're_iot_sim_nao'

    if col_dt not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_dt] = pd.to_datetime(df_geral[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_dt] = pd.to_datetime(df_geral[col_dt], format='%d/%m/%Y', errors='coerce')

    df_mes = df_geral[
        (df_geral[col_dt].dt.month == selected_month) &
        (df_geral[col_dt].dt.year == selected_year)
    ]
    
    df_mes[col_eot] = df_mes[col_eot].astype(str).str.replace(r'\.0$', '', regex=True)
    df_mes[col_aci] = df_mes[col_aci].astype(str).str.replace(r'\.0$', '', regex=True)
    df_mes[col_reiot] = df_mes[col_reiot].astype(str).str.replace(r'\.0$', '', regex=True)

    total_eots = (df_mes[col_eot] == '1').sum()
    acidentais = (df_mes[col_aci] == '1').sum()
    denominador = total_eots - acidentais # EOTs planejadas
    
    numerador = (df_mes[col_reiot] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 10: TAXA UTILIZAÇÃO CVC ---
def calculate_taxa_utilizacao_cvc(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0

    col_dt = 'data_diario'
    col_dev = 'uso_cvc_nas_ultimas_24h'
    col_leito = 'paciente_ocupando_leito'

    try:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%d/%m/%Y', errors='coerce')

    df_diario[col_dev] = df_diario[col_dev].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_diario[
        (df_diario[col_dt].dt.month == selected_month) &
        (df_diario[col_dt].dt.year == selected_year)
    ]

    numerador = (df_mes[col_dev] == '1').sum()
    denominador = (df_mes[col_leito] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 11: TAXA UTILIZAÇÃO SVD ---
def calculate_taxa_utilizacao_svd(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0

    col_dt = 'data_diario'
    col_dev = 'uso_de_svd_nas_ultimas_24h'
    col_leito = 'paciente_ocupando_leito'

    try:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%d/%m/%Y', errors='coerce')

    df_diario[col_dev] = df_diario[col_dev].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_diario[
        (df_diario[col_dt].dt.month == selected_month) &
        (df_diario[col_dt].dt.year == selected_year)
    ]

    numerador = (df_mes[col_dev] == '1').sum()
    denominador = (df_mes[col_leito] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 12: TAXA UTILIZAÇÃO DIALISE ---
def calculate_taxa_utilizacao_dialise(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0

    col_dt = 'data_diario'
    col_dev = 'di_lise_nas_ultimas_24h'
    col_leito = 'paciente_ocupando_leito'

    try:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%d/%m/%Y', errors='coerce')

    df_diario[col_dev] = df_diario[col_dev].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_diario[
        (df_diario[col_dt].dt.month == selected_month) &
        (df_diario[col_dt].dt.year == selected_year)
    ]

    numerador = (df_mes[col_dev] == '1').sum()
    denominador = (df_mes[col_leito] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 13: TAXA UTILIZAÇÃO DVA ---
def calculate_taxa_utilizacao_dva(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0

    col_dt = 'data_diario'
    col_dev = 'dva_nas_ultimas_24h'
    col_leito = 'paciente_ocupando_leito'

    try:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt] = pd.to_datetime(df_diario[col_dt], format='%d/%m/%Y', errors='coerce')

    df_diario[col_dev] = df_diario[col_dev].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_diario[
        (df_diario[col_dt].dt.month == selected_month) &
        (df_diario[col_dt].dt.year == selected_year)
    ]

    numerador = (df_mes[col_dev] == '1').sum()
    denominador = (df_mes[col_leito] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 14: TAXA LPP ---
def calculate_taxa_incidencia_lpp(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Denominador (Dias de Leito)
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: return 0.0, 0, 0

    # Denominador
    col_dt_diario = 'data_diario'
    col_leito = 'paciente_ocupando_leito'
    try:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%d/%m/%Y', errors='coerce')
    
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_mes = df_diario[
        (df_diario[col_dt_diario].dt.month == selected_month) &
        (df_diario[col_dt_diario].dt.year == selected_year)
    ]
    denominador = (df_diario_mes[col_leito] == '1').sum()

    # Numerador (Eventos LPP)
    col_dt_lpp = 'lesao_pressao_data'
    col_sim = 'teve_lesao_por_pressao'
    
    if col_dt_lpp not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_dt_lpp] = pd.to_datetime(df_geral[col_dt_lpp], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_dt_lpp] = pd.to_datetime(df_geral[col_dt_lpp], format='%d/%m/%Y', errors='coerce')

    df_geral[col_sim] = df_geral[col_sim].astype(str).str.replace(r'\.0$', '', regex=True)
    df_mes_lpp = df_geral[
        (df_geral[col_dt_lpp].dt.month == selected_month) &
        (df_geral[col_dt_lpp].dt.year == selected_year)
    ]
    numerador = (df_mes_lpp[col_sim] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 15: TAXA FLEBITE ---
def calculate_taxa_incidencia_flebite(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Denominador (Dias de Leito)
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: return 0.0, 0, 0

    col_dt_diario = 'data_diario'
    col_leito = 'paciente_ocupando_leito'
    try:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%d/%m/%Y', errors='coerce')
    
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_mes = df_diario[
        (df_diario[col_dt_diario].dt.month == selected_month) &
        (df_diario[col_dt_diario].dt.year == selected_year)
    ]
    denominador = (df_diario_mes[col_leito] == '1').sum()

    # Numerador (Eventos Flebite)
    col_dt_fle = 'flebite_data'
    col_sim = 'teve_flebite'
    
    if col_dt_fle not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_dt_fle] = pd.to_datetime(df_geral[col_dt_fle], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_dt_fle] = pd.to_datetime(df_geral[col_dt_fle], format='%d/%m/%Y', errors='coerce')

    df_geral[col_sim] = df_geral[col_sim].astype(str).str.replace(r'\.0$', '', regex=True)
    df_mes_fle = df_geral[
        (df_geral[col_dt_fle].dt.month == selected_month) &
        (df_geral[col_dt_fle].dt.year == selected_year)
    ]
    numerador = (df_mes_fle[col_sim] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# ==============================================================================
# SEÇÃO CRÍTICA: INFECÇÕES (CVC, PAV, ITU) COM SMART COUNT E DATAS NOVAS
# ==============================================================================

# --- FUNÇÃO 16: DENSIDADE INFECÇÃO CVC (ICS) ---
def calculate_densidade_infeccao_cvc(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # 1. Denominador (CVC-Dias)
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0
        
    col_dt_diario = 'data_diario'
    try:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%d/%m/%Y', errors='coerce')
        
    df_diario['uso_cvc_nas_ultimas_24h'] = df_diario['uso_cvc_nas_ultimas_24h'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_mes = df_diario[
        (df_diario[col_dt_diario].dt.month == selected_month) &
        (df_diario[col_dt_diario].dt.year == selected_year)
    ]
    denominador = (df_diario_mes['uso_cvc_nas_ultimas_24h'] == '1').sum()

    # 2. Numerador (ICS) - Lógica Nova + Smart Count
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()
    
    col_data = 'ics_data'   # <--- Nome exato da nova coluna
    col_num = 'ics_numero'  # <--- Nome exato da nova coluna
    col_check = 'ics'       # <--- Checkbox "Sim"

    if col_data not in df_geral.columns: return 0.0, 0, denominador

    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    # Smart Count: Se marcou Sim (1) e numero for 0 ou vazio, assume 1
    df_geral[col_num] = pd.to_numeric(df_geral[col_num], errors='coerce').fillna(0)
    if col_check in df_geral.columns:
        df_geral[col_check] = df_geral[col_check].astype(str).str.replace(r'\.0$', '', regex=True)
        mask_erro = (df_geral[col_check] == '1') & (df_geral[col_num] <= 0)
        df_geral.loc[mask_erro, col_num] = 1

    df_eventos = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]
    numerador = df_eventos[col_num].sum()

    taxa = (numerador / denominador) * 1000 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 17: DENSIDADE INFECÇÃO PAV ---
def calculate_densidade_infeccao_pav(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Denominador (VM-Dias)
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0
        
    col_dt_diario = 'data_diario'
    try:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%d/%m/%Y', errors='coerce')
        
    df_diario['suporte_vm_ultimas_24h'] = df_diario['suporte_vm_ultimas_24h'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_mes = df_diario[
        (df_diario[col_dt_diario].dt.month == selected_month) &
        (df_diario[col_dt_diario].dt.year == selected_year)
    ]
    denominador = (df_diario_mes['suporte_vm_ultimas_24h'] == '1').sum()

    # Numerador (PAV) - Lógica Nova + Smart Count
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()
    
    col_data = 'pavm_data'
    col_num = 'pavm_numero'
    col_check = 'pavm'

    if col_data not in df_geral.columns: return 0.0, 0, denominador

    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    df_geral[col_num] = pd.to_numeric(df_geral[col_num], errors='coerce').fillna(0)
    if col_check in df_geral.columns:
        df_geral[col_check] = df_geral[col_check].astype(str).str.replace(r'\.0$', '', regex=True)
        mask_erro = (df_geral[col_check] == '1') & (df_geral[col_num] <= 0)
        df_geral.loc[mask_erro, col_num] = 1

    df_eventos = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]
    numerador = df_eventos[col_num].sum()

    taxa = (numerador / denominador) * 1000 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 18: DENSIDADE INFECÇÃO ITU ---
def calculate_densidade_infeccao_itu(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Denominador (SVD-Dias)
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
    else: return 0.0, 0, 0
        
    col_dt_diario = 'data_diario'
    try:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%d/%m/%Y', errors='coerce')
        
    df_diario['uso_de_svd_nas_ultimas_24h'] = df_diario['uso_de_svd_nas_ultimas_24h'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_mes = df_diario[
        (df_diario[col_dt_diario].dt.month == selected_month) &
        (df_diario[col_dt_diario].dt.year == selected_year)
    ]
    denominador = (df_diario_mes['uso_de_svd_nas_ultimas_24h'] == '1').sum()

    # Numerador (ITU) - Lógica Nova + Smart Count
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()
    
    col_data = 'itu_data'
    col_num = 'itu_numero'
    col_check = 'itu'

    if col_data not in df_geral.columns: return 0.0, 0, denominador

    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    df_geral[col_num] = pd.to_numeric(df_geral[col_num], errors='coerce').fillna(0)
    if col_check in df_geral.columns:
        df_geral[col_check] = df_geral[col_check].astype(str).str.replace(r'\.0$', '', regex=True)
        mask_erro = (df_geral[col_check] == '1') & (df_geral[col_num] <= 0)
        df_geral.loc[mask_erro, col_num] = 1

    df_eventos = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]
    numerador = df_eventos[col_num].sum()

    taxa = (numerador / denominador) * 1000 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 19: DIÁRIAS EVITÁVEIS ---
def calculate_diarias_evitaveis(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Denominador (Paciente-Dias)
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: return 0.0, 0, 0

    col_dt_diario = 'data_diario'
    col_leito = 'paciente_ocupando_leito'
    try:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%d/%m/%Y', errors='coerce')
    
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_mes = df_diario[
        (df_diario[col_dt_diario].dt.month == selected_month) &
        (df_diario[col_dt_diario].dt.year == selected_year)
    ]
    denominador = (df_diario_mes[col_leito] == '1').sum()

    # Numerador (Dias Evitados)
    col_solic = 'data_solicitacao_alta'
    col_desf = 'data_do_desfecho_uti'
    col_tipo = 'desfecho_uti'

    if col_solic not in df_geral.columns or col_desf not in df_geral.columns: return 0.0, 0, denominador

    try:
        df_geral[col_solic] = pd.to_datetime(df_geral[col_solic], format='%Y-%m-%d', errors='coerce')
        df_geral[col_desf] = pd.to_datetime(df_geral[col_desf], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_solic] = pd.to_datetime(df_geral[col_solic], format='%d/%m/%Y', errors='coerce')
        df_geral[col_desf] = pd.to_datetime(df_geral[col_desf], format='%d/%m/%Y', errors='coerce')

    df_geral[col_tipo] = df_geral[col_tipo].astype(str).str.replace(r'\.0$', '', regex=True)

    df_eventos = df_geral[
        (df_geral[col_solic].dt.month == selected_month) &
        (df_geral[col_solic].dt.year == selected_year)
    ]
    
    # Alta ou Transferência
    df_altas = df_eventos[(df_eventos[col_tipo] == '1') | (df_eventos[col_tipo] == '3')].copy()
    
    df_altas['dias'] = (df_altas[col_desf] - df_altas[col_solic]).dt.days
    df_altas.loc[df_altas['dias'] < 0, 'dias'] = 0
    numerador = df_altas['dias'].sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 20: SAPS-3 MÉDIA ---
def calculate_saps3_media(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_adm = 'data_e_hora_admissao_uti'
    col_pts = 'saps_3_pontuacao'
    col_perc = 'saps_3'

    if col_adm not in df_geral.columns: return 0.0, 0.0, 0
    try:
        df_geral[col_adm] = pd.to_datetime(df_geral[col_adm], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_adm] = pd.to_datetime(df_geral[col_adm], format='%d/%m/%Y', errors='coerce')

    df_mes = df_geral[
        (df_geral[col_adm].dt.month == selected_month) &
        (df_geral[col_adm].dt.year == selected_year)
    ]

    df_mes[col_pts] = pd.to_numeric(df_mes[col_pts], errors='coerce')
    df_mes[col_perc] = pd.to_numeric(df_mes[col_perc], errors='coerce')

    media_pts = df_mes[col_pts].mean()
    media_perc = df_mes[col_perc].mean()
    n = len(df_mes.dropna(subset=[col_pts]))

    if pd.isna(media_pts): media_pts = 0.0
    if pd.isna(media_perc): media_perc = 0.0

    return media_pts, media_perc, n

# --- FUNÇÃO 21: TEMPO MÉDIO PERMANÊNCIA ---
def calculate_tempo_medio_permanencia(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    
    # Numerador (Paciente-Dias)
    if 'redcap_repeat_instrument' in df.columns:
        df_diario = df[df['redcap_repeat_instrument'] == 'diario_paciente'].copy()
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: return 0.0, 0, 0

    col_dt_diario = 'data_diario'
    col_leito = 'paciente_ocupando_leito'
    try:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%Y-%m-%d', errors='coerce')
    except:
        df_diario[col_dt_diario] = pd.to_datetime(df_diario[col_dt_diario], format='%d/%m/%Y', errors='coerce')
    
    df_diario[col_leito] = df_diario[col_leito].astype(str).str.replace(r'\.0$', '', regex=True)
    df_diario_mes = df_diario[
        (df_diario[col_dt_diario].dt.month == selected_month) &
        (df_diario[col_dt_diario].dt.year == selected_year)
    ]
    numerador = (df_diario_mes[col_leito] == '1').sum()

    # Denominador (Desfechos)
    col_dt_desf = 'data_do_desfecho_uti'
    if col_dt_desf not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_dt_desf] = pd.to_datetime(df_geral[col_dt_desf], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_dt_desf] = pd.to_datetime(df_geral[col_dt_desf], format='%d/%m/%Y', errors='coerce')

    df_desf_mes = df_geral[
        (df_geral[col_dt_desf].dt.month == selected_month) &
        (df_geral[col_dt_desf].dt.year == selected_year)
    ]
    denominador = len(df_desf_mes)

    media = (numerador / denominador) if denominador > 0 else 0.0
    return media, numerador, denominador

# --- FUNÇÃO 22: MORTALIDADE HOSPITALAR ---
def calculate_taxa_mortalidade_hospitalar(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_data = 'data_desfecho_hospitalar'
    col_desf = 'desfecho_hospitalar'

    if col_data not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    df_geral[col_desf] = df_geral[col_desf].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]

    denominador = len(df_mes)
    numerador = (df_mes[col_desf] == '2').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 23: REINTERNAÇÃO 48H ---
def calculate_taxa_reinternacao_48h(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_data = 'data_do_desfecho_uti'
    col_alta = 'desfecho_uti'
    col_reint = 'reinternacao_na_uti_48h'

    if col_data not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    df_geral[col_alta] = df_geral[col_alta].astype(str).str.replace(r'\.0$', '', regex=True)
    df_geral[col_reint] = df_geral[col_reint].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]

    denominador = (df_mes[col_alta] == '1').sum() # Altas
    numerador = (df_mes[col_reint] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 24: RE-SOLICITAÇÃO 48H ---
def calculate_taxa_resolicitacao_48h(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_data = 'data_do_desfecho_uti'
    col_alta = 'desfecho_uti'
    col_resol = 're_solicitacao_do_leito'

    if col_data not in df_geral.columns: return 0.0, 0, 0
    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    df_geral[col_alta] = df_geral[col_alta].astype(str).str.replace(r'\.0$', '', regex=True)
    df_geral[col_resol] = df_geral[col_resol].astype(str).str.replace(r'\.0$', '', regex=True)

    df_mes = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]

    denominador = (df_mes[col_alta] == '1').sum() # Altas
    numerador = (df_mes[col_resol] == '1').sum()

    taxa = (numerador / denominador) * 100 if denominador > 0 else 0.0
    return taxa, numerador, denominador

# --- FUNÇÃO 25: SMR ---
def calculate_smr(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_data = 'data_desfecho_hospitalar'
    col_desf = 'desfecho_hospitalar'
    col_saps = 'saps_3'

    if col_data not in df_geral.columns: return 0.0, 0.0, 0.0
    try:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%Y-%m-%d', errors='coerce')
    except:
        df_geral[col_data] = pd.to_datetime(df_geral[col_data], format='%d/%m/%Y', errors='coerce')

    df_geral[col_desf] = df_geral[col_desf].astype(str).str.replace(r'\.0$', '', regex=True)
    df_geral[col_saps] = pd.to_numeric(df_geral[col_saps], errors='coerce')

    df_mes = df_geral[
        (df_geral[col_data].dt.month == selected_month) &
        (df_geral[col_data].dt.year == selected_year)
    ]

    if df_mes.empty: return 0.0, 0.0, 0.0

    # Obs
    num_obs = (df_mes[col_desf] == '2').sum()
    den_obs = len(df_mes)
    taxa_obs = (num_obs / den_obs) * 100 if den_obs > 0 else 0.0

    # Esp
    taxa_esp = df_mes[col_saps].mean()
    if pd.isna(taxa_esp): taxa_esp = 0.0

    smr = (taxa_obs / taxa_esp) if taxa_esp > 0 else 0.0
    return smr, taxa_obs, taxa_esp

# --- FUNÇÃO 26: SRU ---
def calculate_sru(df_clinico_raw, selected_month, selected_year):
    df = df_clinico_raw.copy()
    if 'redcap_repeat_instrument' in df.columns:
        df_geral = df[(df['redcap_repeat_instrument'].isnull()) | (df['redcap_repeat_instrument'] == '')].copy()
    else: df_geral = df.copy()

    col_desf_dt = 'data_do_desfecho_uti'
    col_desf = 'desfecho_uti'
    col_adm = 'data_e_hora_admissao_uti'
    col_saps_pts = 'saps_3_pontuacao'

    if col_desf_dt not in df_geral.columns: return 0.0, 0.0, 0.0
    
    # Conversões
    for c in [col_desf_dt, col_adm]:
        try:
            df_geral[c] = pd.to_datetime(df_geral[c], format='%Y-%m-%d', errors='coerce')
        except:
            df_geral[c] = pd.to_datetime(df_geral[c], format='%d/%m/%Y', errors='coerce')

    df_geral[col_desf] = df_geral[col_desf].astype(str).str.replace(r'\.0$', '', regex=True)
    df_geral[col_saps_pts] = pd.to_numeric(df_geral[col_saps_pts], errors='coerce')

    # Filtro Mês
    df_mes = df_geral[
        (df_geral[col_desf_dt].dt.month == selected_month) &
        (df_geral[col_desf_dt].dt.year == selected_year)
    ]

    # Sobreviventes (Alta ou Transf)
    df_surv = df_mes[(df_mes[col_desf] == '1') | (df_mes[col_desf] == '3')].copy()
    
    if df_surv.empty: return 0.0, 0.0, 0.0

    # Observado
    df_surv['los_obs'] = (df_surv[col_desf_dt] - df_surv[col_adm]).dt.days
    df_surv.loc[df_surv['los_obs'] < 0, 'los_obs'] = 0
    obs = df_surv['los_obs'].sum()

    # Esperado
    bins = [-float('inf'), 24, 34, 44, 54, 64, 74, 84, 94, float('inf')]
    labels = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    los_map = {1: 2.3, 2: 3.2, 3: 4.3, 4: 7.2, 5: 11.0, 6: 16.6, 7: 22.2, 8: 29.4, 9: 39.0}
    
    df_surv['estrato'] = pd.cut(df_surv[col_saps_pts], bins=bins, right=True, labels=labels)
    df_surv['los_esp'] = df_surv['estrato'].map(los_map)
    df_surv['los_esp'] = pd.to_numeric(df_surv['los_esp'], errors='coerce')
    
    esp = df_surv['los_esp'].sum()

    sru = (obs / esp) if esp > 0 else 0.0
    return sru, obs, esp