from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from routes.mood_routes       import mood_bp
from routes.journal_routes    import journal_bp
from routes.assessment_routes import assessment_bp
from routes.chatbot_routes    import chatbot_bp
from routes.profile_routes    import profile_bp
from routes.emotion_routes    import emotion_bp

app = Flask(__name__)
CORS(app)  # Izinkan semua origin (Flutter web/mobile)

# ============================================================
# CATATAN MIGRASI SUPABASE
# ------------------------------------------------------------
# Blueprint 'auth' (register/login/login-google) yang dulu ada
# di sini SUDAH DIHAPUS. Login & register sekarang ditangani
# LANGSUNG oleh Supabase Auth dari sisi Flutter (email+password,
# Google OAuth, dan OTP) — Flask tidak lagi menerbitkan token.
#
# Flask di sini cuma jadi API untuk data aplikasi (mood, journal,
# assessment, chatbot, profile, emotion) dan memverifikasi token
# Supabase yang dikirim Flutter lewat @token_required.
# ============================================================

# ============================================================
# Swagger — Dokumentasi API otomatis
# Akses di: http://localhost:5000/apidocs
# ============================================================
swagger_config = {
    "headers": [],
    "specs": [{
        "endpoint": "apispec",
        "route":    "/apispec.json",
        "rule_filter": lambda rule: True,
        "model_filter": lambda tag: True,
    }],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs"
}

swagger_template = {
    "info": {
        "title":       "MindCare API",
        "description": "API untuk aplikasi kesehatan mental MindCare (data layer di atas Supabase)",
        "version":     "2.0.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in":   "header",
            "description": "Masukkan token Supabase: Bearer <access_token>"
        }
    }
}

Swagger(app, config=swagger_config, template=swagger_template)

# ============================================================
# Register semua Blueprint (kelompok route)
# ============================================================
app.register_blueprint(mood_bp)
app.register_blueprint(journal_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(emotion_bp)

# ============================================================
# Route utama — health check
# ============================================================
@app.route("/")
def home():
    return {
        "success": True,
        "message": "MindCare API Berjalan ✅ (Supabase backend)",
        "endpoints": {
            "docs":       "/apidocs",
            "auth":       "Ditangani langsung oleh Supabase Auth dari Flutter (bukan endpoint Flask lagi)",
            "mood":       ["/mood (GET, POST)", "/mood/<id> (PUT, DELETE)"],
            "journal":    ["/journal (GET, POST)", "/journal/<id> (PUT, DELETE)"],
            "assessment": ["/assessment (GET, POST)"],
            "chatbot":    ["/chatbot (POST)", "/chatbot/history (GET)"],
            "profile":    ["/profile (GET, PUT, DELETE)", "/profile/stats (GET)"],
            "emotion":    ["/emotion (GET, POST)"]
        }
    }

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
