from flask import Blueprint, request, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required

assessment_bp = Blueprint('assessment', __name__)

def get_level(score):
    """Tentukan level kesehatan mental berdasarkan skor 0-100."""
    if score >= 75:
        return "Baik"
    elif score >= 50:
        return "Sedang"
    else:
        return "Perlu Perhatian"

# ============================================================
# POST /assessment — Simpan hasil assessment
# ============================================================
@assessment_bp.route('/assessment', methods=['POST'])
@token_required
def save_assessment(current_user_id):
    """
    Simpan hasil assessment user.
    Header: Authorization: Bearer <token>
    Body JSON: { "score": 75 }
    """
    data  = request.json
    score = data.get("score")

    if score is None or not (0 <= int(score) <= 100):
        return jsonify({"success": False, "message": "Score harus antara 0-100"}), 400

    level = get_level(int(score))

    conn, cursor = get_db()
    try:
        cursor.execute(
            "INSERT INTO assessments (user_id, score, level) VALUES (%s, %s, %s)",
            (current_user_id, score, level)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Hasil assessment berhasil disimpan",
            "data": {
                "score": score,
                "level": level
            }
        }), 201

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# GET /assessment — Ambil riwayat assessment
# ============================================================
@assessment_bp.route('/assessment', methods=['GET'])
@token_required
def get_assessments(current_user_id):
    """
    Ambil riwayat assessment user.
    Header: Authorization: Bearer <token>
    """
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT id, score, level, created_at
            FROM assessments
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (current_user_id,)
        )
        results = cursor.fetchall()

        for r in results:
            r['created_at'] = str(r['created_at'])

        return jsonify({"success": True, "data": results}), 200

    finally:
        cursor.close()
        release_db(conn)
