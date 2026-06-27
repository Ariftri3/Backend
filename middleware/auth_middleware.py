from functools import wraps
from flask import request, jsonify
from supabase import create_client

from config import SUPABASE_URL, SUPABASE_ANON_KEY

_supabase = None


def _get_supabase():
    """Lazy init Supabase client (dipakai cuma untuk verifikasi token)."""
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_ANON_KEY belum diisi di .env."
            )
        _supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase


def token_required(f):
    """
    Dekorator untuk proteksi endpoint dengan token Supabase.

    Bedanya dengan versi lama: token sekarang DIKELUARKAN OLEH SUPABASE
    (hasil login email/password, Google, atau OTP dari Flutter), bukan
    diterbitkan sendiri oleh Flask. Flask di sini cuma memverifikasi
    token itu masih valid lewat Supabase, lalu ambil user id (UUID)-nya.

    Cara pakai di route (sama persis seperti sebelumnya):

        @app.route('/contoh')
        @token_required
        def contoh(current_user_id):
            return jsonify({"user_id": current_user_id})

    Flutter tetap kirim header yang sama:
        Authorization: Bearer <token>
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({
                "success": False,
                "message": "Token tidak ditemukan. Harap login terlebih dahulu."
            }), 401

        try:
            response = _get_supabase().auth.get_user(token)
            user = response.user if response else None
        except Exception:
            user = None

        if not user:
            return jsonify({
                "success": False,
                "message": "Token tidak valid atau sudah kadaluarsa. Silakan login ulang."
            }), 401

        current_user_id = user.id  # UUID string

        return f(current_user_id, *args, **kwargs)

    return decorated
