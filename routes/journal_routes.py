from flask import Blueprint, request, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required

journal_bp = Blueprint('journal', __name__)


# ============================================================
# Kamus rekomendasi kegiatan anti-stres berbasis kata kunci
# Pola sama seperti chatbot_routes.py (rule-based), supaya
# konsisten dengan arsitektur yang sudah ada.
# Bisa diganti API AI (OpenAI/Gemini) nantinya jika perlu.
# ============================================================
STRESS_ACTIVITY_MAP = {
    "cemas": {
        "label": "Cemas",
        "keywords": ["cemas", "khawatir", "gelisah", "deg-degan", "takut", "panik"],
        "activities": [
            "Latihan napas 4-4-4: tarik napas 4 detik, tahan 4 detik, embuskan 4 detik",
            "Jalan kaki santai 10 menit di luar ruangan",
            "Tulis 3 hal yang masih bisa kamu kendalikan saat ini",
        ],
    },
    "stres": {
        "label": "Stres / Tertekan",
        "keywords": ["stres", "stress", "tertekan", "deadline", "numpuk", "beban", "overwhelmed"],
        "activities": [
            "Istirahat 10-15 menit tanpa gadget",
            "Buat daftar prioritas, kerjakan satu per satu",
            "Dengarkan musik instrumental yang menenangkan",
        ],
    },
    "lelah": {
        "label": "Lelah",
        "keywords": ["lelah", "capek", "cape", "ngantuk", "kecapean", "burnout", "ngos-ngosan"],
        "activities": [
            "Tidur lebih awal malam ini",
            "Peregangan ringan selama 5 menit",
            "Minum air putih yang cukup dan kurangi kafein",
        ],
    },
    "sedih": {
        "label": "Sedih",
        "keywords": ["sedih", "kecewa", "nangis", "menangis", "patah hati", "down", "galau"],
        "activities": [
            "Tulis perasaanmu lebih lanjut di jurnal, ini sudah langkah bagus",
            "Hubungi teman atau keluarga yang kamu percaya",
            "Tonton atau dengarkan sesuatu yang menenangkan",
        ],
    },
    "marah": {
        "label": "Marah / Kesal",
        "keywords": ["marah", "kesal", "emosi", "jengkel", "benci", "sebal"],
        "activities": [
            "Jauh sejenak dari situasi yang memicu, beri jeda untuk diri sendiri",
            "Olahraga ringan untuk melepas energi negatif",
            "Tulis apa yang membuatmu marah, baca ulang setelah lebih tenang",
        ],
    },
    "kesepian": {
        "label": "Kesepian",
        "keywords": ["sendiri", "kesepian", "sepi", "tidak ada teman", "kosong"],
        "activities": [
            "Hubungi satu orang yang sudah lama tidak kamu sapa",
            "Ikut komunitas atau aktivitas sosial ringan",
            "Lakukan hobi yang kamu suka, seperti menggambar atau membaca",
        ],
    },
}

DEFAULT_ACTIVITIES = {
    "label": "Umum",
    "activities": [
        "Luangkan 10 menit untuk diam dan bernapas tenang",
        "Lakukan aktivitas fisik ringan, seperti jalan kaki",
        "Konsisten menulis jurnal membantu kamu memahami emosi sendiri",
    ],
}


def get_stress_recommendations(content: str, max_categories: int = 2):
    """
    Cocokkan isi jurnal dengan kata kunci yang ada, lalu kembalikan
    daftar rekomendasi kegiatan anti-stres yang relevan.
    Kalau tidak ada kata kunci yang cocok, kembalikan rekomendasi umum.
    """
    text = (content or "").lower()
    matched = []

    for info in STRESS_ACTIVITY_MAP.values():
        if any(kw in text for kw in info["keywords"]):
            matched.append({
                "kategori": info["label"],
                "kegiatan": info["activities"],
            })
        if len(matched) >= max_categories:
            break

    if not matched:
        matched.append({
            "kategori": DEFAULT_ACTIVITIES["label"],
            "kegiatan": DEFAULT_ACTIVITIES["activities"],
        })

    return matched


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
            "data": {"id": journal_id},
            "recommendations": get_stress_recommendations(content)
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
        # Pastikan jurnal milik user ini
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

        return jsonify({
            "success": True,
            "message": "Jurnal berhasil diperbarui",
            "recommendations": get_stress_recommendations(content)
        }), 200

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