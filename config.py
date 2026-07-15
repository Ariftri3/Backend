import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / ".env"

if DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)

# ============================================================
# Supabase project settings
# Semua nilai ini diambil dari: Supabase Dashboard > Settings > API
# dan Settings > Database
# ============================================================

# Project URL & anon/service key (dipakai untuk verifikasi token & admin ops)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Connection string Postgres langsung (Settings > Database > Connection string > URI)
# Pakai mode "Session pooler" supaya stabil dipakai dari Flask.
DATABASE_URL = os.getenv("DATABASE_URL", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://arkan:mood123@cluster0.wrgqjch.mongodb.net/?appName=Cluster0")

print("========== CONFIG ==========")
print("SUPABASE_URL =", SUPABASE_URL)
print("SUPABASE_ANON_KEY =", SUPABASE_ANON_KEY)
print("============================")
