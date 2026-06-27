from flask import Blueprint, request, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required

journal_bp = Blueprint('journal', __name__)

# ============================================================
# GET /journal — Ambil semua jurnal milik user
# ============================================================
@journal_bp.route('/journal', methods=['GET'])
@token_required
def get_journals(current_user_id):
    """
    Ambil semua jurnal milik user yang login.
    Header: Authorization: Bearer <token>
    """
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT id, title, content, mood, created_at, updated_at
            FROM journals
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (current_user_id,)
        )
        journals = cursor.fetchall()

        for j in journals:
            j['created_at'] = str(j['created_at'])
            j['updated_at'] = str(j['updated_at'])

        return jsonify({"success": True, "data": journals}), 200

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# POST /journal — Buat jurnal baru
# ============================================================
@journal_bp.route('/journal', methods=['POST'])
@token_required
def create_journal(current_user_id):
    """
    Tambah entri jurnal baru.
    Header: Authorization: Bearer <token>
    Body JSON: { "title": "...", "content": "...", "mood": "Baik" }
    """
    data    = request.json
    title   = data.get("title", "").strip()
    content = data.get("content", "").strip()
    mood    = data.get("mood", "")

    if not title or not content:
        return jsonify({"success": False, "message": "Judul dan isi wajib diisi"}), 400

    conn, cursor = get_db()
    try:
        # psycopg2 (Postgres) tidak punya cursor.lastrowid seperti mysql-connector,
        # jadi ambil id baru langsung lewat RETURNING.
        cursor.execute(
            "INSERT INTO journals (user_id, title, content, mood) VALUES (%s, %s, %s, %s) RETURNING id",
            (current_user_id, title, content, mood)
        )
        journal_id = cursor.fetchone()['id']
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Jurnal berhasil disimpan",
            "data": {"id": journal_id}
        }), 201

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# PUT /journal/<id> — Edit jurnal
# ============================================================
@journal_bp.route('/journal/<int:journal_id>', methods=['PUT'])
@token_required
def update_journal(current_user_id, journal_id):
    """
    Edit jurnal berdasarkan ID.
    Header: Authorization: Bearer <token>
    Body JSON: { "title": "...", "content": "...", "mood": "..." }
    """
    data    = request.json
    title   = data.get("title", "").strip()
    content = data.get("content", "").strip()
    mood    = data.get("mood", "")

    conn, cursor = get_db()
    try:
        cursor.execute(
            "SELECT id FROM journals WHERE id=%s AND user_id=%s",
            (journal_id, current_user_id)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Jurnal tidak ditemukan"}), 404

        cursor.execute(
            "UPDATE journals SET title=%s, content=%s, mood=%s WHERE id=%s",
            (title, content, mood, journal_id)
        )
        conn.commit()

        return jsonify({"success": True, "message": "Jurnal berhasil diperbarui"}), 200

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# DELETE /journal/<id> — Hapus jurnal
# ============================================================
@journal_bp.route('/journal/<int:journal_id>', methods=['DELETE'])
@token_required
def delete_journal(current_user_id, journal_id):
    """
    Hapus jurnal berdasarkan ID.
    Header: Authorization: Bearer <token>
    """
    conn, cursor = get_db()
    try:
        cursor.execute(
            "SELECT id FROM journals WHERE id=%s AND user_id=%s",
            (journal_id, current_user_id)
        )
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Jurnal tidak ditemukan"}), 404

        cursor.execute("DELETE FROM journals WHERE id=%s", (journal_id,))
        conn.commit()

        return jsonify({"success": True, "message": "Jurnal berhasil dihapus"}), 200

    finally:
        cursor.close()
        release_db(conn)
