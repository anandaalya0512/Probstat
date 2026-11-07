"""Taskly versi desktop: Python + Tkinter (tanpa HTML), data dari MySQL.

Butuh : taskly.py (satu folder), pip install pymysql scipy
Jalankan: python taskly_ui.py
Konfigurasi MySQL lewat environment: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
Jika MySQL tidak bisa dihubungi, aplikasi tetap jalan dengan data contoh di memori.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from taskly import Tugas, CONTOH, hitung_skor, peringkat, analisis_spearman

PU, CO, TE, YE, PK, GR = "#7566DC", "#FF9B70", "#54BFC0", "#FFD66B", "#F5A9C5", "#A9D9A8"
BG, SF, TX, T2, LN = "#F7F6FC", "#FFFFFF", "#29283A", "#777487", "#ECEAF7"
WARNA = {"Tinggi": ("#FFEDE4", "#B6481C"), "Sedang": ("#FFF5D9", "#946400"), "Rendah": ("#E9F5E8", "#2F7D2E"),
         "Belum Dikerjakan": ("#F1F0F8", T2), "Sedang Dikerjakan": ("#EEEBFC", "#5B4CC4"), "Selesai": ("#E9F5E8", "#2F7D2E"),
         "Tepat Waktu": ("#E9F5E8", "#2F7D2E"), "Terlambat": ("#FFEDE4", "#B6481C")}
STATUS = ["Belum Dikerjakan", "Sedang Dikerjakan", "Selesai"]
KES = ["", "Sangat Mudah", "Mudah", "Sedang", "Sulit", "Sangat Sulit"]
KES_WARNA = ["", GR, TE, YE, CO, PK]
MATKUL = ["Pemrograman Web", "Probabilitas dan Statistika", "UI/UX", "Etika Profesi", "Jaringan Komputer",
          "Basis Data", "Struktur Data", "Kecerdasan Buatan", "Kalkulus"]
FN = "Segoe UI"


# ---------------------------------------------------------------- data
class Repo:
    """MySQL jika tersedia, selain itu data contoh di memori."""

    def __init__(self):
        self.mem, self.err = None, None
        try:
            import pymysql
            self.pm = pymysql
            self.q("SELECT 1")
        except Exception as e:  # server mati, password salah, paket belum terpasang, dst.
            self.err = str(e)
            self.mem = [dict(id=t.id, nama=t.nama, mata_kuliah=t.mata_kuliah, deskripsi=t.deskripsi,
                             tanggal_pemberian=t.deadline.replace(day=1), deadline=t.deadline, kesulitan=t.kesulitan,
                             status=t.status, tanggal_selesai=t.deadline if t.status == 2 else None) for t in CONTOH]

    def q(self, sql, p=(), tulis=False):
        with self.pm.connect(host=os.getenv("DB_HOST", "localhost"), user=os.getenv("DB_USER", "root"),
                             password=os.getenv("DB_PASSWORD", ""), database=os.getenv("DB_NAME", "taskly"),
                             charset="utf8mb4", cursorclass=self.pm.cursors.DictCursor, autocommit=True) as db:
            with db.cursor() as c:
                c.execute(sql, p)
                return c.rowcount if tulis else c.fetchall()

    def semua(self):
        return sorted(self.mem, key=lambda r: r["deadline"]) if self.mem is not None else self.q("SELECT * FROM tugas ORDER BY deadline")

    def simpan(self, d, tid=None):
        if self.mem is not None:
            if tid:
                r = next(x for x in self.mem if x["id"] == tid)
                r.update(d)
            else:
                r = dict(d, id=max([x["id"] for x in self.mem], default=0) + 1)
                self.mem.append(r)
            r["tanggal_selesai"] = (r.get("tanggal_selesai") or date.today()) if d["status"] == 2 else None
            return
        v = (d["nama"], d["mata_kuliah"], d["deskripsi"], d["tanggal_pemberian"], d["deadline"], d["kesulitan"], d["status"])
        if tid:
            self.q("UPDATE tugas SET nama=%s,mata_kuliah=%s,deskripsi=%s,tanggal_pemberian=%s,deadline=%s,kesulitan=%s,status=%s,"
                   "tanggal_selesai=IF(status=2,COALESCE(tanggal_selesai,CURDATE()),NULL) WHERE id=%s", v + (tid,), True)
        else:
            self.q("INSERT INTO tugas (nama,mata_kuliah,deskripsi,tanggal_pemberian,deadline,kesulitan,status,tanggal_selesai) "
                   "VALUES (%s,%s,%s,%s,%s,%s,%s,IF(%s=2,CURDATE(),NULL))", v + (d["status"],), True)

    def selesai(self, tid):
        if self.mem is not None:
            r = next(x for x in self.mem if x["id"] == tid)
            r["status"], r["tanggal_selesai"] = 2, date.today()
        else:
            self.q("UPDATE tugas SET status=2, tanggal_selesai=CURDATE() WHERE id=%s", (tid,), True)

    def hapus(self, tid):
        if self.mem is not None:
            self.mem[:] = [x for x in self.mem if x["id"] != tid]
        else:
            self.q("DELETE FROM tugas WHERE id=%s", (tid,), True)


# ---------------------------------------------------------------- widget kecil
def lbl(p, t, size=10, bold=False, fg=TX, bg=SF, **k):
    return tk.Label(p, text=t, font=(FN, size, "bold" if bold else "normal"), fg=fg, bg=bg, **k)


def card(p, **k):
    return tk.Frame(p, bg=SF, highlightthickness=1, highlightbackground=LN, **k)


def tombol(p, t, cmd, bg=PU, fg="white"):
    return tk.Button(p, text=t, command=cmd, bg=bg, fg=fg, font=(FN, 10, "bold"), relief="flat", bd=0, padx=16, pady=7,
                     cursor="hand2", activebackground=bg, activeforeground=fg)


def badge(p, t, bg=SF):
    b, f = WARNA.get(t, (LN, TX))
    return tk.Label(p, text=f" {t} ", font=(FN, 9, "bold"), bg=b, fg=f, padx=4, pady=1)


def kartu_stat(p, angka, ket, warna):
    c = card(p, padx=16, pady=14)
    tk.Frame(c, bg=warna, width=6).pack(side="left", fill="y", padx=(0, 12))
    kol = tk.Frame(c, bg=SF)
    kol.pack(side="left")
    lbl(kol, str(angka), 22, True).pack(anchor="w")
    lbl(kol, ket, 9, fg=T2).pack(anchor="w")
    return c


def baris_stat(p, items):
    f = tk.Frame(p, bg=BG)
    for i, (a, k, w) in enumerate(items):
        f.columnconfigure(i, weight=1, uniform="s")
        kartu_stat(f, a, k, w).grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))
    return f


def scroller(p):
    cv = tk.Canvas(p, bg=BG, highlightthickness=0)
    sb = ttk.Scrollbar(p, orient="vertical", command=cv.yview)
    inner = tk.Frame(cv, bg=BG)
    inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
    w = cv.create_window((0, 0), window=inner, anchor="nw")
    cv.bind("<Configure>", lambda e: cv.itemconfigure(w, width=e.width))
    cv.configure(yscrollcommand=sb.set)
    cv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def roda(e):
        try:
            cv.yview_scroll(int(-e.delta / 120), "units")
        except tk.TclError:
            pass
    cv.bind_all("<MouseWheel>", roda)
    return inner


def judul(p, t, sub, aksi=None):
    f = tk.Frame(p, bg=BG)
    f.pack(fill="x", pady=(0, 16))
    kiri = tk.Frame(f, bg=BG)
    kiri.pack(side="left")
    lbl(kiri, t, 20, True, bg=BG).pack(anchor="w")
    lbl(kiri, sub, 10, fg=T2, bg=BG).pack(anchor="w")
    if aksi:
        aksi(f).pack(side="right")


def tabel(p, kolom, lebar, tinggi=10):
    f = tk.Frame(p, bg=SF)
    t = ttk.Treeview(f, columns=kolom, show="headings", height=tinggi, selectmode="browse")
    for k, w in zip(kolom, lebar):
        t.heading(k, text=k)
        t.column(k, width=w, anchor="w")
    sb = ttk.Scrollbar(f, orient="vertical", command=t.yview)
    t.configure(yscrollcommand=sb.set)
    t.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    for k, (b, _) in WARNA.items():
        t.tag_configure(k, background=b)
    return f, t


def pilih(p, var, nilai, w=22):
    return ttk.Combobox(p, textvariable=var, values=nilai, state="readonly", width=w)


# ---------------------------------------------------------------- aplikasi
class Taskly(tk.Tk):
    MENU = [("dashboard", "Dashboard", "▦"), ("tugas", "Daftar Tugas", "☰"), ("tambah", "Tambah Tugas", "＋"),
            ("prioritas", "Prioritas Tugas", "⚑"), ("statistik", "Statistik & Analisis", "▤"), ("riwayat", "Riwayat Tugas", "⟲")]

    def __init__(self):
        super().__init__()
        self.title("Taskly – Prioritas Tugas Mahasiswa")
        self.geometry("1200x780")
        self.minsize(980, 620)
        self.configure(bg=BG)
        st = ttk.Style(self)
        st.theme_use("clam")
        st.configure("Treeview", rowheight=32, font=(FN, 10), background=SF, fieldbackground=SF, borderwidth=0)
        st.configure("Treeview.Heading", font=(FN, 10, "bold"), background=BG, foreground=T2, relief="flat")
        st.map("Treeview", background=[("selected", "#EEEBFC")], foreground=[("selected", TX)])
        self.repo = Repo()
        self.edit_id = None
        self.nav = {}

        sb = tk.Frame(self, bg=SF, width=235, highlightthickness=1, highlightbackground=LN)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        logo = tk.Frame(sb, bg=SF)
        logo.pack(anchor="w", padx=18, pady=(22, 20))
        tk.Label(logo, text="✓", bg=PU, fg="white", font=(FN, 14, "bold"), width=3, pady=3).pack(side="left")
        lbl(logo, "  Taskly", 18, True).pack(side="left")
        for k, nama, ik in self.MENU:
            b = tk.Label(sb, text=f"  {ik}   {nama}", anchor="w", font=(FN, 11, "bold"), padx=14, pady=10, cursor="hand2", bg=SF, fg=T2)
            b.pack(fill="x", padx=12, pady=2)
            b.bind("<Button-1>", lambda e, k=k: self.buka(k))
            self.nav[k] = b
        tip = tk.Frame(sb, bg="#FFF5D9")
        tip.pack(side="bottom", fill="x", padx=14, pady=16)
        lbl(tip, "Tips hari ini", 10, True, bg="#FFF5D9").pack(anchor="w", padx=12, pady=(10, 0))
        lbl(tip, "Kerjakan tugas dengan deadline\nterdekat lebih dulu.", 9, fg=T2, bg="#FFF5D9", justify="left").pack(anchor="w", padx=12, pady=(0, 10))

        kanan = tk.Frame(self, bg=BG)
        kanan.pack(side="left", fill="both", expand=True)
        head = tk.Frame(kanan, bg=BG, height=70)
        head.pack(fill="x", padx=28)
        head.pack_propagate(False)
        self.sapa = lbl(head, "", 15, True, bg=BG)
        self.sapa.pack(side="left")
        user = card(head, padx=10, pady=4)
        user.pack(side="right", pady=14)
        tk.Label(user, text="MH", bg=PK, fg=TX, font=(FN, 9, "bold"), width=4, pady=3).pack(side="left")
        lbl(user, "  Mahasiswa Hebat", 10, True).pack(side="left")
        tk.Button(head, text="🔔", relief="flat", bg=SF, font=(FN, 12), command=self.notif, cursor="hand2").pack(side="right", padx=10, pady=14)
        self.isi = tk.Frame(kanan, bg=BG)
        self.isi.pack(fill="both", expand=True, padx=(28, 12), pady=(0, 16))
        self.buka("dashboard")
        if self.repo.err:
            messagebox.showwarning("MySQL tidak terhubung", "Aplikasi memakai data contoh di memori.\n\nPenyebab:\n" + self.repo.err[:300])

    # ----- navigasi & data
    def muat(self):
        self.rows = self.repo.semua()
        self.tasks = [Tugas(r["id"], r["nama"], r["mata_kuliah"], r["deadline"], r["kesulitan"], r["status"], r["deskripsi"] or "") for r in self.rows]
        self.aktif = [t for t in self.tasks if t.aktif()]

    def info(self, t):
        return hitung_skor(t, self.tasks)

    def prio(self, t):
        return self.info(t)["kategori"] if t.aktif() else "–"

    def buka(self, k):
        if k != "tambah":
            self.edit_id = None
        self.muat()
        for n, b in self.nav.items():
            b.configure(bg=PU if n == k else SF, fg="white" if n == k else T2)
        self.sapa.configure(text="Halo, Mahasiswa! 👋" if k == "dashboard" else dict((a, b) for a, b, _ in self.MENU)[k])
        for w in self.isi.winfo_children():
            w.destroy()
        getattr(self, "p_" + k)(scroller(self.isi))

    def notif(self):
        n = [t for t in self.aktif if (t.deadline - date.today()).days <= 3]
        messagebox.showinfo("Notifikasi", "\n".join(f"• {t.nama} ({(t.deadline - date.today()).days} hari lagi)" for t in n) or "Tidak ada deadline mendesak.")

    # ----- 1. dashboard
    def p_dashboard(self, p):
        a = peringkat(self.tasks)
        hi = sum(r["kategori"] == "Tinggi" for r in a)
        soon = sum(r["sisa_hari"] <= 7 for r in a)
        ban = tk.Frame(p, bg=PU)
        ban.pack(fill="x", pady=(0, 16))
        lbl(ban, "Let’s Get Things Done!", 22, True, fg="white", bg=PU).pack(anchor="w", padx=26, pady=(22, 0))
        lbl(ban, "Atur prioritas, kelola waktumu, dan capai target akademikmu.", 11, fg="#EEEBFC", bg=PU).pack(anchor="w", padx=26, pady=(2, 12))
        tombol(ban, "＋ Tambah Tugas", lambda: self.buka("tambah"), CO, TX).pack(anchor="w", padx=26, pady=(0, 22))
        baris_stat(p, [(len(self.tasks), "Total Tugas", PU), (len(self.tasks) - len(self.aktif), "Tugas Selesai", TE),
                       (hi, "Prioritas Tinggi", CO), (soon, "Segera Deadline", YE)]).pack(fill="x", pady=(0, 16))
        bwh = tk.Frame(p, bg=BG)
        bwh.pack(fill="x")
        bwh.columnconfigure(0, weight=3)
        bwh.columnconfigure(1, weight=2)
        kiri = card(bwh, padx=20, pady=16)
        kiri.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        lbl(kiri, "Prioritas Saya", 13, True).pack(anchor="w", pady=(0, 6))
        for r in a[:4]:
            f = tk.Frame(kiri, bg=SF)
            f.pack(fill="x", pady=5)
            tk.Button(f, text="✓", width=3, relief="flat", bg=LN, fg=SF, cursor="hand2", command=lambda i=r["id"]: self.selesai(i)).pack(side="left", padx=(0, 10))
            kol = tk.Frame(f, bg=SF)
            kol.pack(side="left")
            lbl(kol, r["nama"], 10, True).pack(anchor="w")
            lbl(kol, f'{r["mata_kuliah"]} · Deadline {r["deadline"]:%d %b %Y}', 9, fg=T2).pack(anchor="w")
            badge(f, r["kategori"]).pack(side="right")
            badge(f, STATUS[r["status"]]).pack(side="right", padx=6)
        if not a:
            lbl(kiri, "Semua tugas selesai. Waktunya istirahat!", 10, fg=T2).pack(anchor="w")
        kan = tk.Frame(bwh, bg=BG)
        kan.grid(row=0, column=1, sticky="nsew")
        pr = card(kan, padx=20, pady=16)
        pr.pack(fill="x", pady=(0, 8))
        lbl(pr, "Progres Tugas", 13, True).pack(anchor="w")
        n, d = len(self.tasks), len(self.tasks) - len(self.aktif)
        self.bar(pr, [(d, TE), (sum(t.status == 1 for t in self.tasks), PU), (sum(t.status == 0 for t in self.tasks), YE)], 300, 14).pack(anchor="w", pady=8)
        lbl(pr, f"{d} selesai · {sum(t.status == 1 for t in self.tasks)} sedang · {sum(t.status == 0 for t in self.tasks)} belum  ({round(d / n * 100) if n else 0}%)", 9, fg=T2).pack(anchor="w")
        dl = card(kan, padx=20, pady=16)
        dl.pack(fill="x")
        lbl(dl, "Deadline Mendatang", 13, True).pack(anchor="w", pady=(0, 6))
        for r in sorted(a, key=lambda r: r["deadline"])[:4]:
            lbl(dl, f'📅  {r["nama"]}  –  {r["sisa_hari"]} hari lagi', 10).pack(anchor="w", pady=2)

    def bar(self, p, seg, w, h):
        c = tk.Canvas(p, width=w, height=h, bg=SF, highlightthickness=0)
        tot, x = sum(v for v, _ in seg) or 1, 0
        for v, wr in seg:
            c.create_rectangle(x, 0, x + v / tot * w, h, fill=wr, outline=wr)
            x += v / tot * w
        return c

    def selesai(self, tid):
        self.repo.selesai(tid)
        self.buka(self.cur_halaman())

    def cur_halaman(self):
        return next(k for k, b in self.nav.items() if b.cget("bg") == PU)

    # ----- 2. daftar tugas
    def p_tugas(self, p):
        judul(p, "Daftar Tugas", "Kelola semua tugas perkuliahanmu dalam satu tempat.", lambda f: tombol(f, "＋ Tambah Tugas", lambda: self.buka("tambah")))
        baris_stat(p, [(len(self.tasks), "Semua Tugas", PU), (sum(t.status == 0 for t in self.tasks), "Belum Dikerjakan", YE),
                       (sum(t.status == 1 for t in self.tasks), "Sedang Dikerjakan", TE), (sum(t.status == 2 for t in self.tasks), "Selesai", GR)]).pack(fill="x", pady=(0, 16))
        c = card(p, padx=18, pady=16)
        c.pack(fill="x")
        fl = tk.Frame(c, bg=SF)
        fl.pack(fill="x", pady=(0, 10))
        self.fq, self.fm, self.fs, self.fp = tk.StringVar(), tk.StringVar(value="Semua mata kuliah"), tk.StringVar(value="Semua status"), tk.StringVar(value="Semua prioritas")
        e = tk.Entry(fl, textvariable=self.fq, font=(FN, 10), relief="solid", bd=1, width=30)
        e.pack(side="left", ipady=4, padx=(0, 8))
        lbl(fl, "← cari nama tugas atau mata kuliah", 9, fg=T2).pack(side="left", padx=(0, 12))
        for v, n in ((self.fm, ["Semua mata kuliah"] + sorted({t.mata_kuliah for t in self.tasks})), (self.fs, ["Semua status"] + STATUS),
                     (self.fp, ["Semua prioritas", "Tinggi", "Sedang", "Rendah"])):
            pilih(fl, v, n, 20).pack(side="left", padx=4)
            v.trace_add("write", lambda *a: self.isi_tugas())
        self.fq.trace_add("write", lambda *a: self.isi_tugas())
        f, self.tv = tabel(c, ("Nama Tugas", "Mata Kuliah", "Deadline", "Kesulitan", "Prioritas", "Status"), (240, 190, 110, 120, 90, 140), 12)
        f.pack(fill="x")
        ak = tk.Frame(c, bg=SF)
        ak.pack(fill="x", pady=(12, 0))
        for t, fn, b, fg in (("Lihat Detail", self.detail, "#EEEBFC", "#5B4CC4"), ("Ubah", self.ubah, "#EEEBFC", "#5B4CC4"),
                             ("✓ Tandai Selesai", self.tandai, "#E9F5E8", "#2F7D2E"), ("Hapus", self.hapus, "#FFEDE4", "#B6481C")):
            tombol(ak, t, fn, b, fg).pack(side="left", padx=(0, 8))
        self.isi_tugas()

    def isi_tugas(self):
        self.tv.delete(*self.tv.get_children())
        q = self.fq.get().lower()
        for t in self.tasks:
            pr = self.prio(t)
            if (q and q not in (t.nama + t.mata_kuliah).lower()) or (self.fm.get()[:5] != "Semua" and t.mata_kuliah != self.fm.get()) \
                    or (self.fs.get()[:5] != "Semua" and STATUS[t.status] != self.fs.get()) or (self.fp.get()[:5] != "Semua" and pr != self.fp.get()):
                continue
            self.tv.insert("", "end", iid=str(t.id), tags=(pr,), values=(t.nama, t.mata_kuliah, f"{t.deadline:%d %b %Y}", f"{t.kesulitan} – {KES[t.kesulitan]}", pr, STATUS[t.status]))

    def terpilih(self):
        s = self.tv.selection()
        if not s:
            messagebox.showinfo("Pilih tugas", "Klik salah satu tugas di tabel terlebih dahulu.")
            return None
        return next(t for t in self.tasks if t.id == int(s[0]))

    def detail(self):
        if t := self.terpilih():
            i = self.info(t)
            messagebox.showinfo(t.nama, f"Mata kuliah : {t.mata_kuliah}\nDeadline    : {t.deadline:%d %b %Y}\nKesulitan   : {KES[t.kesulitan]}\nStatus      : {STATUS[t.status]}\n"
                                + (f"Skor        : {i['skor']} ({i['kategori']})\n" if t.aktif() else "") + f"\n{t.deskripsi or 'Tidak ada deskripsi.'}")

    def ubah(self):
        if t := self.terpilih():
            self.buka("tambah")
            self.edit_id = t.id
            self.isi_form(t)

    def tandai(self):
        if (t := self.terpilih()) and t.aktif():
            self.selesai(t.id)

    def hapus(self):
        if (t := self.terpilih()) and messagebox.askyesno("Hapus tugas", f"Hapus “{t.nama}”?"):
            self.repo.hapus(t.id)
            self.buka("tugas")

    # ----- 3. tambah tugas
    def p_tambah(self, p):
        judul(p, "Tambah Tugas Baru", "Masukkan detail tugas agar kamu bisa mengatur prioritas dengan lebih mudah.")
        c = card(p, padx=26, pady=22)
        c.pack(fill="x")
        self.v = dict(nama=tk.StringVar(), mk=tk.StringVar(value=MATKUL[0]), beri=tk.StringVar(value=date.today().isoformat()),
                      dl=tk.StringVar(), kes=tk.IntVar(value=3), st=tk.IntVar(value=0))
        self.er = {}

        def field(label, widget_fn, kunci=None, hint=None):
            lbl(c, label, 10, True).pack(anchor="w", pady=(10, 3))
            w = widget_fn()
            w.pack(anchor="w", fill="x" if isinstance(w, tk.Entry) else None, ipady=3 if isinstance(w, tk.Entry) else 0)
            if hint:
                lbl(c, hint, 9, fg=T2).pack(anchor="w")
            if kunci:
                self.er[kunci] = lbl(c, "", 9, True, fg="#B6481C")
                self.er[kunci].pack(anchor="w")
        field("📝  Nama Tugas *", lambda: tk.Entry(c, textvariable=self.v["nama"], font=(FN, 10), relief="solid", bd=1), "nama")
        field("📚  Mata Kuliah *", lambda: pilih(c, self.v["mk"], MATKUL, 40))
        self.txt = tk.Text(c, height=4, font=(FN, 10), relief="solid", bd=1)
        field("🗒  Deskripsi Tugas", lambda: self.txt, hint="Opsional. Catatan singkat membantumu mengingat isi tugas.")
        field("📅  Tanggal Pemberian * (TTTT-BB-HH)", lambda: tk.Entry(c, textvariable=self.v["beri"], font=(FN, 10), relief="solid", bd=1, width=20), "beri")
        field("⏰  Deadline * (TTTT-BB-HH)", lambda: tk.Entry(c, textvariable=self.v["dl"], font=(FN, 10), relief="solid", bd=1, width=20), "dl", "Contoh: 2026-11-12")
        lbl(c, "🎯  Tingkat Kesulitan *", 10, True).pack(anchor="w", pady=(10, 3))
        rb = tk.Frame(c, bg=SF)
        rb.pack(anchor="w")
        for i in range(1, 6):
            tk.Radiobutton(rb, text=f"{i}\n{KES[i]}", variable=self.v["kes"], value=i, indicatoron=0, width=12, pady=6, font=(FN, 9, "bold"), bg=SF,
                           selectcolor=KES_WARNA[i], relief="solid", bd=1, cursor="hand2").pack(side="left", padx=(0, 6))
        lbl(c, "Semakin sulit tugasnya, semakin tinggi skor prioritasnya.", 9, fg=T2).pack(anchor="w")
        lbl(c, "✅  Status Tugas", 10, True).pack(anchor="w", pady=(12, 3))
        sr = tk.Frame(c, bg=SF)
        sr.pack(anchor="w")
        for i, s in enumerate(STATUS):
            tk.Radiobutton(sr, text=s, variable=self.v["st"], value=i, indicatoron=0, padx=14, pady=6, font=(FN, 9, "bold"), bg=SF, selectcolor="#EEEBFC",
                           relief="solid", bd=1, cursor="hand2").pack(side="left", padx=(0, 6))
        bt = tk.Frame(c, bg=SF)
        bt.pack(anchor="w", pady=(20, 0))
        tombol(bt, "✓ Simpan Tugas", self.simpan).pack(side="left", padx=(0, 8))
        tombol(bt, "Batal", lambda: self.buka("tugas"), LN, TX).pack(side="left")

    def isi_form(self, t):
        self.v["nama"].set(t.nama)
        self.v["mk"].set(t.mata_kuliah)
        self.v["dl"].set(t.deadline.isoformat())
        r = next(x for x in self.rows if x["id"] == t.id)
        self.v["beri"].set(r["tanggal_pemberian"].isoformat())
        self.v["kes"].set(t.kesulitan)
        self.v["st"].set(t.status)
        self.txt.insert("1.0", t.deskripsi)

    def simpan(self):
        for e in self.er.values():
            e.configure(text="")
        nama, ok = self.v["nama"].get().strip(), True
        if not nama:
            self.er["nama"].configure(text="Nama tugas wajib diisi.")
            ok = False
        try:
            beri = date.fromisoformat(self.v["beri"].get().strip())
        except ValueError:
            self.er["beri"].configure(text="Format tanggal harus TTTT-BB-HH, contoh 2026-11-06.")
            ok, beri = False, None
        try:
            dl = date.fromisoformat(self.v["dl"].get().strip())
            if beri and dl < beri:
                self.er["dl"].configure(text="Deadline tidak boleh sebelum tanggal pemberian.")
                ok = False
        except ValueError:
            self.er["dl"].configure(text="Deadline wajib diisi dengan format TTTT-BB-HH.")
            ok = False
        if not ok:
            return
        self.repo.simpan(dict(nama=nama, mata_kuliah=self.v["mk"].get(), deskripsi=self.txt.get("1.0", "end").strip(), tanggal_pemberian=beri,
                              deadline=dl, kesulitan=self.v["kes"].get(), status=self.v["st"].get()), self.edit_id)
        self.buka("tugas")

    # ----- 4. prioritas
    def p_prioritas(self, p):
        judul(p, "Prioritas Tugas", "Temukan tugas yang perlu kamu kerjakan lebih dahulu.")
        a = peringkat(self.tasks)
        baris_stat(p, [(sum(r["kategori"] == k for r in a), f"Prioritas {k}", w) for k, w in (("Tinggi", CO), ("Sedang", YE), ("Rendah", GR))]).pack(fill="x", pady=(0, 14))
        info = tk.Frame(p, bg="#EEEBFC")
        info.pack(fill="x", pady=(0, 14))
        lbl(info, "Sistem menentukan rekomendasi prioritas berdasarkan kedekatan deadline, tingkat kesulitan, dan beban tugas lainnya.", 10, True, bg="#EEEBFC", wraplength=820, justify="left").pack(anchor="w", padx=18, pady=(14, 2))
        lbl(info, "Skor = 50% deadline + 30% kesulitan + 20% beban tugas lain. Bobot ini hanya contoh dan belum divalidasi secara ilmiah.", 9, fg=T2, bg="#EEEBFC", wraplength=820, justify="left").pack(anchor="w", padx=18, pady=(0, 14))
        self.urut = tk.StringVar(value="Skor tertinggi")
        bar = tk.Frame(p, bg=BG)
        bar.pack(fill="x", pady=(0, 10))
        pilih(bar, self.urut, ["Skor tertinggi", "Deadline terdekat"]).pack(side="left")
        self.urut.trace_add("write", lambda *x: self.kartu_prio())
        self.wadah = tk.Frame(p, bg=BG)
        self.wadah.pack(fill="x")
        self.kartu_prio()

    def kartu_prio(self):
        for w in self.wadah.winfo_children():
            w.destroy()
        a = peringkat(self.tasks)
        if self.urut.get() != "Skor tertinggi":
            a.sort(key=lambda r: r["deadline"])
        warna = {"Tinggi": CO, "Sedang": YE, "Rendah": GR}
        nama = ["Kedekatan deadline", "Tingkat kesulitan", "Beban tugas lain"]
        for i, r in enumerate(a, 1):
            c = card(self.wadah)
            c.pack(fill="x", pady=5)
            tk.Frame(c, bg=warna[r["kategori"]], width=6).pack(side="left", fill="y")
            isi = tk.Frame(c, bg=SF)
            isi.pack(side="left", fill="x", expand=True, padx=14, pady=12)
            h = tk.Frame(isi, bg=SF)
            h.pack(fill="x")
            tk.Label(h, text=str(i), bg=warna[r["kategori"]], font=(FN, 13, "bold"), width=3, pady=4).pack(side="left", padx=(0, 12))
            kol = tk.Frame(h, bg=SF)
            kol.pack(side="left")
            lbl(kol, r["nama"], 11, True).pack(anchor="w")
            lbl(kol, f'{r["mata_kuliah"]} · {r["deadline"]:%d %b %Y} · {r["sisa_hari"]} hari lagi · kesulitan {r["kesulitan"]}/5 · {r["tugas_lain"]} tugas lain', 9, fg=T2).pack(anchor="w")
            badge(h, r["kategori"]).pack(side="right")
            sk = tk.Frame(h, bg=SF)
            sk.pack(side="right", padx=14)
            lbl(sk, f'{r["skor"]}/100', 12, True).pack(anchor="e")
            self.bar(sk, [(r["skor"], warna[r["kategori"]]), (100 - r["skor"], LN)], 110, 8).pack()
            det = tk.Frame(isi, bg=SF)
            for k, (n, w) in enumerate(zip(nama, (.5, .3, .2))):
                lbl(det, f'{n} (bobot {int(w * 100)}%): +{round(r["faktor"][("deadline", "kesulitan", "beban")[k]] * w * 100)} poin', 9, fg=T2).pack(anchor="w")
            lbl(det, {"Tinggi": "Deadline semakin dekat dan terdapat beberapa tugas lain yang harus diselesaikan.",
                      "Sedang": "Deadline masih cukup longgar, tetapi kesulitan dan beban tugas lain perlu diperhatikan.",
                      "Rendah": "Deadline masih jauh dan tugasnya relatif ringan."}[r["kategori"]], 9, True).pack(anchor="w", pady=(4, 0))

            def toggle(d=det, b=None):
                d.pack_forget() if d.winfo_ismapped() else d.pack(fill="x", pady=(10, 0))
            tombol(h, "Alasan ▾", toggle, "#EEEBFC", "#5B4CC4").pack(side="right", padx=8)

    # ----- 5. statistik
    def p_statistik(self, p):
        judul(p, "Statistik & Analisis", "Kenali pola pengerjaan tugas dan perkembangan akademikmu.")
        T, a = self.tasks, peringkat(self.tasks)
        n, d = len(T), len(T) - len(a)
        rt = lambda x: round(sum(x) / len(x), 1) if x else 0
        baris_stat(p, [(n, "Total Tugas", PU), (f"{rt([t.kesulitan for t in T])} / 5", "Rata-rata Kesulitan", CO),
                       (f"{rt([r['sisa_hari'] for r in a])} hari", "Rata-rata Sisa Hari", YE), (f"{round(d / n * 100) if n else 0}%", "Tugas Selesai", TE)]).pack(fill="x", pady=(0, 14))
        g = tk.Frame(p, bg=BG)
        g.pack(fill="x")
        g.columnconfigure((0, 1), weight=1, uniform="g")
        pc = [(k, sum(r["kategori"] == k for r in a), w) for k, w in (("Tinggi", CO), ("Sedang", YE), ("Rendah", GR))]
        self.chart(g, 0, 0, "Distribusi Prioritas Tugas", "pie", pc)
        self.chart(g, 0, 1, "Tugas per Tingkat Kesulitan", "bar", [(KES[i].replace("Sangat ", "S. "), sum(t.kesulitan == i for t in T), KES_WARNA[i]) for i in range(1, 6)])
        hr = lambda t: (t.deadline - date.today()).days
        self.chart(g, 1, 0, "Distribusi Deadline", "bar", [(k, sum(f(hr(t)) for t in T), w) for k, f, w in
                                                         (("Lewat", lambda x: x < 0, PK), ("0–3 hr", lambda x: 0 <= x <= 3, CO), ("4–7 hr", lambda x: 3 < x <= 7, YE), ("8+ hr", lambda x: x > 7, TE))])
        self.chart(g, 1, 1, "Selesai vs Belum Selesai", "pie", [("Selesai", d, TE), ("Belum", n - d, CO)])
        c = card(p, padx=22, pady=18)
        c.pack(fill="x", pady=(14, 0))
        lbl(c, "Hasil Analisis Statistik (Korelasi Spearman)", 13, True).pack(anchor="w")
        lbl(c, "Dihitung dari data tugas aktif di atas. Skor dibuat dari faktor yang sama, jadi hasil ini hanya ilustrasi, bukan temuan penelitian.", 9, fg=T2, wraplength=820, justify="left").pack(anchor="w", pady=(2, 10))
        try:
            if len(a) < 3:
                raise ValueError("Butuh minimal 3 tugas aktif untuk korelasi Spearman.")
            for h in analisis_spearman(a):
                nan = h["rho"] != h["rho"]
                row = tk.Frame(c, bg="#F7F6FC")
                row.pack(fill="x", pady=4)
                lbl(row, h["analisis"], 10, True, bg="#F7F6FC", width=34, anchor="w").pack(side="left", padx=10, pady=8)
                lbl(row, "ρ = –  ·  p = –" if nan else f'ρ = {h["rho"]}  ·  p = {h["p"]}', 10, bg="#F7F6FC").pack(side="left")
                badge(row, "Selesai" if h["signifikan"] else "Belum Dikerjakan").pack(side="right", padx=10)
                lbl(row, "tidak dapat dihitung" if nan else ("Signifikan" if h["signifikan"] else "Tidak signifikan"), 9, True, bg="#F7F6FC").pack(side="right")
        except Exception as e:
            lbl(c, str(e) if isinstance(e, ValueError) else "Pasang scipy dulu: python -m pip install scipy", 10, fg="#B6481C").pack(anchor="w")

    def chart(self, g, r, k, judul_, jenis, data):
        c = card(g, padx=18, pady=14)
        c.grid(row=r, column=k, sticky="nsew", padx=(0 if k == 0 else 7, 0 if k else 7), pady=7)
        lbl(c, judul_, 12, True).pack(anchor="w")
        cv = tk.Canvas(c, width=330, height=170, bg=SF, highlightthickness=0)
        cv.pack(pady=6)
        if jenis == "pie":
            tot, st = sum(v for _, v, _ in data) or 1, 90
            for nm, v, w in data:
                if v:
                    ex = v / tot * 360
                    cv.create_arc(10, 10, 160, 160, start=st, extent=-ex if ex < 360 else -359.9, fill=w, outline=SF, width=2)
                    st -= ex
            for i, (nm, v, w) in enumerate(data):
                cv.create_rectangle(190, 30 + i * 28, 202, 42 + i * 28, fill=w, outline=w)
                cv.create_text(210, 36 + i * 28, text=f"{nm}: {v}", anchor="w", font=(FN, 10), fill=TX)
        else:
            mx, bw = max([v for _, v, _ in data] + [1]), 330 // len(data)
            for i, (nm, v, w) in enumerate(data):
                h = v / mx * 110
                x = i * bw + 12
                cv.create_rectangle(x, 135 - h, x + bw - 24, 135, fill=w, outline=w)
                cv.create_text(x + (bw - 24) / 2, 125 - h, text=str(v), font=(FN, 9, "bold"), fill=TX)
                cv.create_text(x + (bw - 24) / 2, 152, text=nm, font=(FN, 8), fill=T2)

    # ----- 6. riwayat
    def p_riwayat(self, p):
        judul(p, "Riwayat Tugas", "Lihat kembali perjalanan dan progres penyelesaian tugasmu.")
        sel = [r for r in self.rows if r["status"] == 2]
        tel = lambda r: (r["tanggal_selesai"] or r["deadline"]) > r["deadline"]
        baris_stat(p, [(len(sel), "Total Tugas Selesai", TE), (sum(not tel(r) for r in sel), "Tugas Tepat Waktu", GR), (sum(tel(r) for r in sel), "Tugas Terlambat", CO)]).pack(fill="x", pady=(0, 16))
        c = card(p, padx=18, pady=16)
        c.pack(fill="x")
        fl = tk.Frame(c, bg=SF)
        fl.pack(fill="x", pady=(0, 10))
        self.hq, self.hm, self.hs = tk.StringVar(), tk.StringVar(value="Semua mata kuliah"), tk.StringVar(value="Semua status")
        tk.Entry(fl, textvariable=self.hq, font=(FN, 10), relief="solid", bd=1, width=28).pack(side="left", ipady=4, padx=(0, 8))
        lbl(fl, "← cari nama tugas", 9, fg=T2).pack(side="left", padx=(0, 12))
        pilih(fl, self.hm, ["Semua mata kuliah"] + sorted({r["mata_kuliah"] for r in sel}), 22).pack(side="left", padx=4)
        pilih(fl, self.hs, ["Semua status", "Tepat Waktu", "Terlambat"], 16).pack(side="left", padx=4)
        f, self.hv = tabel(c, ("Nama Tugas", "Mata Kuliah", "Deadline", "Tanggal Penyelesaian", "Status Pengerjaan"), (250, 190, 110, 150, 160), 10)
        f.pack(fill="x")
        self.kosong = lbl(c, "Belum ada riwayat tugas. Yuk, mulai selesaikan tugas pertamamu!", 11, True, fg=T2)

        def isi(*_):
            self.hv.delete(*self.hv.get_children())
            self.kosong.pack_forget()
            q = self.hq.get().lower()
            for r in sorted(sel, key=lambda r: r["tanggal_selesai"] or r["deadline"], reverse=True):
                st = "Terlambat" if tel(r) else "Tepat Waktu"
                if (q and q not in r["nama"].lower()) or (self.hm.get()[:5] != "Semua" and r["mata_kuliah"] != self.hm.get()) or (self.hs.get()[:5] != "Semua" and st != self.hs.get()):
                    continue
                self.hv.insert("", "end", tags=(st,), values=(r["nama"], r["mata_kuliah"], f'{r["deadline"]:%d %b %Y}', f'{(r["tanggal_selesai"] or r["deadline"]):%d %b %Y}', "Selesai " + st))
            if not self.hv.get_children():
                self.kosong.pack(pady=20)
        for v in (self.hq, self.hm, self.hs):
            v.trace_add("write", isi)
        isi()


if __name__ == "__main__":
    Taskly().mainloop()