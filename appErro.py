import streamlit as st
import pandas as pd
import datetime
import indicadores_clinicos26
from data_loader import load_redcap_data 

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard UTI Clínica - HCFMB", page_icon="🏥", layout="wide")

# Estilo para os cards
st.markdown("<style>.stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; }</style>", unsafe_allow_html=True)

# --- Carregamento de Dados ---
@st.cache_data(ttl=600)
def fetch_data():
    try:
        t_geral = st.secrets["api_key_geral"]
        t_enf = st.secrets["api_key_enfermagem"]
        resultado = load_redcap_data(api_key_geral=t_geral, api_key_enfermagem=t_enf)
        df_geral = pd.DataFrame(resultado[0])
        df_enf = pd.DataFrame(resultado[1])
        
        if df_geral.empty: return None, False
        
        id_col = df_geral.columns[0]
        if not df_enf.empty:
            df_unido = pd.merge(df_geral, df_enf, left_on=id_col, right_on=df_enf.columns[0], how='outer', suffixes=('', '_enf'))
        else:
            df_unido = df_geral
            
        if 'record_id' not in df_unido.columns: df_unido['record_id'] = df_unido[id_col]
        return df_unido, not df_enf.empty
    except Exception as e:
        st.error(f"Erro: {e}")
        return None, False

df, tem_enf = fetch_data()

# --- Sidebar ---
with st.sidebar:
    st.title("Filtros")
    anos = [2024, 2025, 2026]
    selected_year = st.selectbox("Ano", anos, index=1)
    meses = {"Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12}
    nome_mes = st.selectbox("Mês", list(meses.keys()), index=datetime.date.today().month - 1)
    m = meses[nome_mes]
    y = selected_year

if df is not None:
    st.title(f"🏥 Dashboard Completo UTI - {nome_mes}/{y}")

    # --- SEÇÃO 1: PERFORMANCE (SMR, SAPS, MORTALIDADE) ---
    st.header("📊 1. Desempenho e Gravidade")
    smr, tx_obs, tx_esp = indicadores_clinicos26.calculate_smr(df, m, y)
    saps_pts, _, saps_n = indicadores_clinicos26.calculate_saps3_media(df, m, y)
    tx_mort_uti, n_obt_uti, _ = indicadores_clinicos26.calculate_taxa_mortalidade_uti(df, m, y)
    tx_mort_hosp, n_obt_hosp, _ = indicadores_clinicos26.calculate_taxa_mortalidade_hospitalar(df, m, y)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SMR", f"{smr:.2f}", help="Razão entre mortalidade real e esperada")
    c2.metric("SAPS 3 Médio", f"{saps_pts:.1f} pts", f"{saps_n} pac.")
    c3.metric("Mortalidade UTI", f"{tx_mort_uti:.1f}%", f"{n_obt_uti} óbitos")
    c4.metric("Mortalidade Hosp.", f"{tx_mort_hosp:.1f}%", f"{n_obt_hosp} óbitos")

    # --- SEÇÃO 2: SEGURANÇA (INFECÇÕES E EVENTOS) ---
    st.header("🛡️ 2. Segurança do Paciente")
    d_cvc, n_cvc, _ = indicadores_clinicos26.calculate_densidade_infeccao_cvc(df, m, y)
    d_pav, n_pav, _ = indicadores_clinicos26.calculate_densidade_infeccao_pav(df, m, y)
    d_itu, n_itu, _ = indicadores_clinicos26.calculate_densidade_infeccao_itu(df, m, y)
    tx_lpp, n_lpp, _ = indicadores_clinicos26.calculate_taxa_incidencia_lpp(df, m, y)
    tx_queda, n_queda, _ = indicadores_clinicos26.calculate_taxa_incidencia_queda(df, m, y)
    tx_extub, n_extub, _ = indicadores_clinicos26.calculate_taxa_extubacao_acidental(df, m, y)

    c1, c2, c3 = st.columns(3)
    c1.metric("Densidade CVC", f"{d_cvc:.1f}", f"{n_cvc} infec.")
    c2.metric("Densidade PAV", f"{d_pav:.1f}", f"{n_pav} infec.")
    c3.metric("Densidade ITU", f"{d_itu:.1f}", f"{n_itu} infec.")
    
    c4, c5, c6 = st.columns(3)
    c4.metric("Incidência LPP", f"{tx_lpp:.1f}%", f"{n_lpp} casos")
    c5.metric("Incidência Queda", f"{tx_queda:.1f}%", f"{n_queda} casos")
    c6.metric("Extubação Acidental", f"{tx_extub:.1f}%", f"{n_extub} casos")

    # --- SEÇÃO 3: SUPORTE RESPIRATÓRIO E FISIOTERAPIA ---
    st.header("🫁 3. Suporte Respiratório")
    tx_vm, _, _ = indicadores_clinicos26.calculate_taxa_utilizacao_vm(df, m, y)
    t_vm_media, _, _ = indicadores_clinicos26.calculate_tempo_medio_vm(df, m, y)
    tx_reiot, _, _ = indicadores_clinicos26.calculate_taxa_re_iot(df, m, y)
    tx_sucesso_ext, _, _ = indicadores_clinicos26.calculate_taxa_sucesso_extubacao(df, m, y)
    tx_vni, _, _ = indicadores_clinicos26.calculate_taxa_sucesso_vni(df, m, y)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Uso de VM", f"{tx_vm:.1f}%")
    c2.metric("Tempo VM (Média)", f"{t_vm_media:.1f} d")
    c3.metric("Reintubação (48h)", f"{tx_reiot:.1f}%")
    c4.metric("Sucesso Extubação", f"{tx_sucesso_ext:.1f}%")
    c5.metric("Sucesso VNI", f"{tx_vni:.1f}%")

    # --- SEÇÃO 4: NUTRIÇÃO ---
    st.header("🥗 4. Terapia Nutricional")
    tx_desn, _, _ = indicadores_clinicos26.calculate_taxa_desnutricao(df, m, y)
    tx_diet, _, _ = indicadores_clinicos26.calculate_relacao_dieta(df, m, y)
    t_meta, _, _ = indicadores_clinicos26.calculate_tempo_ate_meta(df, m, y)
    tx_jejum, _, _ = indicadores_clinicos26.calculate_taxa_jejum_superior_24h(df, m, y)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Desnutrição Adm.", f"{tx_desn:.1f}%")
    c2.metric("Meta Nutricional", f"{tx_diet:.1f}%")
    c3.metric("Tempo até Meta", f"{t_meta:.1f} d")
    c4.metric("Jejum > 24h", f"{tx_jejum:.1f}%")

    # --- SEÇÃO 5: EFICIÊNCIA OPERACIONAL ---
    st.header("⏱️ 5. Eficiência e Ocupação")
    perm, _, _ = indicadores_clinicos26.calculate_tempo_medio_permanencia(df, m, y)
    giro, _ = indicadores_clinicos26.calculate_giro_leito(df, m, y)
    ocup, _, _ = indicadores_clinicos26.calculate_taxa_ocupacao(df, m, y)
    evit, _, _ = indicadores_clinicos26.calculate_diarias_evitaveis(df, m, y)
    readm, _, _ = indicadores_clinicos26.calculate_taxa_readmissao_48h(df, m, y)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Permanência Média", f"{perm:.1f} d")
    c2.metric("Taxa Ocupação", f"{ocup:.1f}%")
    c3.metric("Giro de Leito", f"{giro:.1f}")
    c4.metric("Diárias Evitáveis", f"{evit:.1f}%")
    c5.metric("Readmissão (48h)", f"{readm:.1f}%")

    st.markdown("---")
    st.caption(f"Total de registros processados: {len(df)}")