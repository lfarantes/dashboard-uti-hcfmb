import pandas as pd
from redcap import Project 
import logging
import io 

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO)

# URLs da API (com a barra final)
URL_PROJETO_ADMIN = "https://redcap.hcfmb.unesp.br/api/" 
URL_PROJETO_CLINICO = "https://redcap.hcfmb.unesp.br/api/" 

def load_redcap_data(api_key_geral, api_key_enfermagem):
    """
    Carrega dados de dois projetos REDCap e retorna como DataFrames do pandas.
    MODIFICADO (Plano C): Remove totalmente o argumento 'format'.
    A biblioteca 'pycap' retornará uma lista de dicionários por padrão.
    """
    try:
        # --- Projeto 1: Administrativo (Leitos, Profissionais) ---
        logging.info("Conectando ao projeto Admin (Geral)...")
        project_admin = Project(URL_PROJETO_ADMIN, api_key_geral)
        
        # --- CORREÇÃO 3: Remover 'format' ---
        logging.info("Exportando dados admin (formato padrão: list[dict])...")
        # Chamada sem 'format'. Isso retornará uma lista de dicionários.
        data_admin_raw = project_admin.export_records() 
        
        # O Pandas converte uma lista de dicionários diretamente.
        df_admin = pd.DataFrame(data_admin_raw)
        
        logging.info(f"Projeto Admin carregado: {df_admin.shape[0]} linhas.")

        # --- Projeto 2: Clínico (Pacientes, Desfechos, Diário) ---
        logging.info("Conectando ao projeto Clínico (Enfermagem)...")
        project_clinico = Project(URL_PROJETO_CLINICO, api_key_enfermagem)
        
        # --- CORREÇÃO 3: Remover 'format' ---
        logging.info("Exportando dados clínicos (formato padrão: list[dict])...")
        # Chamada sem 'format'.
        data_clinico_raw = project_clinico.export_records()
        
        # O Pandas converte a lista de dicionários.
        df_clinico = pd.DataFrame(data_clinico_raw)

        logging.info(f"Projeto Clínico carregado: {df_clinico.shape[0]} linhas.")
        
        # Manter as colunas de ID como string (texto) é uma boa prática
        if 'record_id' in df_clinico.columns:
            df_clinico['record_id'] = df_clinico['record_id'].astype(str)
        if 'record_id' in df_admin.columns:
             df_admin['record_id'] = df_admin['record_id'].astype(str)

        return df_admin, df_clinico

    except Exception as e:
        logging.error(f"Erro fatal ao conectar ao REDCap: {e}")
        raise e