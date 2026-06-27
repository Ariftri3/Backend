from flask import Blueprint, request, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required

emotion_bp = Blueprint('emotion', __name__)

# ============================================================
# POST /emotion — Simpan hasil deteksi emosi wajah
# Dipanggil dari layar "Deteksi" setiap kali model di Flutter
# selesai mengklasifikasi ekspresi wajah dari kamera.
# ============================================================
@emotion_bp.route('/emotion', methods=['POST'])
@token_required
def save_emotion(current_user_id):
    """
    Simpan satu hasil deteksi emosi.
    Header: Authorization: Bearer <token>
    Body JSON: { "emotion_label": "Bahagia", "confidence": 92.5 }
    """
    data           = request.json
    emotion_label  = data.get("emotion_label", "").strip()
    confidence     = data.get("confidence")

    if not emotion_label or confidence is None:
        return jsonify({
            "success": False,
            "message": "emotion_label dan confidence wajib diisi"
        }), 400

    conn, cursor = get_db()
    try:
        cursor.execute(
            "INSERT INTO emotion_detections (user_id, emotion_label, confidence) VALUES (%s, %s, %s) RETURNING id",
            (current_user_id, emotion_label, confidence)
        )
        emotion_id = cursor.fetchone()['id']
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Hasil deteksi emosi berhasil disimpan",
            "data": {
                "id": emotion_id,
                "emotion_label": emotion_label,
                "confidence": confidence
            }
        }), 201

    finally:
        cursor.close()
        release_db(conn)


# ============================================================
# GET /emotion — Ambil riwayat deteksi emosi
# ============================================================
@emotion_bp.route('/emotion', methods=['GET'])
@token_required
def get_emotions(current_user_id):
    """
    Ambil riwayat deteksi emosi user (default 20 terakhir).
    Header: Authorization: Bearer <token>
    Query param: ?limit=20
    """
    limit = int(request.args.get('limit', 20))

    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT id, emotion_label, confidence, created_at
            FROM emotion_detections
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (current_user_id, limit)
        )
        results = cursor.fetchall()

        for r in results:
            r['created_at'] = str(r['created_at'])

        return jsonify({"success": True, "data": results}), 200

    finally:
        cursor.close()
        release_db(conn)
