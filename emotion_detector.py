import base64
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import math
import os

# Build the model path correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, 'face_landmarker.task')

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False,
    num_faces=1)

detector = vision.FaceLandmarker.create_from_options(options)

def get_distance(p1, p2, width, height):
    x1, y1 = p1.x * width, p1.y * height
    x2, y2 = p2.x * width, p2.y * height
    return math.hypot(x2 - x1, y2 - y1)

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
        from PIL import Image, ImageOps
        import io
        pil_img = Image.open(io.BytesIO(img_bytes))
        pil_img = ImageOps.exif_transpose(pil_img) # Fix rotation!
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    except Exception:
        return {"status": "error", "message": "Gagal mengurai gambar"}

    if img is None:
        return {"status": "error", "message": "Gambar rusak atau tidak dapat dibaca"}
        
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    
    try:
        detection_result = detector.detect(mp_image)
    except Exception as e:
        return {"status": "error", "message": f"Deteksi gagal: {str(e)}"}
    
    if not detection_result.face_landmarks:
        return {"status": "error", "message": "Wajah tidak terdeteksi"}
        
    landmarks = detection_result.face_landmarks[0]
    h, w, _ = img.shape
    
    # Calculate Mouth Aspect Ratio (MAR)
    mouth_top = landmarks[13]
    mouth_bottom = landmarks[14]
    mouth_left = landmarks[78]
    mouth_right = landmarks[308]
    
    mouth_v_dist = get_distance(mouth_top, mouth_bottom, w, h)
    mouth_h_dist = get_distance(mouth_left, mouth_right, w, h)
    mar = mouth_v_dist / (mouth_h_dist + 1e-6)
    
    # Eye Aspect Ratio (EAR) for surprise
    eye_top = landmarks[159]
    eye_bottom = landmarks[145]
    eye_left = landmarks[33]
    eye_right = landmarks[133]
    
    eye_v_dist = get_distance(eye_top, eye_bottom, w, h)
    eye_h_dist = get_distance(eye_left, eye_right, w, h)
    ear = eye_v_dist / (eye_h_dist + 1e-6)
    
    # Face width & Eyebrow distances
    face_left = landmarks[234]
    face_right = landmarks[454]
    face_width = get_distance(face_left, face_right, w, h)
    
    left_inner_eyebrow = landmarks[107]
    right_inner_eyebrow = landmarks[336]
    eyebrow_dist = get_distance(left_inner_eyebrow, right_inner_eyebrow, w, h)
    
    mouth_width_ratio = mouth_h_dist / (face_width + 1e-6)
    
    # Rule-based logic untuk emosi
    emotion = "Netral"
    confidence = 0.85
    raw_emotion = "neutral"
    
    if mar > 0.4 and ear > 0.25:
        emotion = "Terkejut"
        raw_emotion = "surprise"
        confidence = 0.92
    elif mouth_width_ratio > 0.38 or (mouth_width_ratio > 0.35 and mar > 0.1):
        emotion = "Bahagia"
        raw_emotion = "happy"
        confidence = 0.95
    elif eyebrow_dist / (face_width + 1e-6) < 0.13:
        emotion = "Marah"
        raw_emotion = "angry"
        confidence = 0.88
    elif ear < 0.2:
        emotion = "Sedih"
        raw_emotion = "sad"
        confidence = 0.80
    else:
        emotion = "Netral"
        raw_emotion = "neutral"
        confidence = 0.98
        
    return {
        "status": "success",
        "emotion": emotion,
        "confidence": round(confidence * 100, 2),
        "raw_emotion": raw_emotion,
    }