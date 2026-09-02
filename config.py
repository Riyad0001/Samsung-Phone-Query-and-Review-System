import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'samsung_phones.db')}")

# Scraper
SCRAPE_TARGET_COUNT = 15
SAMSUNG_PHONES = [
    "https://www.gsmarena.com/samsung_galaxy_s24_ultra-12772.php",
    "https://www.gsmarena.com/samsung_galaxy_s24_plus-12773.php",
    "https://www.gsmarena.com/samsung_galaxy_s24-12774.php",
    "https://www.gsmarena.com/samsung_galaxy_s23_ultra-12168.php",
    "https://www.gsmarena.com/samsung_galaxy_s23_plus-12169.php",
    "https://www.gsmarena.com/samsung_galaxy_s23-12170.php",
    "https://www.gsmarena.com/samsung_galaxy_s22_ultra_5g-11416.php",
    "https://www.gsmarena.com/samsung_galaxy_s22_plus_5g-11418.php",
    "https://www.gsmarena.com/samsung_galaxy_s22_5g-11417.php",
    "https://www.gsmarena.com/samsung_galaxy_s21_ultra_5g-10621.php",
    "https://www.gsmarena.com/samsung_galaxy_s21_plus_5g-10622.php",
    "https://www.gsmarena.com/samsung_galaxy_s21_5g-10556.php",
    "https://www.gsmarena.com/samsung_galaxy_a54_5g-12067.php",
    "https://www.gsmarena.com/samsung_galaxy_a34_5g-12068.php",
    "https://www.gsmarena.com/samsung_galaxy_z_fold5-11273.php",
]

# HuggingFace model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "google/flan-t5-small"
# LLM_MODEL = "microsoft/phi-2"  # alternative

# API
API_HOST = "0.0.0.0"
API_PORT = 8888