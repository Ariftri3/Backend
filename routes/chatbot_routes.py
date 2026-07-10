from flask import Blueprint, request, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required

import os
from dotenv import load_dotenv
from google import genai

chatbot_bp = Blueprint('chatbot', __name__)

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")

def get_reply(message: str) -> str:

    prompt = f"""
Kamu adalah MindCare AI, asisten kesehatan mental pada aplikasi MindCare.

Tugasmu:
- Membantu pengguna mengenali mood harian.
- Memberikan dukungan emosional yang hangat.
- Berikan saran sederhana yang aman.
- Jangan memberikan diagnosis psikologis.
- Jangan menyebut pengguna mengalami depresi, bipolar, PTSD, atau gangguan mental lainnya.
- Jika pengguna menunjukkan tanda ingin menyakiti diri sendiri atau orang lain, sarankan segera menghubungi psikolog, keluarga, atau layanan darurat setempat.
- Jawab menggunakan Bahasa Indonesia yang sopan dan mudah dipahami.
- Jawaban maksimal sekitar 150 kata.

Pesan pengguna:

{message}
"""

    response = model.generate_content(prompt)

    return response.text


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
