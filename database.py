import psycopg2
import psycopg2.pool
import psycopg2.extras

from config import DATABASE_URL

_pool = None


def get_pool():
    """Buat pool koneksi (lazy init — hanya dibuat sekali saat pertama dipakai)."""
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL belum diisi di .env. "
                "Ambil dari Supabase Dashboard > Settings > Database > Connection string (URI)."
            )
        try:
            _pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=DATABASE_URL,
            )
        except psycopg2.Error as e:
            print(f"[DB ERROR] Gagal buat pool koneksi: {e}")
            raise
    return _pool


def get_db():
    """
    Ambil koneksi dari pool.
    Selalu pakai pattern ini di setiap route:

        conn, cursor = get_db()
        try:
            ...
        finally:
            cursor.close()
            release_db(conn)

    Catatan: psycopg2 tidak punya conn.close() yang otomatis kembali ke pool
    seperti mysql-connector, jadi pakai release_db(conn) di bagian finally.
    """
    conn = get_pool().getconn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn, cursor


def release_db(conn):
    """Kembalikan koneksi ke pool (panggil ini, bukan conn.close())."""
    get_pool().putconn(conn)
