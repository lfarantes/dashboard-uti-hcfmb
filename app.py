import streamlit as st
import pandas as pd
import datetime
import logging

# Módulos do projeto - Verifique se o nome do arquivo é indicadores_clinicos.py
import indicadores_clinicos 
from data_loader import load_redcap_data 
import admin_report

# --- Configuração da Página ---
st.set_page_config(
    page_title="Dashboard UTI Clínica",
    page_icon="🏥",
    layout="wide"
)

# --- Sidebar de Filtros ---
with st.sidebar:
    st.title("Filtros de Análise")
    today = datetime.date.today()
    default_year = today.year
    default_month = today.month
    year_options = list(range(default_year - 5, default_year + 1))
    selected_year = st.selectbox(
        "Ano", 
        options=year_options, 
        index=len(year_options) - 1
    )
    months = {
        "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, 
        "Maio": 5, "Junho": 6, "Julho": 7, "Agosto": 8, 
        "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12
    }
    month_name = st.selectbox(
        "Mês", 
        options=months.keys(), 
        index=default_month - 1
    )
    selected_month = months[month_name]

    st.markdown("---") 

    if st.button("Recarregar Dados (Limpar Cache)"):
        st.cache_data.clear()
        st.rerun()

# --- Carregamento dos Dados ---
@st.cache_data
def get_data(api_key_geral, api_key_enfermagem):
    try:
        df_admin, df_clinico = load_redcap_data(api_key_geral, api_key_enfermagem)
        logging.info(f"Dados admin carregados: {df_admin.shape[0]} linhas")
        logging.info(f"Dados clínicos carregados: {df_clinico.shape[0]} linhas") 
        return df_admin, df_clinico
    except Exception as e:
        logging.error(f"Falha ao carregar dados do REDCap: {e}")
        raise e 

try:
    df_admin_data, df_clinical_data = get_data(
        st.secrets["api_key_geral"], 
        st.secrets["api_key_enfermagem"]
    )
except Exception as e:
    st.error(f"Erro ao carregar dados do REDCap: {e}")
    st.error("Verifique suas chaves de API, URLs e permissões.")
    st.stop()


# --- Título Principal ---
st.title(f"Dashboard de Gestão – UTI Clínica")
st.markdown(f"### Análise de {month_name} de {selected_year}")

# --- Criação das Abas ---
tab_medica, tab_enfermagem, tab_fisioterapia, tab_nutricao = st.tabs(
    ["Médica", "Enfermagem", "Fisioterapia", "Nutrição"]
)

# --- Aba 1: Médica ---
with tab_medica:
    st.subheader("Indicadores Médicos")
    if not df_clinical_data.empty:
        
        # --- Cálculo dos Indicadores ---
        taxa_mortalidade, num_obitos, num_desfechos = indicadores_clinicos.calculate_taxa_mortalidade_uti(
            df_clinical_data, selected_month, selected_year
        )
        taxa_inf_cvc, num_inf_cvc, num_cvc_dias_inf = indicadores_clinicos.calculate_densidade_infeccao_cvc(
            df_clinical_data, selected_month, selected_year
        )
        taxa_inf_pav, num_inf_pav, num_vm_dias_inf = indicadores_clinicos.calculate_densidade_infeccao_pav(
            df_clinical_data, selected_month, selected_year
        )
        taxa_inf_itu, num_inf_itu, num_svd_dias_inf = indicadores_clinicos.calculate_densidade_infeccao_itu(
            df_clinical_data, selected_month, selected_year
        )
        taxa_diarias_evit, num_dias_evit, num_pac_dias_evit = indicadores_clinicos.calculate_diarias_evitaveis(
            df_clinical_data, selected_month, selected_year
        )
        media_saps_pontos, media_saps_perc, num_pac_saps = indicadores_clinicos.calculate_saps3_media(
            df_clinical_data, selected_month, selected_year
        )
        media_permanencia, num_pac_dias, num_desfechos_perm = indicadores_clinicos.calculate_tempo_medio_permanencia(
            df_clinical_data, selected_month, selected_year
        )
        taxa_mort_hosp, num_obitos_hosp, num_desfechos_hosp = indicadores_clinicos.calculate_taxa_mortalidade_hospitalar(
            df_clinical_data, selected_month, selected_year
        )
        taxa_reint_48h, num_reint, num_altas_reint = indicadores_clinicos.calculate_taxa_reinternacao_48h(
            df_clinical_data, selected_month, selected_year
        )
        taxa_resol_48h, num_resol, num_altas_resol = indicadores_clinicos.calculate_taxa_resolicitacao_48h(
            df_clinical_data, selected_month, selected_year
        )
        # --- Chamada da função (Certifique-se de que os nomes à esquerda do = são estes) ---
        smr, taxa_obs, taxa_esp, m_saps = indicadores_clinicos.calculate_smr(
            df_clinical_data, selected_month, selected_year
        )
        sru, dias_obs, dias_esp = indicadores_clinicos.calculate_sru(
            df_clinical_data, selected_month, selected_year
        )

        # --- Exibição ---
        
        #st.write("#### Indicadores de Gravidade (Admissão)")
        #col1, col2, col3 = st.columns(3)
        #with col1:
        #    st.metric(
        #        label="Média SAPS-3 (Pontos)",
        #        value=f"{media_saps_pontos:.1f}",
        #        help=f"Média da pontuação SAPS-3 para {num_pac_saps} pacientes admitidos no período."
        #    )
        #with col2:
        #    st.metric(
        #        label="Média SAPS-3 (%)",
        #        value=f"{media_saps_perc:.1f} %",
        #        help=f"Média da probabilidade de mortalidade (SAPS-3 %) para {num_pac_saps} pacientes admitidos no período."
        #    )
        
        #st.write(f"DEBUG: Pacientes no dataframe: {len(df_clinical_data)}")
        # Se este número for 0, o problema é no carregamento dos dados (data_loader).
        st.markdown("---")
        st.write("#### Indicadores de Resultado")
        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric(
                label="Taxa de Mortalidade UTI",
                value=f"{taxa_mortalidade:.1f} %",
                help=f"Baseado em {num_obitos} óbito(s) e {num_desfechos} desfecho(s) UTI no período selecionado."
            )
        with col5:
            st.metric(
                label="Taxa de Mortalidade Hospitalar",
                value=f"{taxa_mort_hosp:.1f} %",
                help=f"Baseado em {num_obitos_hosp} óbito(s) e {num_desfechos_hosp} desfecho(s) Hospitalares no período."
            )
        with col6:
            st.metric(
                label="Tempo Médio de Permanência",
                value=f"{media_permanencia:.1f} dias",
                help=f"Total de Paciente-dias ({num_pac_dias}) dividido pelo total de Desfechos UTI ({num_desfechos_perm}) no período."
            )
        
        col7, col8, col_empty = st.columns(3) # Nova linha
        with col7:
            st.metric(
                label="Taxa de Reinternação 48h (UTI)",
                value=f"{taxa_reint_48h:.1f} %",
                help=f"Total de Reinternações ({num_reint}) dividido pelo total de Altas ({num_altas_reint}) no período. Filtro pela data da alta."
            )
        with col8:
            st.metric(
                label="Taxa de Re-solicitação 48h (UTI)",
                value=f"{taxa_resol_48h:.1f} %",
                help=f"Total de Re-solicitações ({num_resol}) dividido pelo total de Altas ({num_altas_resol}) no período. Filtro pela data da alta."
            )
        
        st.markdown("---")
        st.write("#### Indicadores de Densidade de Infecção (x 1.000 dias)")
        col9, col10, col11 = st.columns(3)
        
        with col9:
            st.metric(
                label="Densidade de Infecção (CVC)",
                value=f"{taxa_inf_cvc:.1f}",
                help=f"Total de Infecções de CVC ({num_inf_cvc}) dividido pelo total de CVC-dias ({num_cvc_dias_inf}) no período, x 1000."
            )
        
        with col10:
            st.metric(
                label="Densidade de Infecção (PAV)",
                value=f"{taxa_inf_pav:.1f}",
                help=f"Total de Infecções PAV ({num_inf_pav}) dividido pelo total de VM-dias ({num_vm_dias_inf}) no período, x 1000."
            )
        
        with col11:
            st.metric(
                label="Densidade de Infecção (ITU)",
                value=f"{taxa_inf_itu:.1f}",
                help=f"Total de Infecções ITU ({num_inf_itu}) dividido pelo total de SVD-dias ({num_svd_dias_inf}) no período, x 1000."
            )

        st.markdown("---")
        st.write("#### Indicadores de Processo")
        col12, col13 = st.columns(2)
        
        with col12:
            st.metric(
                label="Taxa de Diárias Evitáveis",
                value=f"{taxa_diarias_evit:.1f} %",
                help=f"Total de dias evitados ({num_dias_evit}) dividido pelo total de Paciente-dias ({num_pac_dias_evit}) no período."
            )
            
                # --- Bloco de exibição (Copie exatamente assim) ---
        st.markdown("---")
        st.write("#### Indicadores de Desempenho (SMR / SRU)")

        col14, col15, col16, col17 = st.columns(4)

        with col14:
            st.metric(
                label="SMR (Padronizado)",
                value=f"{smr:.2f}",
                delta=f"{smr - 1:.2f}", # if smr > 0 else None
                delta_color="inverse",
                help="SMR = Taxa Observada / Taxa Esperada. Calculado sobre a média SAPS 3 do mês."
            )

        with col15:
            st.metric(
                label="Mort. Observada",
                value=f"{taxa_obs:.1f} %",  # Agora o nome 'taxa_obs' existe acima!
                help="Porcentagem real de óbitos na UTI no mês selecionado."
            )

        with col16:
            st.metric(
                label="Mort. Esperada",
                value=f"{taxa_esp:.1f} %",
                help="Mortalidade esperada calculada via Equação Padrão sobre a média do SAPS 3."
            )
            
        with col17:
            st.metric(
                label="Média SAPS 3",
                value=f"{m_saps:.1f} pts",
                help="Média das pontuações SAPS 3 dos pacientes do período."
            )

        # Se quiser manter o SRU abaixo ou em outra linha:
        st.info(f"**Nota:** O cálculo do SMR agora utiliza a média do SAPS 3 do período ({m_saps:.1f} pts) como denominador da equação de mortalidade esperada.")

# --- Aba 2: Enfermagem (MODIFICADA) ---
with tab_enfermagem:
    st.subheader("Indicadores de Enfermagem")
    
    # --- Indicadores Administrativos (sem título de seção) ---
    if not df_admin_data.empty:
        admin_report.display_admin_metrics(df_admin_data, selected_month, selected_year)
    else:
        st.warning("Não foi possível carregar os dados administrativos.")
    
    st.markdown("---") # Divisor

    # --- Indicadores Clínicos de Enfermagem ---
    if not df_clinical_data.empty:
        
        st.write("#### Indicadores de Utilização de Dispositivos (Diário)")
        
        taxa_cvc, num_cvc_dias, num_pac_dias_cvc = indicadores_clinicos.calculate_taxa_utilizacao_cvc(
            df_clinical_data, selected_month, selected_year
        )
        taxa_svd, num_svd_dias, num_pac_dias_svd = indicadores_clinicos.calculate_taxa_utilizacao_svd(
            df_clinical_data, selected_month, selected_year
        )
        taxa_dialise, num_dialise_dias, num_pac_dias_dialise = indicadores_clinicos.calculate_taxa_utilizacao_dialise(
            df_clinical_data, selected_month, selected_year
        )
        taxa_dva, num_dva_dias, num_pac_dias_dva = indicadores_clinicos.calculate_taxa_utilizacao_dva(
            df_clinical_data, selected_month, selected_year
        )
        
        col1, col2, col3, col4 = st.columns(4) 
        with col1:
            st.metric(
                label="Taxa de Utilização de CVC",
                value=f"{taxa_cvc:.1f} %",
                help=f"Total de CVC-dias ({num_cvc_dias}) dividido pelo total de Paciente-dias ({num_pac_dias_cvc}) no período."
            )
        with col2:
            st.metric(
                label="Taxa de Utilização de SVD",
                value=f"{taxa_svd:.1f} %",
                help=f"Total de SVD-dias ({num_svd_dias}) dividido pelo total de Paciente-dias ({num_pac_dias_svd}) no período."
            )
        with col3:
            st.metric(
                label="Taxa de Utilização de Diálise",
                value=f"{taxa_dialise:.1f} %",
                help=f"Total de Diálise-dias ({num_dialise_dias}) dividido pelo total de Paciente-dias ({num_pac_dias_dialise}) no período."
            )
        with col4:
            st.metric(
                label="Taxa de Utilização de DVA",
                value=f"{taxa_dva:.1f} %",
                help=f"Total de DVA-dias ({num_dva_dias}) dividido pelo total de Paciente-dias ({num_pac_dias_dva}) no período."
            )

        st.markdown("---")
        
        st.write("#### Indicadores de Incidência (Evento)")
        
        taxa_lpp, num_lpp, num_pac_dias_lpp = indicadores_clinicos.calculate_taxa_incidencia_lpp(
            df_clinical_data, selected_month, selected_year
        )
        taxa_flebite, num_flebite, num_pac_dias_flebite = indicadores_clinicos.calculate_taxa_incidencia_flebite(
            df_clinical_data, selected_month, selected_year
        )
        
        col5, col6 = st.columns(2) 
        
        with col5:
            st.metric(
                label="Taxa de Incidência de LPP",
                value=f"{taxa_lpp:.1f} %",
                help=f"Total de Novas LPPs ({num_lpp}) dividido pelo total de Paciente-dias ({num_pac_dias_lpp}) no período. Filtro pela data do evento."
            )
        
        with col6:
            st.metric(
                label="Taxa de Incidência de Flebite",
                value=f"{taxa_flebite:.1f} %",
                help=f"Total de Novas Flebites ({num_flebite}) dividido pelo total de Paciente-dias ({num_pac_dias_flebite}) no período. Filtro pela data do evento."
            )
    else:
        st.warning("Não foi possível carregar os dados clínicos de enfermagem.")

# --- Aba 3: Fisioterapia ---
with tab_fisioterapia:
    st.subheader("Indicadores de Fisioterapia")
    
    if not df_clinical_data.empty:
        
        media_dias_vm, total_dias_vm, total_pac_vm = indicadores_clinicos.calculate_tempo_medio_vm(
            df_clinical_data, selected_month, selected_year
        )
        taxa_util_vm, num_vm_dias, num_pac_dias = indicadores_clinicos.calculate_taxa_utilizacao_vm(
            df_clinical_data, selected_month, selected_year
        )
        taxa_eot_pal, num_eot_pal, num_eot_total_pal = indicadores_clinicos.calculate_taxa_eot_paliativa(
            df_clinical_data, selected_month, selected_year
        )
        taxa_eot_acid, num_eot_acid, num_eot_total_acid = indicadores_clinicos.calculate_taxa_eot_acidental(
            df_clinical_data, selected_month, selected_year
        )
        taxa_re_iot, num_re_iot, num_eot_planejadas = indicadores_clinicos.calculate_taxa_re_iot(
            df_clinical_data, selected_month, selected_year
        )

        st.write("#### Indicadores de Ventilação Mecânica (VM)")
        col1, col2 = st.columns(2) 
        
        with col1:
            st.metric(
                label="Tempo Médio de VM",
                value=f"{media_dias_vm:.1f} dias",
                help=f"Baseado em {total_dias_vm} dias totais de VM, dividido por {total_pac_vm} pacientes únicos em VM no período."
            )
        
        with col2:
            st.metric(
                label="Taxa de Utilização de VM",
                value=f"{taxa_util_vm:.1f} %",
                help=f"Total de VM-dias ({num_vm_dias}) dividido pelo total de Paciente-dias ({num_pac_dias}) no período."
            )
        
        st.markdown("---")
        st.write("#### Indicadores de Extubação (EOT)")
        col3, col4, col5 = st.columns(3)

        with col3:
            st.metric(
                label="Proporção EOT Paliativa",
                value=f"{taxa_eot_pal:.1f} %",
                help=f"Total de EOTs Paliativas ({num_eot_pal}) dividido pelo total de EOTs ({num_eot_total_pal}) no período. Filtro pela data do evento."
            )
            
        with col4:
            st.metric(
                label="Taxa EOT Acidental",
                value=f"{taxa_eot_acid:.1f} %",
                help=f"Total de EOTs Acidentais ({num_eot_acid}) dividido pelo total de EOTs ({num_eot_total_acid}) no período. Filtro pela data do evento."
            )
        
        with col5:
            st.metric(
                label="Taxa Re-IOT 48h",
                value=f"{taxa_re_iot:.1f} %",
                help=f"Total de Re-IOTs ({num_re_iot}) dividido pelo total de EOTs Planejadas ({num_eot_planejadas}) no período. Filtro pela data do evento."
            )
        
        st.markdown("---")
        st.markdown("*Todos os indicadores de Fisioterapia implementados.*")
    else:
        st.warning("Não foi possível carregar os dados clínicos.")

# --- Aba 4: Nutrição ---
with tab_nutricao:
    st.subheader("Indicadores de Nutrição")
    
    if not df_clinical_data.empty:
        
        taxa_desnutricao, num_desnutridos, num_admissoes = indicadores_clinicos.calculate_taxa_desnutricao(
            df_clinical_data, selected_month, selected_year
        )
        taxa_dieta, vol_infundido, vol_prescrito = indicadores_clinicos.calculate_relacao_dieta(
            df_clinical_data, selected_month, selected_year
        )
        media_dias_meta, total_dias, total_pac_meta = indicadores_clinicos.calculate_tempo_ate_meta(
            df_clinical_data, selected_month, selected_year
        )

        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Taxa de Desnutrição (Admissão)",
                value=f"{taxa_desnutricao:.1f} %",
                help=f"Baseado em {num_desnutridos} paciente(s) desnutridos e {num_admissoes} admissão(ões) total(is) no período. Filtro pelo mês de admissão."
            )
        
        with col2:
            st.metric(
                label="Relação Prescrito vs. Infundido",
                value=f"{taxa_dieta:.1f} %",
                help=f"Total Infundido: {vol_infundido:,.0f} mL / Total Prescrito: {vol_prescrito:,.0f} mL. Filtro pelos registros diários do mês."
            )
        
        with col3:
            st.metric(
                label="Tempo Médio até a Meta",
                value=f"{media_dias_meta:.1f} dias",
                help=f"Soma de {total_dias:,.0f} dias até a meta, dividido por {total_pac_meta} pacientes admitidos no período. Filtro pelo mês de admissão."
            )

        st.markdown("---")
        st.markdown("*Todos os indicadores de Nutrição implementados.*")
    else:
        st.warning("Não foi possível carregar os dados clínicos.")