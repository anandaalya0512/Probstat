"""Taskly: skor prioritas tugas, analisis Spearman, dan API sederhana.

Jalankan demo   : python taskly.py
Jalankan API    : python taskly.py api   (butuh: pip install flask)
Dependensi demo : pip install scipy
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import date
import sys

# Bobot CONTOH (belum divalidasi secara ilmiah), sama dengan versi web.
BOBOT = {"deadline": 0.5, "kesulitan": 0.3, "beban": 0.2}
BATAS_TINGGI, BATAS_SEDANG = 65, 45
HARI_MAKS = 14        # deadline >= 14 hari dianggap "jauh" (nilai 0)
BEBAN_MAKS = 6        # 6 tugas aktif lain dianggap beban penuh (nilai 1)


@dataclass
class Tugas:
    id: int
    nama: str
    mata_kuliah: str
    deadline: date
    kesulitan: int            # 1-5
    status: int = 0           # 0 belum, 1 sedang, 2 selesai
    deskripsi: str = ""

    def aktif(self) -> bool:
        return self.status < 2


def _batas(x: float) -> float:
    return max(0.0, min(1.0, x))


def hitung_skor(t: Tugas, semua: list[Tugas], hari_ini: date | None = None) -> dict:
    """Skor 0-100 = 50% kedekatan deadline + 30% kesulitan + 20% beban tugas lain."""
    hari_ini = hari_ini or date.today()
    sisa = (t.deadline - hari_ini).days
    lain = sum(1 for x in semua if x.aktif() and x.id != t.id)
    f = {
        "deadline": _batas(1 - sisa / HARI_MAKS),
        "kesulitan": t.kesulitan / 5,
        "beban": _batas(lain / BEBAN_MAKS),
    }
    skor = round(100 * sum(f[k] * BOBOT[k] for k in BOBOT))
    kategori = "Tinggi" if skor >= BATAS_TINGGI else "Sedang" if skor >= BATAS_SEDANG else "Rendah"
    return {"skor": skor, "kategori": kategori, "sisa_hari": sisa, "tugas_lain": lain, "faktor": f}


def peringkat(daftar: list[Tugas], hari_ini: date | None = None) -> list[dict]:
    aktif = [t for t in daftar if t.aktif()]
    hasil = [{**asdict(t), **hitung_skor(t, daftar, hari_ini)} for t in aktif]
    return sorted(hasil, key=lambda r: r["skor"], reverse=True)


def analisis_spearman(rows: list[dict], alpha: float = 0.05) -> list[dict]:
    """Korelasi Spearman tiap faktor terhadap skor prioritas."""
    from scipy.stats import spearmanr
    skor = [r["skor"] for r in rows]
    pasangan = {
        "Kedekatan deadline & prioritas": [-r["sisa_hari"] for r in rows],  # makin dekat = nilai makin besar
        "Tingkat kesulitan & prioritas": [r["kesulitan"] for r in rows],
        "Beban tugas lain & prioritas": [r["tugas_lain"] for r in rows],
    }
    out = []
    for nama, x in pasangan.items():
        rho, p = spearmanr(x, skor)
        out.append({"analisis": nama, "rho": round(float(rho), 3), "p": round(float(p), 4),
                    "signifikan": bool(p < alpha)})
    return out


CONTOH = [
    Tugas(1, "Laporan Praktikum", "Pemrograman Web", date(2026, 11, 8), 4, 1),
    Tugas(2, "Tugas Analisis Data", "Probabilitas dan Statistika", date(2026, 11, 9), 5, 0),
    Tugas(3, "Desain Prototype", "UI/UX", date(2026, 11, 10), 3, 1),
    Tugas(4, "Esai Etika Profesi TI", "Etika Profesi", date(2026, 11, 12), 2, 0),
    Tugas(5, "Rangkuman Bab Jaringan", "Jaringan Komputer", date(2026, 11, 13), 1, 0),
    Tugas(6, "Makalah Normalisasi", "Basis Data", date(2026, 10, 28), 3, 2),
]


def demo():
    hari_ini = date(2026, 11, 6)
    rows = peringkat(CONTOH, hari_ini)
    print("PERINGKAT PRIORITAS")
    for i, r in enumerate(rows, 1):
        print(f"{i}. {r['nama']:<26} skor {r['skor']:>3}  {r['kategori']:<7} ({r['sisa_hari']} hari lagi)")
    print("\nANALISIS SPEARMAN (data contoh, bukan temuan penelitian)")
    try:
        for a in analisis_spearman(rows):
            print(f"- {a['analisis']}: rho={a['rho']}, p={a['p']}, "
                  f"{'signifikan' if a['signifikan'] else 'tidak signifikan'}")
    except ImportError:
        print("Pasang scipy dulu: pip install scipy")


def api():
    from flask import Flask, jsonify, request
    app = Flask(__name__)
    db = {t.id: t for t in CONTOH}

    @app.get("/api/tugas")
    def daftar():
        return jsonify([asdict(t) | {"deadline": t.deadline.isoformat()} for t in db.values()])

    @app.post("/api/tugas")
    def tambah():
        d = request.get_json(force=True)
        if not d.get("nama") or not d.get("deadline"):
            return jsonify(error="Nama tugas dan deadline wajib diisi"), 400
        tid = max(db, default=0) + 1
        db[tid] = Tugas(tid, d["nama"], d.get("mata_kuliah", ""), date.fromisoformat(d["deadline"]),
                        int(d.get("kesulitan", 3)), int(d.get("status", 0)), d.get("deskripsi", ""))
        return jsonify(id=tid), 201

    @app.post("/api/tugas/<int:tid>/selesai")
    def selesai(tid):
        if tid not in db:
            return jsonify(error="Tugas tidak ditemukan"), 404
        db[tid].status = 2
        return jsonify(ok=True)

    @app.delete("/api/tugas/<int:tid>")
    def hapus(tid):
        db.pop(tid, None)
        return jsonify(ok=True)

    @app.get("/api/prioritas")
    def prioritas():
        return jsonify([{**r, "deadline": r["deadline"].isoformat()} for r in peringkat(list(db.values()))])

    app.run(debug=True)


if __name__ == "__main__":
    api() if len(sys.argv) > 1 and sys.argv[1] == "api" else demo()