from flask import Blueprint, request, jsonify
from database import get_db
import bcrypt
import jwt
import datetime
from config import SECRET_KEY

auth_bp = Blueprint('auth', __name__)

# ============================================================
# POST /register — Daftar akun baru
# ============================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register user baru.
    Body JSON: { "nama": "...", "email": "...", "password": "..." }
    """
    data = request.json
    nama     = data.get("nama", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    # Validasi input
    if not nama or not email or not password:
        return jsonify({"success": False, "message": "Semua field wajib diisi"}), 400

    conn, cursor = get_db()
    try:
        # Cek apakah email sudah dipakai
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Email sudah digunakan"}), 409

        # Hash password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Simpan user baru
        cursor.execute(
            "INSERT INTO users (nama, email, password) VALUES (%s, %s, %s)",
            (nama, email, hashed.decode('utf-8'))
        )
        conn.commit()

        return jsonify({"success": True, "message": "Registrasi berhasil"}), 201

    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /login — Masuk akun
# ============================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user.
    Body JSON: { "email": "...", "password": "..." }
    Response: { "success": true, "token": "...", "user": {...} }
    """
    data     = request.json
    email    = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email dan password wajib diisi"}), 400

    conn, cursor = get_db()
    try:
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "Email tidak ditemukan"}), 401

        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({"success": False, "message": "Password salah"}), 401

        # Buat JWT token (berlaku 7 hari)
        token = jwt.encode(
            {
                "user_id": user["id"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "success": True,
            "message": "Login berhasil",
            "token": token,
            "user": {
                "id":    user["id"],
                "nama":  user["nama"],
                "email": user["email"],
                "foto_url": user.get("foto_url")
            }
        }), 200

    finally:
        cursor.close()
        conn.close()


# ============================================================
# POST /login/google — Login/Register otomatis via Google
# ============================================================
@auth_bp.route('/login/google', methods=['POST'])
def login_google():
    """
    Login/Register otomatis via Google.
    Body JSON: { "email": "...", "nama": "...", "foto_url": "..." }
    """
    data     = request.json
    email    = data.get("email", "").strip()
    nama     = data.get("nama", "").strip()
    foto_url = data.get("foto_url", "").strip()

    if not email or not nama:
        return jsonify({"success": False, "message": "Email dan nama wajib diisi"}), 400

    conn, cursor = get_db()
    try:
        # Cek apakah user sudah terdaftar di MySQL
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            # Jika belum terdaftar, buat akun secara otomatis
            cursor.execute(
                "INSERT INTO users (nama, email, password, foto_url) VALUES (%s, %s, %s, %s)",
                (nama, email, "GOOGLE_AUTH_NO_PASSWORD", foto_url)
            )
            conn.commit()

            # Ambil kembali data user yang baru dibuat
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

        # Buat JWT token (berlaku 7 hari)
        token = jwt.encode(
            {
                "user_id": user["id"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
            },
            SECRET_KEY,
            algorithm="HS256"
        )

        return jsonify({
            "success": True,
            "message": "Login Google berhasil",
            "token": token,
            "user": {
                "id":    user["id"],
                "nama":  user["nama"],
                "email": user["email"],
                "foto_url": user.get("foto_url")
            }
        }), 200

    finally:
        cursor.close()
        conn.close()