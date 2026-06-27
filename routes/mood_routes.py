from flask import Blueprint, request, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required

mood_bp = Blueprint('mood', __name__)

MOOD_LABELS = {
    1: 'Sangat Buruk',
    2: 'Buruk',
    3: 'Biasa',
    4: 'Baik',
    5: 'Sangat Baik'
}

# ============================================================
# POST /mood — Simpan mood hari ini
# ============================================================
@mood_bp.route('/mood', methods=['POST'])
@token_required
def add_mood(current_user_id):
    """
    Simpan mood harian.
    Header: Authorization: Bearer <token>
    Body JSON: { "mood_value": 4, "catatan": "Hari yang menyenangkan" }
    """
    data        = request.json
    mood_value  = data.get("mood_value")
    catatan     = data.get("catatan", "")

    if mood_value is None or not (1 <= int(mood_value) <= 5):
        return jsonify({"success": False, "message": "mood_value harus antara 1-5"}), 400

    mood_label = MOOD_LABELS.get(int(mood_value), 'Biasa')

    conn, cursor = get_db()
    try:
        cursor.execute(
            "INSERT INTO mood_logs (user_id, mood_value, mood_label, catatan) VALUES (%s, %s, %s, %s)",
            (current_user_id, mood_value, mood_label, catatan)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Mood berhasil disimpan",
            "data": {
                "mood_value": mood_value,
                "mood_label": mood_label
            }
        }), 201

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# GET /mood — Ambil riwayat mood (untuk dashboard & statistik)
# ============================================================
@mood_bp.route('/mood', methods=['GET'])
@token_required
def get_moods(current_user_id):
    """
    Ambil data mood user (default 7 hari terakhir).
    Header: Authorization: Bearer <token>
    Query param: ?limit=7
    """
    limit = int(request.args.get('limit', 7))

    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT id, mood_value, mood_label, catatan, created_at
            FROM mood_logs
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (current_user_id, limit)
        )
        moods = cursor.fetchall()

        for m in moods:
            m['created_at'] = str(m['created_at'])

        return jsonify({
            "success": True,
            "data": moods
        }), 200

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# PUT /mood/<id> — Update catatan mood
# ============================================================
@mood_bp.route('/mood/<int:mood_id>', methods=['PUT'])
@token_required
def update_mood(current_user_id, mood_id):
    """
    Update catatan mood yang sudah ada.
    Header: Authorization: Bearer <token>
    Body JSON: { "mood_value": 4, "catatan": "..." }
    """
    data = request.json
    mood_value = data.get("mood_value")
    catatan = data.get("catatan", "")

    if mood_value is None or not (1 <= int(mood_value) <= 5):
        return jsonify({"success": False, "message": "mood_value harus antara 1-5"}), 400

    mood_label = MOOD_LABELS.get(int(mood_value), 'Biasa')

    conn, cursor = get_db()
    try:
        cursor.execute(
            "SELECT id FROM mood_logs WHERE id=%s AND user_id=%s",
            (mood_id, current_user_id)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Mood tidak ditemukan"}), 404

        cursor.execute(
            "UPDATE mood_logs SET mood_value=%s, mood_label=%s, catatan=%s WHERE id=%s",
            (mood_value, mood_label, catatan, mood_id)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Mood berhasil diperbarui",
            "data": {
                "mood_value": mood_value,
                "mood_label": mood_label
            }
        }), 200

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# DELETE /mood/<id> — Hapus entry mood
# ============================================================
@mood_bp.route('/mood/<int:mood_id>', methods=['DELETE'])
@token_required
def delete_mood(current_user_id, mood_id):
    """
    Hapus entry mood berdasarkan ID.
    Header: Authorization: Bearer <token>
    """
    conn, cursor = get_db()
    try:
        cursor.execute(
            "SELECT id FROM mood_logs WHERE id=%s AND user_id=%s",
            (mood_id, current_user_id)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Mood tidak ditemukan"}), 404

        cursor.execute("DELETE FROM mood_logs WHERE id=%s", (mood_id,))
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Mood berhasil dihapus"
        }), 200

    finally:
        cursor.close()
        release_db(conn)
