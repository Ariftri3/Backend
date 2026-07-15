from flask import Blueprint, jsonify
from database import get_db, release_db
from middleware.auth_middleware import token_required

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics/summary", methods=["GET"])
@token_required
def analytics_summary(current_user_id):
    conn, cursor = get_db()

    try:
        # Total User
        cursor.execute("SELECT COUNT(*) AS total FROM profiles")
        total_users = cursor.fetchone()["total"]

        # Total Mood
        cursor.execute("SELECT COUNT(*) AS total FROM mood_logs")
        total_moods = cursor.fetchone()["total"]

        # Total Journal
        cursor.execute("SELECT COUNT(*) AS total FROM journals")
        total_journals = cursor.fetchone()["total"]

        # Total Assessment
        cursor.execute("SELECT COUNT(*) AS total FROM assessments")
        total_assessments = cursor.fetchone()["total"]

        # Total Chat
        cursor.execute("SELECT COUNT(*) AS total FROM chat_histories")
        total_chat = cursor.fetchone()["total"]

        # Total Emotion
        cursor.execute("SELECT COUNT(*) AS total FROM emotion_detections")
        total_emotions = cursor.fetchone()["total"]

        return jsonify({
            "success": True,
            "data": {
                "total_users": total_users,
                "total_moods": total_moods,
                "total_journals": total_journals,
                "total_assessments": total_assessments,
                "total_chat": total_chat,
                "total_emotions": total_emotions
            }
        })

    finally:
        cursor.close()
        release_db(conn)
        