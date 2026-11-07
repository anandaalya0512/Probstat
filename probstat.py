"""Taskly API dengan MySQL.

Pasang : pip install flask pymysql scipy flask-cors
Siapkan: mysql -u root -p < schema.sql      (atau impor schema.sql lewat phpMyAdmin)
Jalankan: python taskly_mysql.py
Konfigurasi lewat environment: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
"""
import os
from datetime import date

import pymysql
from flask import Flask, jsonify, request

from taskly import Tugas, peringkat, analisis_spearman  # logika skor dari taskly.py

app = Flask(__name__)
try:
    from flask_cors import CORS  # agar halaman web bisa memanggil API ini
    CORS(app)
except ImportError:
    pass


def koneksi():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "taskly"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def query(sql, params=(), satu=False, tulis=False):
    with koneksi() as db, db.cursor() as cur:
        cur.execute(sql, params)
        if tulis:
            return cur.lastrowid, cur.rowcount
        return cur.fetchone() if satu else cur.fetchall()


def ke_json(r):
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in r.items() if k != "dibuat_pada"}


def validasi(d):
    if not str(d.get("nama", "")).strip():
        return "Nama tugas wajib diisi"
    if not d.get("mata_kuliah"):
        return "Mata kuliah wajib diisi"
    try:
        beri = date.fromisoformat(d.get("tanggal_pemberian") or date.today().isoformat())
        dl = date.fromisoformat(d.get("deadline", ""))
    except ValueError:
        return "Format tanggal harus YYYY-MM-DD"
    if dl < beri:
        return "Deadline tidak boleh sebelum tanggal pemberian"
    if int(d.get("kesulitan", 3)) not in range(1, 6):
        return "Kesulitan harus 1-5"
    if int(d.get("status", 0)) not in range(0, 3):
        return "Status harus 0, 1, atau 2"
    return None


@app.get("/api/tugas")
def daftar():
    return jsonify([ke_json(r) for r in query("SELECT * FROM tugas ORDER BY deadline")])


@app.post("/api/tugas")
def tambah():
    d = request.get_json(force=True)
    if (e := validasi(d)):
        return jsonify(error=e), 400
    tid, _ = query(
        "INSERT INTO tugas (nama, mata_kuliah, deskripsi, tanggal_pemberian, deadline, kesulitan, status, tanggal_selesai) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (d["nama"].strip(), d["mata_kuliah"], d.get("deskripsi", ""),
         d.get("tanggal_pemberian") or date.today().isoformat(), d["deadline"],
         int(d.get("kesulitan", 3)), int(d.get("status", 0)),
         date.today().isoformat() if int(d.get("status", 0)) == 2 else None),
        tulis=True)
    return jsonify(id=tid), 201


@app.put("/api/tugas/<int:tid>")
def ubah(tid):
    d = request.get_json(force=True)
    if (e := validasi(d)):
        return jsonify(error=e), 400
    st = int(d.get("status", 0))
    _, n = query(
        "UPDATE tugas SET nama=%s, mata_kuliah=%s, deskripsi=%s, tanggal_pemberian=%s, deadline=%s, "
        "kesulitan=%s, status=%s, tanggal_selesai=IF(%s=2, COALESCE(tanggal_selesai, CURDATE()), NULL) WHERE id=%s",
        (d["nama"].strip(), d["mata_kuliah"], d.get("deskripsi", ""),
         d.get("tanggal_pemberian") or date.today().isoformat(), d["deadline"],
         int(d.get("kesulitan", 3)), st, st, tid), tulis=True)
    return (jsonify(ok=True), 200) if n else (jsonify(error="Tugas tidak ditemukan"), 404)


@app.post("/api/tugas/<int:tid>/selesai")
def selesai(tid):
    _, n = query("UPDATE tugas SET status=2, tanggal_selesai=CURDATE() WHERE id=%s", (tid,), tulis=True)
    return (jsonify(ok=True), 200) if n else (jsonify(error="Tugas tidak ditemukan"), 404)


@app.delete("/api/tugas/<int:tid>")
def hapus(tid):
    _, n = query("DELETE FROM tugas WHERE id=%s", (tid,), tulis=True)
    return (jsonify(ok=True), 200) if n else (jsonify(error="Tugas tidak ditemukan"), 404)


def semua_tugas():
    return [Tugas(r["id"], r["nama"], r["mata_kuliah"], r["deadline"], r["kesulitan"], r["status"], r["deskripsi"] or "")
            for r in query("SELECT * FROM tugas")]


@app.get("/api/prioritas")
def prioritas():
    rows = peringkat(semua_tugas())
    return jsonify([{**r, "deadline": r["deadline"].isoformat()} for r in rows])


@app.get("/api/analisis")
def analisis():
    rows = peringkat(semua_tugas())
    if len(rows) < 3:
        return jsonify(error="Butuh minimal 3 tugas aktif untuk korelasi Spearman"), 400
    return jsonify(catatan="Skor dihitung dari faktor yang sama, sehingga korelasi ini hanya contoh.",
                   hasil=analisis_spearman(rows))


if __name__ == "__main__":
    app.run(debug=True)