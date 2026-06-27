# MindCare API Testing Guide
# Gunakan Postman atau cURL untuk test endpoints ini

## 1. REGISTER
POST http://localhost:5000/register
Content-Type: application/json

{
  "nama": "John Doe",
  "email": "john@example.com",
  "password": "password123"
}

## 2. LOGIN
POST http://localhost:5000/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "password123"
}

Response akan berisi token JWT:
{
  "success": true,
  "token": "eyJhbGc...",
  "user": { "id": 1, "nama": "John Doe", "email": "john@example.com" }
}

## 3. GET PROFILE (Protected - butuh token)
GET http://localhost:5000/profile
Authorization: Bearer <TOKEN_DARI_LOGIN>

## 4. UPDATE PROFILE (Protected)
PUT http://localhost:5000/profile
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "nama": "Jane Doe",
  "foto_url": "https://..."
}

## 5. GET PROFILE STATS (Protected)
GET http://localhost:5000/profile/stats
Authorization: Bearer <TOKEN>

## 6. SAVE MOOD (Protected)
POST http://localhost:5000/mood
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "mood_value": 4,
  "catatan": "Hari yang menyenangkan"
}

## 7. GET MOODS (Protected)
GET http://localhost:5000/mood?limit=7
Authorization: Bearer <TOKEN>

## 8. UPDATE MOOD (Protected)
PUT http://localhost:5000/mood/1
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "mood_value": 3,
  "catatan": "Mood update"
}

## 9. DELETE MOOD (Protected)
DELETE http://localhost:5000/mood/1
Authorization: Bearer <TOKEN>

## 10. CREATE JOURNAL (Protected)
POST http://localhost:5000/journal
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "title": "Jurnal Hari Ini",
  "content": "Isi jurnal yang panjang...",
  "mood": "Baik"
}

## 11. GET JOURNALS (Protected)
GET http://localhost:5000/journal
Authorization: Bearer <TOKEN>

## 12. UPDATE JOURNAL (Protected)
PUT http://localhost:5000/journal/1
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "title": "Judul Baru",
  "content": "Isi baru...",
  "mood": "Sedang"
}

## 13. DELETE JOURNAL (Protected)
DELETE http://localhost:5000/journal/1
Authorization: Bearer <TOKEN>

## 14. SAVE ASSESSMENT (Protected)
POST http://localhost:5000/assessment
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "score": 75
}

## 15. GET ASSESSMENTS (Protected)
GET http://localhost:5000/assessment
Authorization: Bearer <TOKEN>

## 16. SEND CHATBOT MESSAGE (Protected)
POST http://localhost:5000/chatbot
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "message": "Aku merasa sedih hari ini"
}

## 17. GET CHAT HISTORY (Protected)
GET http://localhost:5000/chatbot/history
Authorization: Bearer <TOKEN>

## 18. DELETE ACCOUNT (Protected)
DELETE http://localhost:5000/profile
Authorization: Bearer <TOKEN>

---

## Testing dengan cURL (Linux/Mac/Windows)

# Register
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"nama":"John","email":"john@test.com","password":"123456"}'

# Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@test.com","password":"123456"}'

# Get Profile (ganti TOKEN dengan token dari login)
curl -X GET http://localhost:5000/profile \
  -H "Authorization: Bearer TOKEN"

# Save Mood
curl -X POST http://localhost:5000/mood \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mood_value":4,"catatan":"Baik hari ini"}'
