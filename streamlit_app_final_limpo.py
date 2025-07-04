import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
import time
import logging
from config import config, IDIOMAS_POR_PAIS
import plotly.express as px

# Import functions from main.py
from main import (
    ler_planilha, 
    buscar_logo_por_site, 
    gerar_criativos, 
    get_existing_creatives, 
    upload_creatives,
    buscar_idioma_por_pais
)
from google.ads.googleads.client import GoogleAdsClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(
    page_title="🚀 Google Ads Creative Automation",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.status-box {
    background: linear-gradient(135deg, #f0f2f6 0%, #e8ecf1 100%);
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #00d4aa;
    margin: 1rem 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.success-box {
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    padding: 1.2rem 1.2rem 1.2rem 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #28a745;
    margin: 1rem 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    color: #155724;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.7rem;
}

.warning-box {
    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #ffc107;
    margin: 1rem 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.error-box {
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #dc3545;
    margin: 1rem 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.info-box {
    background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #17a2b8;
    margin: 1rem 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}

.metric-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    padding: 1.2rem 1.2rem 1.2rem 1.5rem;
    border-radius: 12px;
    border: 1px solid #e9ecef;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    text-align: left;
    margin-bottom: 1rem;
    margin-top: 0.5rem;
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: #667eea;
    margin-bottom: 0.5rem;
}

.metric-label {
    color: #6c757d;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    padding: 0.75rem 1.5rem;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.progress-container {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
}

.section-header {
    background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 1rem;
    border-radius: 10px;
    margin: 1.5rem 0 1rem 0;
    border-left: 4px solid #667eea;
}

.dataframe-container {
    background: white;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin: 1rem 0;
}

/* Sidebar tweaks */
section[data-testid="stSidebar"] {
    background: #f7f8fa;
    padding: 1.5rem 1rem 1.5rem 1.5rem;
}

.sidebar-header {
    font-size: 1.2rem;
    font-weight: 700;
    color: #495057;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.sidebar-subheader {
    font-size: 1rem;
    font-weight: 600;
    color: #667eea;
    margin-top: 1.5rem;
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

def check_credentials():
    """Check if all required credential files exist"""
    required_files = [
        "google-ads.yaml",
        "drive_credentials.json", 
        "sheets_credentials.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files

def load_campaigns_data():
    """Load campaigns data from Google Sheets"""
    try:
        df = ler_planilha()
        if df is not None and not df.empty:
            return df
        else:
            return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return None

def initialize_session_state():
    """Initialize session state variables"""
    if 'urls_checked' not in st.session_state:
        st.session_state.urls_checked = False
    if 'campaigns_needing_urls' not in st.session_state:
        st.session_state.campaigns_needing_urls = []
    if 'campaigns_with_urls' not in st.session_state:
        st.session_state.campaigns_with_urls = []
    if 'manual_urls' not in st.session_state:
        st.session_state.manual_urls = {}
    if 'urls_confirmed' not in st.session_state:
        st.session_state.urls_confirmed = False
    if 'client' not in st.session_state:
        st.session_state.client = None

def check_urls_for_campaigns(df, client):
    """Check which campaigns need manual URLs"""
    campaigns_needing_urls = []
    campaigns_with_urls = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (idx, row) in enumerate(df.iterrows()):
        try:
            progress = float(i + 1) / float(len(df))
            progress_bar.progress(progress)
            if i == 0:
                status_text.text("Verificando campanhas...")
            
            # Convert IDs
            account_id = str(int(row["ID da Conta"].replace("-", "")))
            ad_group_id = str(int(row["ID do Grupo de Anúncios"]))
            
            # Check for existing creatives
            final_url = get_existing_creatives(client, account_id, ad_group_id)
            
            if final_url:
                campaigns_with_urls.append({
                    'idx': idx,
                    'site': row['Site'],
                    'url': final_url
                })
            else:
                campaigns_needing_urls.append({
                    'idx': idx,
                    'site': row['Site']
                })
                
        except Exception as e:
            st.error(f"❌ Erro ao verificar {row['Site']}: {str(e)}")
    
    progress_bar.progress(1.0)
    
    return campaigns_needing_urls, campaigns_with_urls

def collect_manual_urls_form(campaigns_needing_urls):
    """Collect manual URLs using a form"""
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.write(f"📝 {len(campaigns_needing_urls)} campanhas precisam de URL manual.")
    st.markdown('</div>', unsafe_allow_html=True)
    if len(campaigns_needing_urls) > 0:
        with st.expander("Ver campanhas que precisam de URL manual"):
            for campaign in campaigns_needing_urls:
                st.write(f"• {campaign['site']}")
    with st.form("url_collection_form"):
        url_inputs = {}
        for i, campaign in enumerate(campaigns_needing_urls):
            idx = campaign['idx']
            site = campaign['site']
            key = f"url_input_{i}_{idx}"
            url = st.text_input(
                f"URL final para {site}:",
                key=key,
                placeholder="https://exemplo.com"
            )
            url_inputs[idx] = url
        submitted = st.form_submit_button("✅ Confirmar URLs", type="primary")
        if submitted:
            all_provided = True
            missing_urls = []
            for idx, url in url_inputs.items():
                if url:
                    st.session_state.manual_urls[idx] = url
                else:
                    all_provided = False
                    missing_urls.append(idx)
            if all_provided:
                st.session_state.urls_confirmed = True
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success("✅ Todas as URLs foram preenchidas!")
                st.markdown('</div>', unsafe_allow_html=True)
                return True
            else:
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.error("❌ Por favor, preencha todas as URLs antes de continuar")
                st.markdown('</div>', unsafe_allow_html=True)
                st.info("💡 Dica: Digite as URLs e clique em 'Confirmar URLs'")
                return False
        else:
            return False

def process_campaigns_with_urls(df, client, manual_urls, creative_config):
    """Process campaigns with collected URLs"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_campaigns = len(df)
    processed = 0
    success_count = 0
    errors = []
    for idx, row in df.iterrows():
        try:
            processed += 1
            progress = float(processed) / float(total_campaigns)
            progress_bar.progress(progress)
            site = row["Site"]
            if processed == 1:
                status_text.text("Processando campanhas...")
            account_id = str(int(row["ID da Conta"].replace("-", "")))
            ad_group_id = str(int(row["ID do Grupo de Anúncios"]))
            logo_path = buscar_logo_por_site(site)
            if not logo_path:
                errors.append(f"❌ Logo não encontrada para {site}")
                continue
            idioma = buscar_idioma_por_pais(row["País"])
            if not idioma:
                errors.append(f"❌ Idioma não encontrado para {row['País']} - {site}")
                continue
            if creative_config['quantity_input'].lower() == "all":
                quantidade = "all"
            else:
                quantidade = int(creative_config['quantity_input'])
            criativos = gerar_criativos(
                site, 
                idioma, 
                quantidade, 
                logo_path, 
                creative_config['templates_especificos'] if creative_config['creative_type'] == "Específicos" else None
            )
            if not criativos:
                errors.append(f"❌ Nenhum criativo gerado para {site}")
                continue
            final_url = get_existing_creatives(client, account_id, ad_group_id)
            if not final_url:
                if idx in manual_urls:
                    final_url = manual_urls[idx]
                else:
                    errors.append(f"⚠️ URL final não encontrada para {site}")
                    continue
            upload_creatives(client, account_id, ad_group_id, criativos, final_url)
            success_count += 1
        except Exception as e:
            errors.append(f"❌ Erro ao processar {row['Site']}: {str(e)}")
    progress_bar.progress(1.0)
    status_text.text("✅ Processamento concluído!")
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.success(f"🎉 Processamento concluído! {success_count}/{total_campaigns} campanhas processadas com sucesso.")
    st.markdown('</div>', unsafe_allow_html=True)
    if errors:
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning(f"⚠️ {len(errors)} campanhas tiveram erro. Veja detalhes abaixo.")
        with st.expander("Ver detalhes dos erros"):
            for error in errors:
                st.write(error)
        st.markdown('</div>', unsafe_allow_html=True)
    st.balloons()

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 Google Ads Creative Automation</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-header">⚙️ Configurações</div>', unsafe_allow_html=True)
        
        # Check credentials
        missing_files = check_credentials()
        if missing_files:
            st.markdown('<div class="error-box">', unsafe_allow_html=True)
            st.error("❌ Arquivos de credenciais não encontrados:")
            for file in missing_files:
                st.write(f"• {file}")
            st.markdown('</div>', unsafe_allow_html=True)
            st.info("📝 Adicione os arquivos de credenciais para continuar.")
            return
        else:
            st.markdown('<div class="success-box">✅ Credenciais encontradas</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-subheader">📊 Configuração Atual</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Dimensões</div></div>'.format(str(config.IMAGE_WIDTH) + 'x' + str(config.IMAGE_HEIGHT)), unsafe_allow_html=True)
        st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Logo</div></div>'.format(str(config.LOGO_WIDTH) + 'x' + str(config.LOGO_HEIGHT)), unsafe_allow_html=True)
        st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Max Requests</div></div>'.format(str(config.MAX_REQUESTS)), unsafe_allow_html=True)
        
        # Reset button
        if st.button("🔄 Reset Processo", type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎯 Gerar Criativos", "📈 Análise de Campanhas"])
    
    with tab1:
        st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📊 Dashboard</h2>', unsafe_allow_html=True)
        # Load data
        df = load_campaigns_data()
        st.markdown('<div>', unsafe_allow_html=True)
        if df is not None:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'<div class="metric-value">{len(df)}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Total de Campanhas</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                unique_countries = df['País'].nunique()
                st.markdown(f'<div class="metric-value">{unique_countries}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Países</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                unique_sites = df['Site'].nunique()
                st.markdown(f'<div class="metric-value">{unique_sites}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Sites</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with col4:
                unique_accounts = df['ID da Conta'].nunique()
                st.markdown(f'<div class="metric-value">{unique_accounts}</div>', unsafe_allow_html=True)
                st.markdown('<div class="metric-label">Contas</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            # Gráficos rápidos do dashboard
            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
            gcol1, gcol2 = st.columns(2)
            with gcol1:
                st.markdown("#### Distribuição de Campanhas por País")
                country_counts = df['País'].value_counts().head(10)
                fig1 = px.bar(
                    x=country_counts.index,
                    y=country_counts.values,
                    labels={'x': 'País', 'y': 'Campanhas'},
                    text=country_counts.values
                )
                fig1.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig1, use_container_width=True)
            with gcol2:
                st.markdown("#### Top 10 Sites com Mais Campanhas")
                site_counts = df['Site'].value_counts().head(10)
                fig2 = px.bar(
                    x=site_counts.index,
                    y=site_counts.values,
                    labels={'x': 'Site', 'y': 'Campanhas'},
                    text=site_counts.values
                )
                fig2.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig2, use_container_width=True)
            # Data table
            st.markdown('<h3 class="section-header">📋 Dados das Campanhas</h3>', unsafe_allow_html=True)
            st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<h2 class="section-header">🎯 Gerar Criativos</h2>', unsafe_allow_html=True)
        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
        
        # Load campaigns
        df = load_campaigns_data()
        if df is None:
            return
        
        # Country selection
        st.markdown('<h3 class="section-header">🌍 Seleção de Países</h3>', unsafe_allow_html=True)
        countries = ["Todos"] + sorted(df['País'].unique().tolist())
        selected_countries = st.multiselect(
            "Selecione os países:",
            countries,
            default=["Todos"]
        )
        
        # Filter data based on country selection
        if "Todos" in selected_countries:
            filtered_df = df
        else:
            filtered_df = df[df['País'].isin(selected_countries)]
        
        if filtered_df.empty:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.warning("⚠️ Nenhuma campanha encontrada para os países selecionados.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Campaign selection
        st.markdown('<h3 class="section-header">📊 Seleção de Campanhas</h3>', unsafe_allow_html=True)
        campaigns = ["Todas"] + sorted(filtered_df['Campanha'].unique().tolist())
        selected_campaigns = st.multiselect(
            "Selecione as campanhas:",
            campaigns,
            default=["Todas"]
        )
        
        # Filter by campaigns
        if "Todas" in selected_campaigns:
            final_df = filtered_df
        else:
            final_df = filtered_df[filtered_df['Campanha'].isin(selected_campaigns)]
        
        if final_df.empty:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.warning("⚠️ Nenhuma campanha encontrada para a seleção.")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Show selected campaigns
        st.markdown('<h3 class="section-header">✅ Campanhas Selecionadas</h3>', unsafe_allow_html=True)
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
        st.dataframe(final_df[['Site', 'Campanha', 'País']], use_container_width=True)
        st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)
        
        # Creative configuration
        st.markdown('<h3 class="section-header">🎨 Configuração dos Criativos</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            creative_type = st.radio(
                "Tipo de criativos:",
                ["Aleatórios", "Específicos"]
            )
        
        with col2:
            if creative_type == "Específicos":
                templates_input = st.text_input(
                    "Templates específicos (separados por vírgula):",
                    placeholder="ex: template1, template2"
                )
                templates_especificos = [t.strip() for t in templates_input.split(",") if t.strip()] if templates_input else None
            else:
                templates_especificos = None
        
        quantity_input = st.text_input(
            "Quantidade de criativos (número ou 'all'):",
            value="2"
        )
        
        # Check URLs button
        if st.button("🔍 Verificar URLs das Campanhas", type="secondary", use_container_width=True):
            # Initialize Google Ads client
            try:
                client = GoogleAdsClient.load_from_storage(config.GOOGLE_ADS_YAML)
                st.session_state.client = client
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success("✅ Cliente Google Ads conectado")
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.error(f"❌ Erro ao conectar Google Ads: {e}")
                st.markdown('</div>', unsafe_allow_html=True)
                return
            
            # Check URLs for selected campaigns
            campaigns_needing_urls, campaigns_with_urls = check_urls_for_campaigns(final_df, client)
            
            # Store results in session state
            st.session_state.campaigns_needing_urls = campaigns_needing_urls
            st.session_state.campaigns_with_urls = campaigns_with_urls
            st.session_state.urls_checked = True
            
            # Show results
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.success(f"✅ Verificação concluída!")
            st.write(f"• {len(campaigns_with_urls)} campanhas com URLs existentes")
            st.write(f"• {len(campaigns_needing_urls)} campanhas precisam de URL manual")
            if campaigns_with_urls:
                with st.expander("Ver campanhas com URLs existentes"):
                    for campaign in campaigns_with_urls:
                        st.write(f"{campaign['site']}: {campaign['url']}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Show URL collection form if needed
        if st.session_state.urls_checked and st.session_state.campaigns_needing_urls:
            st.markdown('<h3 class="section-header">📝 URLs Manuais Necessárias</h3>', unsafe_allow_html=True)
            
            collect_manual_urls_form(st.session_state.campaigns_needing_urls)
            
            # Show generate button if URLs are confirmed
            if st.session_state.urls_confirmed:
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success("🎯 Todas as URLs foram configuradas! Pronto para gerar criativos.")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Generate button
                if st.button("🚀 Gerar e Enviar Criativos", type="primary", use_container_width=True):
                    creative_config = {
                        'creative_type': creative_type,
                        'templates_especificos': templates_especificos,
                        'quantity_input': quantity_input
                    }
                    
                    process_campaigns_with_urls(
                        final_df, 
                        st.session_state.client, 
                        st.session_state.manual_urls, 
                        creative_config
                    )
        
        # Show generate button if no URLs needed
        elif st.session_state.urls_checked and not st.session_state.campaigns_needing_urls:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.success("🎯 Todas as campanhas têm URLs existentes! Pronto para gerar criativos.")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Generate button
            if st.button("🚀 Gerar e Enviar Criativos", type="primary", use_container_width=True):
                creative_config = {
                    'creative_type': creative_type,
                    'templates_especificos': templates_especificos,
                    'quantity_input': quantity_input
                }
                
                process_campaigns_with_urls(
                    final_df, 
                    st.session_state.client, 
                    {},  # No manual URLs needed
                    creative_config
                )
    
    with tab3:
        st.markdown('<h2 class="section-header">📈 Análise de Campanhas</h2>', unsafe_allow_html=True)
        
        df = load_campaigns_data()
        if df is not None:
            # Advanced filtering
            col1, col2 = st.columns(2)
            
            with col1:
                selected_country = st.selectbox(
                    "Filtrar por país:",
                    ["Todos"] + sorted(df['País'].unique().tolist())
                )
            
            with col2:
                selected_site = st.selectbox(
                    "Filtrar por site:",
                    ["Todos"] + sorted(df['Site'].unique().tolist())
                )
            
            # Apply filters
            filtered_data = df
            if selected_country != "Todos":
                filtered_data = filtered_data[filtered_data['País'] == selected_country]
            if selected_site != "Todos":
                filtered_data = filtered_data[filtered_data['Site'] == selected_site]
            
            st.dataframe(filtered_data, use_container_width=True)

if __name__ == "__main__":
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
    main() 