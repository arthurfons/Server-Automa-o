import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class with environment variables and defaults"""
    
    # Google Sheets Configuration
    SHEET_ID = os.getenv("SHEET_ID", "1QQ7_ByU8siGV_NAMXM-fWiEt60fyPOJp0h-RshNsFeg")
    SHEET_RANGE = os.getenv("SHEET_RANGE", "Página1!A:F")
    
    # Google Drive Folder IDs
    TEMPLATES_DRIVE_FOLDER_ID = os.getenv("TEMPLATES_DRIVE_FOLDER_ID", "1LElWu5TVRw9Xbzhgm1wm58pv0u3pVgMl")
    LOGOS_DRIVE_FOLDER_ID = os.getenv("LOGOS_DRIVE_FOLDER_ID", "1cVRl4kUOltDLxnMYLiVFe69MAHI8KnrL")
    
    # Credentials Files
    DRIVE_CREDENTIALS_FILE = os.getenv("DRIVE_CREDENTIALS_FILE", "drive_credentials.json")
    SHEETS_CREDENTIALS_FILE = os.getenv("SHEETS_CREDENTIALS_FILE", "sheets_credentials.json")
    GOOGLE_ADS_YAML = os.getenv("GOOGLE_ADS_YAML", "google-ads.yaml")
    
    # Environment Variables for Railway
    GOOGLE_ADS_YAML_CONTENT = os.getenv("GOOGLE_ADS_YAML")
    DRIVE_CREDENTIALS_CONTENT = os.getenv("DRIVE_CREDENTIALS")
    SHEETS_CREDENTIALS_CONTENT = os.getenv("SHEETS_CREDENTIALS")
    
    # Image Configuration
    IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "336"))
    IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "280"))
    LOGO_WIDTH = int(os.getenv("LOGO_WIDTH", "45"))
    LOGO_HEIGHT = int(os.getenv("LOGO_HEIGHT", "14"))
    
    # Request Limits
    MAX_REQUESTS = int(os.getenv("MAX_REQUESTS", "3000"))
    
    # Directories
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
    TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", "templates")
    LOGOS_DIR = os.getenv("LOGOS_DIR", "logos")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    
    @property
    def DIMENSOES(self):
        return (self.IMAGE_WIDTH, self.IMAGE_HEIGHT)
    
    @property
    def LOGO_SIZE(self):
        return (self.LOGO_WIDTH, self.LOGO_HEIGHT)

# Language mapping by country
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

# Global config instance
config = Config() 