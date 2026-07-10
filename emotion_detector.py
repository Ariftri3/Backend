import base64
import cv2
import numpy as np
from deepface import DeepFace

EMOTION_TRANSLATION = {
    "angry": "Marah",
    "disgust": "Jijik",
    "fear": "Takut",
    "happy": "Bahagia",
    "sad": "Sedih",
    "surprise": "Terkejut",
    "neutral": "Netral",
}

def predict_emotion_from_base64(base64_string):
    if not base64_string or not isinstance(base64_string, str):
        return {"status": "error", "message": "Gambar wajib berupa string base64"}

    if base64_string.startswith("data:image"):
        base64_string = base64_string.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(base64_string, validate=True)
    except Exception:
        return {"status": "error", "message": "Format base64 tidak valid"}

    try:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        return {"status": "error", "message": "Gagal mengurai gambar"}

    if img is None:
        return {"status": "error", "message": "Gambar rusak atau tidak dapat dibaca"}

    try:
        predictions = DeepFace.analyze(
            img_path=img,
            actions=["emotion"],
            enforce_detection=False,
        )
    except Exception as e:
        return {"status": "error", "message": f"Model gagal memproses gambar: {str(e)}"}

    if not predictions:
        return {"status": "error", "message": "Tidak ada hasil prediksi"}

    result = predictions[0]
    dominant_emotion = result.get("dominant_emotion", "neutral")
    emotion_scores = result.get("emotion", {})
    confidence = round(float(emotion_scores.get(dominant_emotion, 0.0)), 2)

    return {
        "status": "success",
        "emotion": EMOTION_TRANSLATION.get(dominant_emotion, dominant_emotion),
        "confidence": confidence,
        "raw_emotion": dominant_emotion,
    }