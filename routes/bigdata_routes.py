import base64
import io
from flask import Blueprint, send_file, jsonify, abort
import pymongo
from config import MONGO_URI

bigdata_bp = Blueprint("bigdata", __name__)

_mongo_client = None

def get_mongo_db():
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = pymongo.MongoClient(MONGO_URI)
        except Exception as e:
            print(f"[MONGO ERROR] Gagal koneksi MongoDB Atlas: {e}")
            raise
    return _mongo_client["CapstoneBigData"]

@bigdata_bp.route("/api/bigdata/charts/<chart_name>", methods=["GET"])
def get_chart_image(chart_name):
    """
    Mengembalikan file PNG biner untuk chart tertentu.
    Akses publik (tanpa token_required) untuk kemudahan Image.network() di Flutter.
    
    Kategori chart_name yang didukung:
    - mood_distribution
    - emotion_breakdown
    - news_words
    - news_wordcloud
    """
    # Mapping request param ke key di database
    key_mapping = {
        "mood_distribution": "chart_mood_distribution",
        "emotion_breakdown": "chart_emotion_breakdown",
        "news_words": "chart_news_words",
        "news_wordcloud": "chart_news_wordcloud"
    }
    
    db_key = key_mapping.get(chart_name)
    if not db_key:
        return jsonify({"success": False, "message": "Nama chart tidak valid. Gunakan: mood_distribution, emotion_breakdown, news_words, atau news_wordcloud."}), 400
        
    try:
        db = get_mongo_db()
        collection = db["BigData_Charts"]
        
        doc = collection.find_one({"_id": "latest_charts"})
        if not doc or db_key not in doc:
            return jsonify({"success": False, "message": "Chart belum digenerate. Silakan jalankan pipeline data."}), 404
            
        # Decode base64 image
        b64_data = doc[db_key]
        img_bytes = base64.b64decode(b64_data)
        
        return send_file(
            io.BytesIO(img_bytes),
            mimetype='image/png',
            as_attachment=False,
            download_name=f"{chart_name}.png"
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal mengambil chart: {str(e)}"}), 500

@bigdata_bp.route("/api/bigdata/stats", methods=["GET"])
def get_bigdata_stats():
    """
    Mengambil data statistik ringkas big data (termasuk timestamp update terakhir).
    """
    try:
        db = get_mongo_db()
        collection = db["BigData_Charts"]
        
        doc = collection.find_one({"_id": "latest_charts"})
        if not doc:
            return jsonify({
                "success": True,
                "data": {
                    "news_count": 0,
                    "updated_at": "Belum ada data"
                }
            }), 200
            
        # Format updated_at
        updated_at = doc.get("updated_at")
        if isinstance(updated_at, str):
            updated_at_str = updated_at
        else:
            updated_at_str = updated_at.strftime("%Y-%m-%d %H:%M:%S") if updated_at else "Unknown"
            
        return jsonify({
            "success": True,
            "data": {
                "news_count": doc.get("news_count", 0),
                "updated_at": updated_at_str
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal mengambil statistik: {str(e)}"}), 500
