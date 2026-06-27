from flask import Blueprint, request, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

profile_bp = Blueprint('profile', __name__)

_supabase_admin = None


def _get_supabase_admin():
    """
    Client Supabase dengan service_role key — hanya dipakai untuk
    operasi admin seperti hapus akun (auth.admin.delete_user).
    JANGAN PERNAH kirim service_role key ini ke Flutter/client.
    """
    global _supabase_admin
    if _supabase_admin is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY belum diisi di .env."
            )
        _supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin


# ============================================================
# GET /profile — Ambil data profile user yang login
# ============================================================
@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    """
    Ambil informasi profile user yang login.
    Header: Authorization: Bearer <token>
    Response: { "success": true, "data": { "id": "...", "nama": "...", "email": "...", ... } }
    """
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT id, nama, email, foto_url, created_at
            FROM profiles
            WHERE id=%s
            """,
            (current_user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "User tidak ditemukan"}), 404

        user['created_at'] = str(user['created_at'])

        return jsonify({"success": True, "data": user}), 200

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# PUT /profile — Update data profile user
# ============================================================
@profile_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user_id):
    """
    Update profile user (nama dan foto).
    Header: Authorization: Bearer <token>
    Body JSON: { "nama": "Nama Baru", "foto_url": "https://..." }
    """
    data = request.json
    nama = data.get("nama", "").strip()
    foto_url = data.get("foto_url", "")

    if not nama:
        return jsonify({"success": False, "message": "Nama wajib diisi"}), 400

    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            UPDATE profiles
            SET nama=%s, foto_url=%s
            WHERE id=%s
            """,
            (nama, foto_url, current_user_id)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Profile berhasil diperbarui",
            "data": {
                "nama": nama,
                "foto_url": foto_url
            }
        }), 200

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# GET /profile/stats — Ambil statistik user
# ============================================================
@profile_bp.route('/profile/stats', methods=['GET'])
@token_required
def get_user_stats(current_user_id):
    """
    Ambil ringkasan statistik user (jumlah mood, jurnal, assessment).
    Header: Authorization: Bearer <token>
    """
    conn, cursor = get_db()
    try:
        cursor.execute(
            "SELECT COUNT(*) as count FROM mood_logs WHERE user_id=%s",
            (current_user_id,)
        )
        mood_count = cursor.fetchone()['count']

        cursor.execute(
            "SELECT COUNT(*) as count FROM journals WHERE user_id=%s",
            (current_user_id,)
        )
        journal_count = cursor.fetchone()['count']

        cursor.execute(
            "SELECT COUNT(*) as count FROM assessments WHERE user_id=%s",
            (current_user_id,)
        )
        assessment_count = cursor.fetchone()['count']

        cursor.execute(
            "SELECT COUNT(*) as count FROM chat_histories WHERE user_id=%s",
            (current_user_id,)
        )
        chat_count = cursor.fetchone()['count']

        return jsonify({
            "success": True,
            "data": {
                "mood_logs": mood_count,
                "journals": journal_count,
                "assessments": assessment_count,
                "chat_history": chat_count,
                "total_records": mood_count + journal_count + assessment_count + chat_count
            }
        }), 200

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# DELETE /profile — Hapus akun user
# ============================================================
@profile_bp.route('/profile', methods=['DELETE'])
@token_required
def delete_account(current_user_id):
    """
    Hapus akun user secara permanen.

    Bedanya dengan versi MySQL lama: sekarang yang dihapus adalah baris
    user di auth.users milik Supabase (lewat Admin API), bukan langsung
    di tabel biasa. Begitu auth.users terhapus, baris di `profiles` ikut
    terhapus otomatis (ON DELETE CASCADE), dan itu menyeret semua
    mood_logs, journals, assessments, chat_histories, emotion_detections
    milik user tersebut juga ikut terhapus.

    Header: Authorization: Bearer <token>
    """
    try:
        _get_supabase_admin().auth.admin.delete_user(current_user_id)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Gagal menghapus akun: {str(e)}"
        }), 500

    return jsonify({
        "success": True,
        "message": "Akun dan semua data berhasil dihapus"
    }), 200
