import os
import re
import random
from datetime import datetime
import pandas as pd
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
import io
import time
import argparse
from PIL import Image, ImageSequence

# Try to import platform-specific notification libraries
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    NOTIFICATION_AVAILABLE = True
except ImportError:
    # For Linux/Mac - using subprocess for native notifications
    import subprocess
    import platform
    toaster = None
    NOTIFICATION_AVAILABLE = True


# ------------------------ CONFIGURAÇÕES GERAIS ------------------------
MAX_REQUESTS = 3000
request_count = 0  # Contador de requisições feitas

PASTA_OUTPUT = "output"
TEMPLATES_DIR = "templates"
LOGOS_DIR = "logos"
DIMENSOES = (336, 280)      # Dimensões compatíveis com Google Ads
LOGO_SIZE = (45, 14)        # Tamanho da logo

# IDs das pastas no Google Drive
TEMPLATES_DRIVE_FOLDER_ID = "1LElWu5TVRw9Xbzhgm1wm58pv0u3pVgMl"  # Substitua pelo ID da pasta de templates
LOGOS_DRIVE_FOLDER_ID = "1cVRl4kUOltDLxnMYLiVFe69MAHI8KnrL"  # ID da pasta de logos

IDIOMAS_POR_PAIS = {
    "arabia": "arabian",
    "arg": "Espanhol ",
    "alemanha": "alemão",
    "argelia": "arabic",
    "australia": "english",
    "austria": "german",
    "belgica": "french",
    "bielorrussia": "bielorrussian",
    "brasil": "portuguese",
    "bulgaria": "bulgaro",
    "canada": "english-ca",
    "chile": "Espanho",
    "colombia": "Espanhol",
    "croacia": "croatian",
    "dinamarca": "dinamarques",
    "egito": "arabic",
    "emirados arabes": "arabian",
    "emirados arabes ingles": "arabian english",
    "equador": "Espanhol",
    "espanha": "Espanhol ",
    "estonia": "estonian",
    "eua": "english",
    "filipinas": "filipino",
    "finlandia": "finlandes",
    "frança": "french",
    "georgia": "georgian",
    "grecia": "grego",
    "holanda": "dutch",
    "hungria": "hungarian",
    "india": "hindi",
    "indonesia": "indonesio",
    "irlanda": "ireland",
    "israel": "hebrew",
    "italia": "italiano",
    "japao": "japanese",
    "ko": "coreano",
    "lituania": "lituano",
    "malasia": "malay",
    "marrocos": "arabic",
    "mexico": "Espanh",
    "nigeria": "english",
    "noruega": "noruegues",
    "nz": "english",
    "peru": "Espanhol",
    "polonia": "poland",
    "portugal": "portuguese-pt",
    "paraguai": "Espanhol",
    "uk": "english-uk",
    "romenia": "romanian",
    "russia": "russian",
    "servia": "serbian",
    "singapura": "english",
    "SK": "Eslovaco",
    "suica": "suico",
    "suecia": "sueco",
    "taiwan": "mandarin",
    "tailandia": "thai",
    "tcheca": "tcheco",
    "tunisia": "arabic",
    "turquia": "turkish",
    "ucrania": "ucraniano",
    "uk": "english-uk",
    "vietna": "vietnamese",
    "uruguai": "Espanhol",
}


# Configuração do Google Sheets – sua planilha deve ter as 6 colunas: Site, ID da Conta, Nome da Conta, ID do Grupo de Anúncios, Campanha, País.
SHEET_ID = "1QQ7_ByU8siGV_NAMXM-fWiEt60fyPOJp0h-RshNsFeg"
SHEET_RANGE = "Página1!A:F"

# ------------------------ FUNÇÕES DO GOOGLE DRIVE ------------------------
def get_drive_service():
    """Inicializa e retorna o serviço do Google Drive."""
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        creds = service_account.Credentials.from_service_account_file("drive_credentials.json", scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        # Testa a conexão
        service.files().list(pageSize=1).execute()
        return service
    except Exception as e:
        print(f"❌ Erro ao inicializar o serviço do Drive: {str(e)}")
        if "credentials" in str(e).lower():
            print("⚠️ Verifique se:")
            print("1. O arquivo drive_credentials.json está na mesma pasta do script")
            print("2. O conteúdo do arquivo está correto")
            print("3. A conta de serviço tem permissão para acessar o Google Drive")
        raise e

def list_files_in_folder(folder_id):
    """Lista todos os arquivos em uma pasta do Google Drive."""
    service = get_drive_service()
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name, mimeType)",
        pageSize=1000
    ).execute()
    return results.get('files', [])

def download_file(file_id, output_path):
    """Baixa um arquivo do Google Drive para o caminho especificado."""
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    
    # Garante que o diretório pai existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(fh.getvalue())

def buscar_logo_por_site(site):
    """Busca a logo do site no Google Drive."""
    try:
        service = get_drive_service()
        
        # Remove espaços extras do nome do site
        site = site.strip()
        
        # Procura o arquivo da logo no Google Drive - case insensitive
        query = f"name contains '{site}' and name contains '.png' and '{LOGOS_DRIVE_FOLDER_ID}' in parents and trashed = false"
        
        try:
            results = service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=10
            ).execute()
            files = results.get('files', [])
            
            # Procura por correspondência exata ignorando maiúsculas/minúsculas
            matching_file = None
            for file in files:
                if file['name'].lower() == f"{site}.png".lower():
                    matching_file = file
                    break
            
            if not matching_file:
                print("❌ Nenhum arquivo correspondente encontrado")
                print("⚠️ Verifique se:")
                print(f"1. Existe um arquivo chamado '{site}.png' na pasta")
                print(f"2. O ID da pasta ({LOGOS_DRIVE_FOLDER_ID}) está correto")
                print("3. A conta de serviço tem acesso à pasta")
                return None
            
            # Cria o diretório de logos se não existir
            os.makedirs(LOGOS_DIR, exist_ok=True)
            logo_path = os.path.join(LOGOS_DIR, f"{site}.png")
            
            # Baixa a logo se ainda não estiver no cache local
            if not os.path.exists(logo_path):
                try:
                    download_file(matching_file['id'], logo_path)
                except Exception as e:
                    print(f"❌ Erro ao baixar a logo: {str(e)}")
                    return None
            
            return logo_path
            
        except Exception as e:
            print(f"❌ Erro ao buscar arquivos no Drive: {str(e)}")
            return None
            
    except Exception as e:
        print(f"❌ Erro geral ao buscar logo: {str(e)}")
        return None

def get_templates_for_language(idioma, tag=None):
    """Obtém a lista de templates para um idioma específico do Google Drive."""
    service = get_drive_service()
    
    # Se uma tag foi especificada, procura diretamente na pasta da tag
    if tag:
        # Procura a pasta da tag no Google Drive
        tag_results = service.files().list(
            q=f"name = '{tag}' and '{TEMPLATES_DRIVE_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)",
            pageSize=1
        ).execute()
        tag_folders = tag_results.get('files', [])
        
        if tag_folders:
            # Usa a pasta da tag se encontrada
            parent_id = tag_folders[0]['id']
        else:
            print(f"⚠️ Pasta {tag} não encontrada no Drive.")
            return []
    else:
        # Procura a pasta do idioma no Google Drive
        results = service.files().list(
            q=f"name = '{idioma}' and '{TEMPLATES_DRIVE_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)",
            pageSize=1
        ).execute()
        folders = results.get('files', [])
        
        if not folders:
            print(f"⚠️ Pasta {idioma} não encontrada no Drive.")
            return []
        
        parent_id = folders[0]['id']
    
    # Lista os arquivos na pasta selecionada
    templates = service.files().list(
        q=f"'{parent_id}' in parents and (mimeType = 'image/png' or mimeType = 'image/gif') and trashed = false",
        fields="files(id, name, mimeType)",
        pageSize=1000
    ).execute().get('files', [])
    
    # Retorna lista de tuplas (id, nome) dos templates
    return [(template['id'], template['name']) for template in templates]

# ------------------------ FUNÇÃO DE LEITURA DA PLANILHA ------------------------
def ler_planilha():
    expected_columns = ["Site", "ID da Conta", "Nome da Conta", "ID do Grupo de Anúncios", "Campanha", "País"]
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = service_account.Credentials.from_service_account_file("sheets_credentials.json", scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    try:
        result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=SHEET_RANGE).execute()
    except Exception as e:
        print(f"Erro ao ler a planilha: {e}")
        return None
    values = result.get("values", [])
    if not values:
        print("Nenhum dado encontrado na planilha.")
        return pd.DataFrame(columns=expected_columns)
    headers = values[0]
    if len(headers) < len(expected_columns):
        headers = expected_columns
    data = []
    for row in values[1:]:
        if len(row) < len(expected_columns):
            row += [""] * (len(expected_columns) - len(row))
        data.append(row)
    df = pd.DataFrame(data, columns=expected_columns)
    return df

# ------------------------ FUNÇÕES AUXILIARES ------------------------
def buscar_idioma_por_pais(pais):
    return IDIOMAS_POR_PAIS.get(pais.lower())

def gerar_nomes_criativos(quantidade):
    data_str = datetime.now().strftime("%d%m")
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    nomes = []
    for i in range(quantidade):
        sufixo = ""
        idx = i
        while idx >= len(alfabeto):
            sufixo = alfabeto[idx % len(alfabeto)] + sufixo
            idx = idx // len(alfabeto) - 1
        sufixo = alfabeto[idx] + sufixo
        nomes.append(f"{data_str}{sufixo}")
    return nomes

def salvar_sem_metadados(image, output_path, file_format="PNG"):
    image = image.resize(DIMENSOES)
    if file_format.upper() == "GIF":
        image.save(output_path, format="GIF", optimize=True)
    else:
        image = image.convert("RGB")
        image.save(output_path, format="PNG", optimize=True, compress_level=0)

def gerar_criativos(nome_site, idioma, quantidade, logo_path, templates_especificos=None, tag=None):
    """Gera criativos usando templates do Google Drive."""
    template_list = get_templates_for_language(idioma, tag)
    if not template_list:
        print(f"⚠️ Nenhuma pasta encontrada para o idioma: {idioma}" + (f" e tag: {tag}" if tag else ""))
        return []
    
    # Cria o diretório de output se não existir
    pasta_destino = os.path.join(PASTA_OUTPUT, f"{idioma}_{nome_site}")
    os.makedirs(pasta_destino, exist_ok=True)
    
    # Filtra os templates se templates_especificos estiver definido
    if templates_especificos:
        print(f"Filtrando templates. Procurando por: {templates_especificos}")
        filtered_templates = []
        for template_id, template_name in template_list:
            for template_spec in templates_especificos:
                if template_spec.lower() in template_name.lower():
                    filtered_templates.append((template_id, template_name))
                    print(f"Template encontrado: {template_name}")
                    break
        
        if not filtered_templates:
            print(f"⚠️ Nenhum template específico encontrado para: {templates_especificos}")
            return []
        
        template_list = filtered_templates
    
    # Determina a quantidade de criativos a gerar
    if quantidade == "all":
        quantidade = len(template_list)
    else:
        quantidade = min(len(template_list), int(quantidade))
    
    if quantidade == 0:
        print("⚠️ Não há templates disponíveis para gerar criativos.")
        return []
    
    # Gera nomes para os criativos
    nomes = gerar_nomes_criativos(quantidade)
    criativos = []
    
    # Seleciona uma amostra aleatória dos templates
    selected_templates = random.sample(template_list, quantidade)
    
    # Baixa e processa cada template
    for i, (template_id, template_name) in enumerate(selected_templates):
        print(f"Processando template: {template_name}")
        # Baixa o template temporariamente
        temp_template_path = os.path.join(pasta_destino, f"temp_template_{i}.png")
        download_file(template_id, temp_template_path)
        
        # Processa o template
        ext = os.path.splitext(temp_template_path)[1].lower()
        output_file = os.path.join(pasta_destino, f"{nomes[i]}{ext}")
        logo = Image.open(logo_path).convert("RGBA").resize(LOGO_SIZE)
        posicao = (DIMENSOES[0] - LOGO_SIZE[0] - 10, DIMENSOES[1] - LOGO_SIZE[1] - 10)
        
        if ext == ".gif":
            template = Image.open(temp_template_path)
            frames = []
            durations = []
            transparency = template.info.get('transparency', 0)
            loop = template.info.get('loop', 0)

            for frame in ImageSequence.Iterator(template):
                duration = frame.info.get("duration", 100)
                # Sempre trabalhe em uma cópia nova do frame
                frame_rgba = frame.convert("RGBA").resize(DIMENSOES, Image.Resampling.LANCZOS)
                frame_with_logo = frame_rgba.copy()
                frame_with_logo.paste(logo, posicao, logo)
                frame_p = frame_with_logo.convert("P", palette=Image.ADAPTIVE)
                frames.append(frame_p)
                durations.append(duration)

            frames[0].save(
                output_file,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=loop,
                optimize=False,
                disposal=2,  # ESSENCIAL para não empilhar a logo!
                transparency=transparency
            )
        else:
            template = Image.open(temp_template_path).resize(DIMENSOES)
            template.paste(logo, posicao, logo)
            salvar_sem_metadados(template, output_file, "PNG")
        
        # Remove o template temporário
        os.remove(temp_template_path)
        criativos.append(output_file)
    
    return criativos

def fazer_requisicao_liberada(func, *args, **kwargs):
    global request_count
    if request_count >= MAX_REQUESTS:
        print(f"Limite de requisições ({MAX_REQUESTS}) atingido. Aguardando reinício...")
        time.sleep(3600)
        request_count = 0
    try:
        response = func(*args, **kwargs)
        request_count += 1
        return response
    except Exception as e:
        print(f"Erro ao fazer a requisição: {e}")
        return None

def get_existing_creatives(client, account_id, ad_group_id):
    google_ads_service = client.get_service("GoogleAdsService")
    query = f"""
        SELECT ad_group_ad.ad.final_urls 
        FROM ad_group_ad 
        WHERE ad_group_ad.ad_group = 'customers/{account_id}/adGroups/{ad_group_id}' 
        AND ad_group_ad.status = 'ENABLED'
    """
    try:
        response = fazer_requisicao_liberada(google_ads_service.search, customer_id=account_id, query=query)
        for row in response:
            final_urls = row.ad_group_ad.ad.final_urls
            if final_urls:
                return final_urls[0]
        return None
    except Exception as ex:
        print(f"❌ Erro ao buscar criativos existentes: {ex}")
        return None

def upload_creatives(client, account_id, ad_group_id, creative_paths, final_url):
    print(f"🚀 Iniciando upload de {len(creative_paths)} criativos...")
    print(f"   Account ID: {account_id}")
    print(f"   Ad Group ID: {ad_group_id}")
    print(f"   Final URL: {final_url}")
    
    try:
        ad_group_ad_service = client.get_service("AdGroupAdService")
        print("✅ Serviço AdGroupAdService obtido")
    except Exception as e:
        print(f"❌ Erro ao obter serviço AdGroupAdService: {e}")
        return
    
    success_count = 0
    error_count = 0
    
    for idx, creative_path in enumerate(creative_paths, 1):
        try:
            print(f"\n📤 Enviando criativo {idx}/{len(creative_paths)}: {os.path.basename(creative_path)}")
            
            # Verifica se o arquivo existe
            if not os.path.exists(creative_path):
                print(f"   ❌ Arquivo não encontrado: {creative_path}")
                error_count += 1
                continue
            
            # Lê o arquivo
            with open(creative_path, "rb") as f:
                image_data = f.read()
            print(f"   ✅ Arquivo lido: {len(image_data)} bytes")
            
            # Cria a operação
            ad_operation = client.get_type("AdGroupAdOperation")
            ad = ad_operation.create
            ad.ad_group = f"customers/{account_id}/adGroups/{ad_group_id}"
            ad.status = client.enums.AdGroupAdStatusEnum.ENABLED
            
            # Configura o anúncio de imagem
            image_ad = ad.ad.image_ad
            image_ad.data = image_data
            
            # Define o tipo MIME
            ext = os.path.splitext(creative_path)[1].lower()
            if ext == ".gif":
                image_ad.mime_type = client.enums.MimeTypeEnum.IMAGE_GIF
            else:
                image_ad.mime_type = client.enums.MimeTypeEnum.IMAGE_PNG
            
            # Configura URLs
            ad.ad.final_urls.append(final_url)
            ad.ad.display_url = final_url.split("://")[-1]
            ad.ad.name = os.path.splitext(os.path.basename(creative_path))[0]
            
            print(f"   📤 Enviando para Google Ads...")
            
            # Faz o upload (sem fazer_requisicao_liberada para evitar problemas)
            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=account_id,
                operations=[ad_operation]
            )
            
            if response and response.results:
                for result in response.results:
                    print(f"   ✅ Criativo enviado com sucesso: {result.resource_name}")
                    success_count += 1
            else:
                print(f"   ⚠️ Resposta vazia do Google Ads")
                error_count += 1
                
        except Exception as ex:
            print(f"   ❌ Erro ao enviar o criativo {os.path.basename(creative_path)}: {ex}")
            error_count += 1
    
    print(f"\n📊 Resultado do Upload:")
    print(f"   ✅ Sucessos: {success_count}")
    print(f"   ❌ Erros: {error_count}")
    
    if success_count > 0:
        print(f"🎉 {success_count} criativo(s) enviado(s) com sucesso!")
    else:
        print(f"❌ Nenhum criativo foi enviado com sucesso.")

def show_notification(title, message, duration=15):
    """Cross-platform notification function"""
    try:
        if toaster:  # Windows
            toaster.show_toast(title, message, duration=duration, threaded=True)
        else:  # Linux/Mac
            system = platform.system().lower()
            if system == 'linux':
                subprocess.run(['notify-send', title, message], check=False)
            elif system == 'darwin':  # macOS
                subprocess.run(['osascript', '-e', f'display notification "{message}" with title "{title}"'], check=False)
            else:
                print(f"📱 {title}: {message}")
    except Exception as e:
        print(f"📱 {title}: {message}")  # Fallback to console print

# ------------------------ FUNÇÃO INTERATIVA (CASO NÃO SEJAM PASSADOS PARÂMETROS) ------------------------
def main_interativo():
    df = ler_planilha()
    if df is None or df.empty:
        print("Nenhuma campanha encontrada na planilha.")
        exit(1)
    
    pais_selecionado = input("Digite o(s) país(es) para subir os criativos (separados por vírgula, ou 'all' para todos os países): ").strip()
    
    if pais_selecionado.lower() == "all":
        df_filtrado = df
    else:
        paises = [p.strip() for p in pais_selecionado.split(",") if p.strip()]
        df_filtrado = pd.DataFrame()
        for pais in paises:
            df_pais = df[df["País"].str.contains(pais, case=False, na=False)]
            if df_pais.empty:
                print(f"⚠️ Nenhuma campanha encontrada para o país: {pais}")
            else:
                df_filtrado = pd.concat([df_filtrado, df_pais])
        
        if df_filtrado.empty:
            print("❌ Nenhuma campanha encontrada para os países informados.")
            exit(1)
        
        df_filtrado = df_filtrado.drop_duplicates()
    
    print("Campanhas encontradas:")
    campanhas_unicas = df_filtrado["Campanha"].unique()
    for campanha in campanhas_unicas:
        print(f" - {campanha}")
    
    campanhas_input = input("Digite as campanhas que deseja processar (separadas por vírgula, 'all' para todas ou 'all T1', 'all T2', etc.): ").strip()
    if campanhas_input.lower() == "all":
        df_final = df_filtrado
        tag = None
    else:
        campanhas_escolhidas = [c.strip() for c in campanhas_input.split(",") if c.strip()]
        df_final = pd.DataFrame()
        tag = None
        for item in campanhas_escolhidas:
            if item.lower().startswith("all "):
                tag = item[4:].strip().upper()
                pattern = re.escape(f"[ - {tag} - ]")
                df_filtered = df_filtrado[df_filtrado["Campanha"].str.contains(pattern, case=False, na=False)]
                df_final = pd.concat([df_final, df_filtered])
            else:
                df_filtered = df_filtrado[df_filtrado["Campanha"] == item]
                df_final = pd.concat([df_final, df_filtered])
        df_final = df_final.drop_duplicates()
        if df_final.empty:
            print("❌ Nenhuma campanha corresponde à seleção.")
            exit(1)
    
    usar_mesmas_config = False
    config_global = {}
    if len(df_final) > 1:
        resposta_global = input("Deseja usar a mesma configuração de criativos para todas as campanhas? (S/N): ").strip().lower()
        if resposta_global == "s":
            usar_mesmas_config = True
            opcao_global = input("Deseja gerar criativos aleatórios ou específicos? (A/E): ").strip().lower()
            if opcao_global == "e":
                templates_especificos_global = input("Digite os nomes dos templates específicos (separados por vírgula): ").strip().split(",")
                templates_especificos_global = [t.strip() for t in templates_especificos_global if t.strip()]
            else:
                templates_especificos_global = None
            qtd_input_global = input("Quantos criativos deseja gerar para todas as campanhas? (Digite um número ou 'all'): ").strip()
            quantidade_global = "all" if qtd_input_global.lower() == "all" else int(qtd_input_global)
            config_global = {
                "opcao": opcao_global,
                "templates_especificos": templates_especificos_global,
                "quantidade": quantidade_global
            }
    
    client = GoogleAdsClient.load_from_storage("google-ads.yaml")
    processados = set()
    for idx, row in df_final.iterrows():
        try:
            # Remove hyphens from account ID and convert to string
            account_id = str(int(row["ID da Conta"].replace("-", "")))
            ad_group_id = str(int(row["ID do Grupo de Anúncios"]))
        except Exception as e:
            print(f"Erro ao converter IDs na linha {idx}: {e}")
            continue
        
        site = row["Site"]
        if (account_id, ad_group_id) in processados:
            print(f"⚠️ Criativos para a conta {account_id}, grupo {ad_group_id} já foram processados. Pulando...")
            continue
        processados.add((account_id, ad_group_id))
        
        logo_path = buscar_logo_por_site(site)
        if not logo_path:
            print(f"⚠️ Logo não encontrada para o site {site}. Pulando...")
            continue
        
        if not usar_mesmas_config:
            opcao = input("Deseja gerar criativos aleatórios ou específicos? (A/E): ").strip().lower()
            templates_especificos = None
            if opcao == "e":
                templates_especificos = input("Digite os nomes dos templates específicos (separados por vírgula): ").strip().split(",")
                templates_especificos = [t.strip() for t in templates_especificos if t.strip()]
            qtd_input = input(f"Quantos criativos deseja gerar para o site {site}? (Digite um número ou 'all'): ").strip()
            quantidade = "all" if qtd_input.lower() == "all" else int(qtd_input)
        else:
            opcao = config_global["opcao"]
            templates_especificos = config_global["templates_especificos"]
            quantidade = config_global["quantidade"]
        
        idioma = buscar_idioma_por_pais(row["País"])
        if not idioma:
            print(f"❌ Idioma não encontrado para o país {row['País']}. Pulando {site}.")
            continue
        
        criativos = gerar_criativos(site, idioma, quantidade, logo_path, templates_especificos, tag)
        if not criativos:
            print(f"❌ Nenhum criativo gerado para o site {site}.")
            continue
        
        final_url = get_existing_creatives(client, account_id, ad_group_id)
        if final_url:
            print(f"✅ URL final encontrada: {final_url}")
        else:
            print(f"⚠️ Nenhum criativo ativo encontrado para o site {site}.")
            final_url = input(f"Digite a URL final para o site {site}: ").strip()
        
        upload_creatives(client, account_id, ad_group_id, criativos, final_url)

# ------------------------ EXECUÇÃO PRINCIPAL ------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerar criativos automaticamente para campanha com menos de 8 criativos.")
    parser.add_argument("--account_id", type=str, help="ID da Conta do Google Ads")
    parser.add_argument("--ad_group_id", type=str, help="ID do Grupo de Anúncios")
    parser.add_argument("--site", type=str, help="Nome do Site ou Campanha")
    parser.add_argument("--quantity", type=str, help="Quantidade de criativos a serem gerados (número ou 'all')")
    args = parser.parse_args()

    if args.account_id and args.ad_group_id and args.site and args.quantity:
        # Remove hyphens from account ID
        account_id = args.account_id.replace("-", "")
        ad_group_id = args.ad_group_id
        site = args.site
        quantidade = args.quantity

        logo_path = buscar_logo_por_site(site)
        if not logo_path:
            print(f"⚠️ Logo não encontrada para o site {site}. Abortando.")
            exit(1)

        # Define o idioma padrão – para fluxo automático, pode ser ajustado conforme necessário
        idioma = "portuguese"

        criativos = gerar_criativos(site, idioma, quantidade, logo_path)
        if not criativos:
            print(f"❌ Nenhum criativo gerado para o site {site}. Abortando.")
            exit(1)

        client = GoogleAdsClient.load_from_storage("google-ads.yaml")
        final_url = get_existing_creatives(client, account_id, ad_group_id)
        if final_url:
            print(f"✅ URL final encontrada: {final_url}")
        else:
            print(f"⚠️ Nenhum criativo ativo encontrado para o site {site}.")
            final_url = input(f"Digite a URL final para o site {site}: ").strip()
            if not final_url:
                print("❌ URL final não fornecida. Abortando.")
                exit(1)

        upload_creatives(client, account_id, ad_group_id, criativos, final_url)
        
    else:
        main_interativo()

    if NOTIFICATION_AVAILABLE:
        show_notification(
            "Criativos Finalizados",
            "✅ Todos os criativos foram gerados e enviados com sucesso!"
        )
