from flask import Blueprint, request, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required
import random

chatbot_bp = Blueprint('chatbot', __name__)

# ============================================================
# Kamus respons chatbot berbasis kata kunci (rule-based)
# Bisa diganti dengan API AI (OpenAI/Gemini) nantinya
# ============================================================
RESPONSES = {
    "sedih": [
        "Aku mengerti perasaanmu. Wajar untuk merasa sedih, ini bagian dari proses. Apakah ada sesuatu yang ingin kamu ceritakan?",
        "Rasa sedih itu valid. Cobalah untuk tidak menyalahkan diri sendiri ya. Aku di sini mendengarkanmu.",
    ],
    "cemas": [
        "Kecemasan memang berat. Coba tarik napas dalam-dalam: hirup 4 detik, tahan 4 detik, hembuskan 4 detik.",
        "Saat cemas, fokus pada hal-hal yang bisa kamu kendalikan sekarang. Satu langkah kecil sudah cukup.",
    ],
    "stress": [
        "Stres adalah sinyal tubuhmu untuk beristirahat. Sudahkah kamu minum air dan meregangkan tubuh hari ini?",
        "Coba luangkan 10 menit untuk relaksasi. Musik pelan atau jalan-jalan singkat bisa sangat membantu.",
    ],
    "lelah": [
        "Kelelahan fisik dan mental itu nyata. Penting untuk memberi dirimu izin untuk istirahat.",
        "Tubuh dan pikiranmu butuh pemulihan. Tidur yang cukup adalah salah satu perawatan diri terpenting.",
    ],
    "bahagia": [
        "Senang mendengar kamu bahagia! Perasaan positif seperti ini patut disyukuri dan dirayakan.",
        "Bagus sekali! Catat momen bahagia ini supaya kamu bisa mengingatnya di hari-hari yang lebih berat.",
    ],
    "marah": [
        "Marah adalah emosi yang normal. Coba ekspresikan dengan cara yang sehat, seperti menulis jurnal.",
        "Saat marah, cobalah menjauh sejenak dari situasi itu dan berikan dirimu waktu untuk tenang.",
    ],
    "default": [
        "Terima kasih sudah berbagi. Aku selalu di sini untuk mendengarkan.",
        "Perasaanmu penting. Ceritakan lebih lanjut jika kamu mau, aku siap mendengarkan.",
        "Aku memahami situasimu. Ingat, kamu tidak sendirian dalam perjalanan ini.",
        "Satu langkah kecil setiap hari sudah merupakan pencapaian yang luar biasa.",
    ]
}

def get_reply(message: str) -> str:
    """Cari respons berdasarkan kata kunci dalam pesan."""
    message_lower = message.lower()
    for keyword, replies in RESPONSES.items():
        if keyword in message_lower:
            return random.choice(replies)
    return random.choice(RESPONSES["default"])


# ============================================================
# POST /chatbot — Kirim pesan dan dapatkan balasan
# ============================================================
@chatbot_bp.route('/chatbot', methods=['POST'])
@token_required
def chat(current_user_id):
    """
    Kirim pesan ke chatbot dan dapatkan balasan.
    Header: Authorization: Bearer <token>
    Body JSON: { "message": "Aku merasa sedih hari ini" }
    """
    data    = request.json
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"success": False, "message": "Pesan tidak boleh kosong"}), 400

    reply = get_reply(message)

    conn, cursor = get_db()
    try:
        cursor.execute(
            "INSERT INTO chat_histories (user_id, message, reply) VALUES (%s, %s, %s)",
            (current_user_id, message, reply)
        )
        conn.commit()
    finally:
        cursor.close()
        release_db(conn)

    return jsonify({
        "success": True,
        "data": {
            "message": message,
            "reply":   reply
        }
    }), 200


# ============================================================
# GET /chatbot/history — Ambil riwayat chat
# ============================================================
@chatbot_bp.route('/chatbot/history', methods=['GET'])
@token_required
def get_history(current_user_id):
    """
    Ambil riwayat percakapan chatbot.
    Header: Authorization: Bearer <token>
    """
    conn, cursor = get_db()
    try:
        cursor.execute(
            """
            SELECT id, message, reply, created_at
            FROM chat_histories
            WHERE user_id = %s
            ORDER BY created_at ASC
            LIMIT 50
            """,
            (current_user_id,)
        )
        history = cursor.fetchall()
        for h in history:
            h['created_at'] = str(h['created_at'])

        return jsonify({"success": True, "data": history}), 200

    finally:
        cursor.close()
        release_db(conn)
