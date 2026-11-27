"""
GEMASIC - Sistem Informasi Pengelolaan Beasiswa Cinta Bergema (versi CLI sederhana)
Pemerintah Kabupaten Jember
Hanya butuh: pip install psycopg2-binary
"""
import psycopg2

# msvcrt hanya ada di Windows, dipakai agar password tampil sebagai *
try:
    import msvcrt
except ImportError:
    msvcrt = None

# =====================================================
# 1. KONFIGURASI & KONEKSI
# =====================================================
PINK = "\033[38;5;213m"
RESET = "\033[0m"

BANNER = r"""
  ____ _____ __  __    _    ____ ___ ____
 / ___| ____|  \/  |  / \  / ___|_ _/ ___|
| |  _|  _| | |\/| | / _ \ \___ \| | |
| |_| | |___| |  | |/ ___ \ ___) | | |___
 \____|_____|_|  |_/_/   \_\____/___\____|
   Beasiswa Cinta Bergema - Kabupaten Jember
"""

# Dokumen yang diperiksa tiap jenis verifikator (selain itu diperiksa verifikator Umum)
DOKUMEN_TAHFIDZ = "('Sertifikat Hafalan Al-Quran')"
DOKUMEN_PTN = "('Kartu Tanda Mahasiswa (KTM)', 'Transkrip Nilai')"

try:
    conn = psycopg2.connect(dbname="GEMASIC", user="postgres",
                            password="anjaybasda", host="localhost", port="5432")
    cur = conn.cursor()
except Exception as e:
    print("Gagal konek ke database:", e)
    exit()


# =====================================================
# 2. FUNGSI BANTU DATABASE
# Catatan: tanda % yang bukan %s harus ditulis %% jika query memakai parameter
# =====================================================
def ambil_semua(sql, params=()):
    """Jalankan SELECT, kembalikan semua baris (list)."""
    try:
        cur.execute(sql, params)
        hasil = cur.fetchall()
        conn.commit()
        return hasil
    except Exception as e:
        conn.rollback()
        print("[ERROR]", str(e).split("\n")[0])
        return []


def ambil_satu(sql, params=()):
    """Jalankan SELECT, kembalikan satu baris (atau None jika tidak ada)."""
    try:
        cur.execute(sql, params)
        hasil = cur.fetchone()
        conn.commit()
        return hasil
    except Exception as e:
        conn.rollback()
        print("[ERROR]", str(e).split("\n")[0])
        return None


def ubah(sql, params=()):
    """Jalankan INSERT / UPDATE / DELETE. Kembalikan True jika berhasil."""
    try:
        cur.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("[ERROR]", str(e).split("\n")[0])
        return False


# =====================================================
# 3. FUNGSI BANTU TAMPILAN & INPUT
# =====================================================
def banner():
    print(PINK + BANNER + RESET)


def judul(teks):
    print(PINK + "\n=== " + teks + " ===" + RESET)


def tunggu():
    input("\nTekan ENTER untuk lanjut...")


def rupiah(angka):
    return "Rp " + str(int(angka))


def tampil_tabel(kolom, baris):
    if len(baris) == 0:
        print("(kosong)")
        return
    print(" | ".join(kolom))
    print("-" * 60)
    for b in baris:
        teks = []
        for isi in b:
            teks.append(str(isi))
        print(" | ".join(teks))


def menu(nama, pilihan):
    """Tampilkan menu bernomor, kembalikan teks pilihan."""
    judul(nama)
    nomor = 1
    for p in pilihan:
        print(str(nomor) + ". " + p)
        nomor = nomor + 1
    while True:
        k = input("Pilih: ")
        if k.isdigit() and 1 <= int(k) <= len(pilihan):
            return pilihan[int(k) - 1]
        print("Pilihan tidak valid.")


def tanya(label):
    while True:
        v = input(label + ": ").strip()
        if v != "":
            return v
        print("Tidak boleh kosong.")


def tanya_password(label):
    """Input password: tampil * per karakter, selesai setelah ENTER ditekan.
    Jika bukan Windows, memakai input() biasa."""
    if msvcrt is None:
        return tanya(label)
    while True:
        print(label + ": ", end="", flush=True)
        password = ""
        tombol = msvcrt.getwch()
        while tombol != "\r" and tombol != "\n":      # ulangi sampai ENTER ditekan
            if tombol == "\b":                        # Backspace
                if len(password) > 0:
                    password = password[:-1]
                    print("\b \b", end="", flush=True)
            elif tombol == "\x00" or tombol == "\xe0":   # tombol khusus (panah, F1, dst): lewati
                msvcrt.getwch()
            else:
                password = password + tombol
                print("*", end="", flush=True)
            tombol = msvcrt.getwch()
        print()
        if password != "":
            return password
        print("Tidak boleh kosong.")


def tanya_angka(label, minimal=0, maksimal=999999999):
    while True:
        v = input(label + ": ").strip()
        if v.isdigit() and minimal <= int(v) <= maksimal:
            return int(v)
        print("Harus angka antara " + str(minimal) + " dan " + str(maksimal) + ".")


def tanya_digit(label, min_panjang, max_panjang):
    """Input yang hanya boleh angka dengan panjang tertentu (NIM, NIK, no HP)."""
    while True:
        v = input(label + ": ").strip()
        if v.isdigit() and min_panjang <= len(v) <= max_panjang:
            return v
        print("Harus angka " + str(min_panjang) + "-" + str(max_panjang) + " digit.")


def tanya_email():
    while True:
        v = input("Email: ").strip()
        if "@" in v and "." in v:
            return v
        print("Format email tidak valid.")


def tanya_tanggal(label):
    """Format YYYY-MM-DD (tanggal yang tidak ada akan ditolak oleh database)."""
    while True:
        v = input(label + " (YYYY-MM-DD): ").strip()
        if len(v) == 10 and v[4] == "-" and v[7] == "-":
            return v
        print("Format harus YYYY-MM-DD.")


def pilih_id(sql, params, kolom, label):
    """Tampilkan hasil query (kolom pertama = id), minta user memilih id.
    Kembalikan 0 jika batal atau datanya kosong."""
    baris = ambil_semua(sql, params)
    tampil_tabel(kolom, baris)
    if len(baris) == 0:
        return 0
    while True:
        i = tanya_angka(label + " (0 = batal)")
        if i == 0:
            return 0
        for b in baris:
            if b[0] == i:
                return i
        print("ID tidak ada di daftar.")


def sinkron_status(id_pendaftaran):
    """Perbarui status_pendaftaran (Menunggu <-> Diverifikasi) dari kondisi dokumen pendaftaran tsb:
    semua dokumen sudah diperiksa dan tidak ada yang perlu perbaikan -> Diverifikasi."""
    ada_dokumen = ambil_satu("SELECT 1 FROM dokumen_persyaratan WHERE id_pendaftaran = %s LIMIT 1",
                             (id_pendaftaran,))
    if ada_dokumen is None:
        return
    belum = ambil_satu("""
        SELECT 1 FROM dokumen_persyaratan d
        WHERE d.id_pendaftaran = %s
          AND (NOT EXISTS (SELECT 1 FROM verifikasi v WHERE v.id_dokumen = d.id_dokumen)
               OR EXISTS (SELECT 1 FROM verifikasi v WHERE v.id_dokumen = d.id_dokumen
                          AND v.catatan_verifikasi LIKE 'Perbaikan%%'))
        LIMIT 1""", (id_pendaftaran,))
    if belum is None:
        ubah("""UPDATE pendaftaran SET status_pendaftaran = 'Diverifikasi'
                WHERE id_pendaftaran = %s AND status_pendaftaran = 'Menunggu'""", (id_pendaftaran,))
    else:
        ubah("""UPDATE pendaftaran SET status_pendaftaran = 'Menunggu'
                WHERE id_pendaftaran = %s AND status_pendaftaran = 'Diverifikasi'""", (id_pendaftaran,))


# =====================================================
# 4. LOGIN & REGISTRASI
# =====================================================
def login():
    """Kembalikan (id_pengguna, nama, role) atau None.
    Role: ada di tabel mahasiswa -> mahasiswa, ada di verifikator -> verifikator, selain itu -> petugas."""
    judul("LOGIN")
    email = tanya("Email")
    password = tanya_password("Password")
    data = ambil_satu("""
        SELECT p.id_pengguna, p.nama_pengguna, p.status_akun::text,
               CASE WHEN EXISTS (SELECT 1 FROM mahasiswa m WHERE m.id_pengguna = p.id_pengguna) THEN 'mahasiswa'
                    WHEN EXISTS (SELECT 1 FROM verifikator v WHERE v.id_pengguna = p.id_pengguna) THEN 'verifikator'
                    ELSE 'petugas' END
        FROM pengguna p
        WHERE lower(p.email) = lower(%s) AND p.password = %s""", (email, password))
    if data is None:
        print("Email atau password salah.")
        return None
    if data[2] != "Aktif":
        print("Akun nonaktif.")
        return None
    return (data[0], data[1], data[3])


def register_mahasiswa():
    judul("REGISTRASI MAHASISWA")
    nama = tanya("Nama lengkap")
    email = tanya_email()
    password = tanya_password("Password")
    nim = tanya_digit("NIM", 5, 20)
    nik = tanya_digit("NIK (16 digit)", 16, 16)
    tgl = tanya_tanggal("Tanggal lahir")
    hp = tanya_digit("No. HP", 8, 12)
    kelurahan = tanya("Kelurahan")
    kecamatan = tanya("Kecamatan")
    kabupaten = tanya("Kabupaten")
    univ = tanya("Nama universitas")
    prodi = tanya("Program studi")

    # Cek duplikat di sini supaya pesannya jelas (email & NIK di pengguna; NIM & no HP di mahasiswa)
    if ambil_satu("SELECT 1 FROM pengguna WHERE lower(email) = lower(%s)", (email,)) is not None:
        print("Email sudah terdaftar.")
        return
    if ambil_satu("SELECT 1 FROM pengguna WHERE nik = %s", (nik,)) is not None:
        print("NIK sudah terdaftar.")
        return
    if ambil_satu("SELECT 1 FROM mahasiswa WHERE nim = %s OR no_hp = %s", (nim, hp)) is not None:
        print("NIM atau No. HP sudah terdaftar.")
        return

    # Semua INSERT di bawah satu transaksi: jika ada yang gagal, semuanya dibatalkan
    try:
        cur.execute("SELECT id_universitas FROM universitas WHERE lower(nama_universitas) = lower(%s)", (univ,))
        baris = cur.fetchone()
        if baris is None:
            cur.execute("INSERT INTO universitas (nama_universitas) VALUES (%s) RETURNING id_universitas", (univ,))
            baris = cur.fetchone()
        id_univ = baris[0]

        cur.execute("""SELECT id_program_studi FROM program_studi
                       WHERE lower(nama_program_studi) = lower(%s) AND id_universitas = %s""", (prodi, id_univ))
        baris = cur.fetchone()
        if baris is None:
            cur.execute("""INSERT INTO program_studi (nama_program_studi, id_universitas)
                           VALUES (%s, %s) RETURNING id_program_studi""", (prodi, id_univ))
            baris = cur.fetchone()
        id_prodi = baris[0]

        cur.execute("""INSERT INTO pengguna (nik, nama_pengguna, email, password, status_akun)
                       VALUES (%s, %s, %s, %s, 'Aktif') RETURNING id_pengguna""", (nik, nama, email, password))
        id_pengguna = cur.fetchone()[0]

        cur.execute("""INSERT INTO mahasiswa (id_pengguna, nim, tanggal_lahir, no_hp,
                                              kelurahan, kecamatan, kabupaten, id_program_studi)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (id_pengguna, nim, tgl, hp, kelurahan, kecamatan, kabupaten, id_prodi))
        conn.commit()
        print("Registrasi berhasil. Silakan login.")
    except Exception as e:
        conn.rollback()
        print("[ERROR] Registrasi gagal:", str(e).split("\n")[0])


# =====================================================
# 5. FITUR MAHASISWA
# =====================================================
def mhs_daftar(uid):
    judul("DAFTAR BEASISWA")
    id_jalur = pilih_id("SELECT id_jalur, nama_jalur, kuota FROM jalur_beasiswa ORDER BY 1", (),
                        ["ID", "Jalur", "Kuota"], "ID jalur")
    if id_jalur == 0:
        return
    syarat = ambil_semua("""SELECT nama_persyaratan, deskripsi_persyaratan
                            FROM persyaratan WHERE id_jalur = %s ORDER BY 1""", (id_jalur,))
    tampil_tabel(["Persyaratan", "Keterangan"], syarat)
    if input("Daftar ke jalur ini? (y/n): ") == "y":
        if ambil_satu("SELECT 1 FROM pendaftaran WHERE id_jalur = %s AND id_pengguna = %s", (id_jalur, uid)) is not None:
            print("Kamu sudah terdaftar di jalur ini.")
        elif ubah("""INSERT INTO pendaftaran (tanggal_daftar, status_pendaftaran, id_jalur, id_pengguna)
                     VALUES (CURRENT_DATE, 'Menunggu', %s, %s)""", (id_jalur, uid)):
            print("Pendaftaran berhasil. Lengkapi dokumen lewat menu Upload dokumen.")


def mhs_upload(uid):
    judul("UPLOAD DOKUMEN")
    # Dokumen sekarang melekat pada satu pendaftaran, jadi mahasiswa harus sudah mendaftar
    if ambil_satu("SELECT 1 FROM pendaftaran WHERE id_pengguna = %s LIMIT 1", (uid,)) is None:
        print("Kamu belum mendaftar beasiswa. Daftar dulu lewat menu Daftar beasiswa.")
        return
    id_pd = pilih_id("""
        SELECT pd.id_pendaftaran, j.nama_jalur, pd.tanggal_daftar, pd.status_pendaftaran::text
        FROM pendaftaran pd
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        WHERE pd.id_pengguna = %s
        ORDER BY 1""", (uid,), ["ID", "Jalur", "Tanggal daftar", "Status"], "ID pendaftaran")
    if id_pd == 0:
        return
    id_jenis = pilih_id("SELECT id_jenis_dokumen, nama_jenis_dokumen FROM jenis_dokumen ORDER BY 1", (),
                        ["ID", "Jenis dokumen"], "ID jenis dokumen")
    if id_jenis == 0:
        return
    nama_file = tanya("Nama file (contoh: ktp_saya.pdf)")
    if ubah("""INSERT INTO dokumen_persyaratan (nama_file, tanggal_upload, id_jenis_dokumen, id_pendaftaran)
               VALUES (%s, CURRENT_DATE, %s, %s)""", (nama_file, id_jenis, id_pd)):
        sinkron_status(id_pd)       # dokumen baru belum diperiksa -> status kembali Menunggu
        print("Dokumen tersimpan, menunggu verifikasi.")


def mhs_perbaiki(uid):
    judul("LENGKAPI BERKAS PERBAIKAN")
    # Dokumen perlu perbaikan = punya verifikasi dengan catatan berawalan "Perbaikan"
    id_dok = pilih_id("""
        SELECT d.id_dokumen, jd.nama_jenis_dokumen, d.nama_file,
               (SELECT v.catatan_verifikasi FROM verifikasi v
                WHERE v.id_dokumen = d.id_dokumen AND v.catatan_verifikasi LIKE 'Perbaikan%%'
                ORDER BY v.id_verifikasi DESC LIMIT 1)
        FROM dokumen_persyaratan d
        JOIN pendaftaran pd ON pd.id_pendaftaran = d.id_pendaftaran
        JOIN jenis_dokumen jd ON jd.id_jenis_dokumen = d.id_jenis_dokumen
        WHERE pd.id_pengguna = %s
          AND EXISTS (SELECT 1 FROM verifikasi v WHERE v.id_dokumen = d.id_dokumen
                      AND v.catatan_verifikasi LIKE 'Perbaikan%%')
        ORDER BY 1""", (uid,), ["ID", "Jenis", "File lama", "Catatan verifikator"], "ID dokumen")
    if id_dok == 0:
        return
    nama_file = tanya("Nama file baru")
    try:
        cur.execute("""UPDATE dokumen_persyaratan SET nama_file = %s, tanggal_upload = CURRENT_DATE
                       WHERE id_dokumen = %s""", (nama_file, id_dok))
        # Hapus catatan perbaikan lama agar dokumen diperiksa ulang
        cur.execute("""DELETE FROM verifikasi WHERE id_dokumen = %s AND catatan_verifikasi LIKE 'Perbaikan%%'""",
                    (id_dok,))
        conn.commit()
        pemilik = ambil_satu("SELECT id_pendaftaran FROM dokumen_persyaratan WHERE id_dokumen = %s", (id_dok,))
        sinkron_status(pemilik[0])
        print("Berkas perbaikan terkirim, menunggu verifikasi ulang.")
    except Exception as e:
        conn.rollback()
        print("[ERROR]", str(e).split("\n")[0])


def mhs_status(uid):
    judul("STATUS PENDAFTARAN")
    baris = ambil_semua("""
        SELECT pd.id_pendaftaran, j.nama_jalur, pd.tanggal_daftar, pd.status_pendaftaran::text,
               COALESCE(pt.status_keputusan::text, '-'), COALESCE(c.status_pencairan, '-')
        FROM pendaftaran pd
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        LEFT JOIN penetapan pt ON pt.id_pendaftaran = pd.id_pendaftaran
        LEFT JOIN pencairan c ON c.id_penetapan = pt.id_penetapan
        WHERE pd.id_pengguna = %s
        ORDER BY pd.id_pendaftaran""", (uid,))
    tampil_tabel(["ID", "Jalur", "Tanggal daftar", "Status", "Keputusan", "Pencairan"], baris)

    judul("STATUS DOKUMEN")
    baris = ambil_semua("""
        SELECT d.id_dokumen, d.id_pendaftaran, jd.nama_jenis_dokumen, d.nama_file,
               CASE WHEN EXISTS (SELECT 1 FROM verifikasi v WHERE v.id_dokumen = d.id_dokumen
                                 AND v.catatan_verifikasi LIKE 'Perbaikan%%') THEN 'Perlu perbaikan'
                    WHEN EXISTS (SELECT 1 FROM verifikasi v WHERE v.id_dokumen = d.id_dokumen) THEN 'Terverifikasi'
                    ELSE 'Menunggu' END,
               COALESCE((SELECT v.catatan_verifikasi FROM verifikasi v WHERE v.id_dokumen = d.id_dokumen
                         ORDER BY v.id_verifikasi DESC LIMIT 1), '-')
        FROM dokumen_persyaratan d
        JOIN pendaftaran pd ON pd.id_pendaftaran = d.id_pendaftaran
        JOIN jenis_dokumen jd ON jd.id_jenis_dokumen = d.id_jenis_dokumen
        WHERE pd.id_pengguna = %s
        ORDER BY d.id_dokumen""", (uid,))
    tampil_tabel(["ID", "ID Daftar", "Jenis", "File", "Status", "Catatan terakhir"], baris)


def mhs_pengumuman(uid):
    judul("PENGUMUMAN")
    baris = ambil_semua("""SELECT tanggal_publikasi, judul, isi_pengumuman FROM pengumuman
                           WHERE status_pengumuman = 'Terbit' ORDER BY tanggal_publikasi DESC, id_pengumuman DESC""")
    if len(baris) == 0:
        print("(belum ada pengumuman)")
    for b in baris:
        print("\n[" + str(b[0]) + "] " + b[1])
        print("  " + b[2])


def mhs_rekening(uid):
    judul("REKENING BANK")
    baris = ambil_semua("""SELECT id_rekening, nama_bank, nomor_rekening, nama_pemilik_rekening, status_validasi
                           FROM rekening_bank WHERE id_mahasiswa = %s ORDER BY 1""", (uid,))
    tampil_tabel(["ID", "Bank", "No. Rekening", "Atas nama", "Status"], baris)
    if input("Ajukan rekening baru? (y/n): ") == "y":
        bank = tanya("Nama bank")
        nomor = tanya_digit("Nomor rekening", 5, 30)
        atas_nama = tanya("Atas nama")
        if ambil_satu("SELECT 1 FROM rekening_bank WHERE nomor_rekening = %s", (nomor,)) is not None:
            print("Nomor rekening sudah terdaftar.")
            return
        # Rekening ditangani petugas pencairan yang paling sedikit menangani rekening
        petugas = ambil_satu("""
            SELECT p.id_pengguna FROM pengguna p
            LEFT JOIN rekening_bank r ON r.id_pengguna = p.id_pengguna
            WHERE p.id_pengguna NOT IN (SELECT id_pengguna FROM mahasiswa)
              AND p.id_pengguna NOT IN (SELECT id_pengguna FROM verifikator)
            GROUP BY p.id_pengguna
            ORDER BY COUNT(r.id_rekening), p.id_pengguna LIMIT 1""")
        if petugas is None:
            print("Belum ada petugas pencairan.")
        elif ubah("""INSERT INTO rekening_bank (nama_bank, nomor_rekening, nama_pemilik_rekening,
                                               status_validasi, saldo_rekening, id_pengguna, id_mahasiswa)
                     VALUES (%s, %s, %s, 'Belum Valid', 0, %s, %s)""", (bank, nomor, atas_nama, petugas[0], uid)):
            print("Rekening diajukan, menunggu validasi petugas pencairan.")


def dashboard_mahasiswa(uid, nama):
    while True:
        banner()
        print("Halo, " + nama + "!")
        pilih = menu("MENU MAHASISWA", ["Daftar beasiswa", "Upload dokumen", "Lengkapi berkas perbaikan",
                                        "Status pendaftaran", "Pengumuman", "Rekening bank", "Logout"])
        if pilih == "Daftar beasiswa":
            mhs_daftar(uid)
        elif pilih == "Upload dokumen":
            mhs_upload(uid)
        elif pilih == "Lengkapi berkas perbaikan":
            mhs_perbaiki(uid)
        elif pilih == "Status pendaftaran":
            mhs_status(uid)
        elif pilih == "Pengumuman":
            mhs_pengumuman(uid)
        elif pilih == "Rekening bank":
            mhs_rekening(uid)
        else:
            return
        tunggu()


# =====================================================
# 6. FITUR VERIFIKATOR
# =====================================================
def jenis_verifikator(uid):
    """Kembalikan 'Umum', 'Tahfidz', atau 'PTN'."""
    data = ambil_satu("SELECT jenis_verifikator::text FROM verifikator WHERE id_pengguna = %s", (uid,))
    return data[0]


def vf_pendaftaran(uid):
    judul("DATA PENDAFTARAN")
    baris = ambil_semua("""
        SELECT pd.id_pendaftaran, pg.nama_pengguna, u.nama_universitas, j.nama_jalur,
               pd.tanggal_daftar, pd.status_pendaftaran::text
        FROM pendaftaran pd
        JOIN pengguna pg ON pg.id_pengguna = pd.id_pengguna
        JOIN mahasiswa m ON m.id_pengguna = pd.id_pengguna
        JOIN program_studi ps ON ps.id_program_studi = m.id_program_studi
        JOIN universitas u ON u.id_universitas = ps.id_universitas
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        ORDER BY pd.id_pendaftaran""")
    tampil_tabel(["ID", "Mahasiswa", "Universitas", "Jalur", "Tanggal", "Status"], baris)


def vf_verifikasi(uid):
    judul("VERIFIKASI DOKUMEN")
    jenis = jenis_verifikator(uid)
    print("Verifikator " + jenis)

    # Tiap jenis verifikator hanya memeriksa dokumen miliknya
    if jenis == "Tahfidz":
        filter_jenis = "jd.nama_jenis_dokumen IN " + DOKUMEN_TAHFIDZ
    elif jenis == "PTN":
        filter_jenis = "jd.nama_jenis_dokumen IN " + DOKUMEN_PTN
    else:
        filter_jenis = ("jd.nama_jenis_dokumen NOT IN " + DOKUMEN_TAHFIDZ +
                        " AND jd.nama_jenis_dokumen NOT IN " + DOKUMEN_PTN)

    # Daftar dokumen yang belum pernah diperiksa oleh verifikator ini
    sql = """
        SELECT d.id_dokumen, pg.nama_pengguna, jd.nama_jenis_dokumen, d.nama_file
        FROM dokumen_persyaratan d
        JOIN jenis_dokumen jd ON jd.id_jenis_dokumen = d.id_jenis_dokumen
        JOIN pendaftaran pd ON pd.id_pendaftaran = d.id_pendaftaran
        JOIN pengguna pg ON pg.id_pengguna = pd.id_pengguna
        WHERE NOT EXISTS (SELECT 1 FROM verifikasi v WHERE v.id_dokumen = d.id_dokumen AND v.id_verifikator = %s)
          AND """ + filter_jenis + " ORDER BY 1"
    id_dok = pilih_id(sql, (uid,), ["ID", "Mahasiswa", "Jenis", "File"], "ID dokumen")
    if id_dok == 0:
        return

    hasil = menu("HASIL", ["Valid", "Perbaikan"])
    if hasil == "Perbaikan":
        catatan = "Perbaikan: " + tanya("Alasan perbaikan")      # awalan "Perbaikan" = berkas perlu diperbaiki
    else:
        catatan = input("Catatan verifikasi (boleh kosong): ").strip()
        if catatan == "":
            catatan = None
    if ubah("""INSERT INTO verifikasi (tanggal_verifikasi, catatan_verifikasi, id_verifikator, id_dokumen)
               VALUES (CURRENT_DATE, %s, %s, %s)""", (catatan, uid, id_dok)):
        pemilik = ambil_satu("SELECT id_pendaftaran FROM dokumen_persyaratan WHERE id_dokumen = %s", (id_dok,))
        sinkron_status(pemilik[0])
        print("Hasil verifikasi disimpan.")


def vf_nilai(uid):
    judul("PENILAIAN KELAYAKAN")
    print("(hanya pendaftar berstatus Diverifikasi)")
    id_pd = pilih_id("""
        SELECT pd.id_pendaftaran, pg.nama_pengguna, j.nama_jalur
        FROM pendaftaran pd
        JOIN pengguna pg ON pg.id_pengguna = pd.id_pengguna
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        WHERE pd.status_pendaftaran = 'Diverifikasi'
        ORDER BY 1""", (), ["ID", "Mahasiswa", "Jalur"], "ID pendaftaran")
    if id_pd == 0:
        return
    nilai = tanya_angka("Nilai (0-100)", 0, 100)
    catatan = input("Catatan penilaian (boleh kosong, maks 100 huruf): ").strip()
    if catatan == "":
        catatan = None
    try:
        cur.execute("""INSERT INTO penilaian (nilai, catatan_penilaian, tanggal_penilaian,
                                              id_pendaftaran, id_pengguna)
                       VALUES (%s, %s, CURRENT_DATE, %s, %s)""", (nilai, catatan, id_pd, uid))
        cur.execute("UPDATE pendaftaran SET status_pendaftaran = 'Dinilai' WHERE id_pendaftaran = %s", (id_pd,))
        conn.commit()
        print("Penilaian tersimpan.")
    except Exception as e:
        conn.rollback()
        print("[ERROR]", str(e).split("\n")[0])


def vf_tetapkan(uid):
    judul("PENETAPAN PENERIMA")
    print("(hanya pendaftar berstatus Dinilai)")
    id_pd = pilih_id("""
        SELECT pd.id_pendaftaran, pg.nama_pengguna, j.nama_jalur, ROUND(AVG(n.nilai), 1)
        FROM pendaftaran pd
        JOIN pengguna pg ON pg.id_pengguna = pd.id_pengguna
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        JOIN penilaian n ON n.id_pendaftaran = pd.id_pendaftaran
        WHERE pd.status_pendaftaran = 'Dinilai'
        GROUP BY pd.id_pendaftaran, pg.nama_pengguna, j.nama_jalur
        ORDER BY 1""", (), ["ID", "Mahasiswa", "Jalur", "Rata-rata nilai"], "ID pendaftaran")
    if id_pd == 0:
        return
    data = ambil_satu("SELECT id_jalur FROM pendaftaran WHERE id_pendaftaran = %s", (id_pd,))
    id_jalur = data[0]

    keputusan = menu("KEPUTUSAN", ["Diterima", "Ditolak"])
    if keputusan == "Diterima":
        # Kuota terpakai = jumlah penetapan Diterima dari semua pendaftaran di jalur ini
        sisa = ambil_satu("""
            SELECT j.kuota - COUNT(t.id_penetapan)
            FROM jalur_beasiswa j
            LEFT JOIN pendaftaran p2 ON p2.id_jalur = j.id_jalur
            LEFT JOIN penetapan t ON t.id_pendaftaran = p2.id_pendaftaran AND t.status_keputusan = 'Diterima'
            WHERE j.id_jalur = %s
            GROUP BY j.kuota""", (id_jalur,))
        if sisa is not None and sisa[0] <= 0:
            print("Kuota jalur ini sudah penuh.")
            return
    catatan = input("Catatan keputusan (boleh kosong): ").strip()
    if catatan == "":
        catatan = None
    try:
        cur.execute("""INSERT INTO penetapan (tanggal_penetapan, status_keputusan, catatan_keputusan,
                                              id_pengguna, id_pendaftaran)
                       VALUES (CURRENT_DATE, %s, %s, %s, %s)""", (keputusan, catatan, uid, id_pd))
        cur.execute("UPDATE pendaftaran SET status_pendaftaran = 'Ditetapkan' WHERE id_pendaftaran = %s", (id_pd,))
        conn.commit()
        print("Keputusan " + keputusan + " tersimpan.")
    except Exception as e:
        conn.rollback()
        print("[ERROR]", str(e).split("\n")[0])


def vf_pengumuman(uid):
    pilih = menu("PENGUMUMAN", ["Lihat semua", "Buat baru", "Terbitkan draft", "Kembali"])
    if pilih == "Lihat semua":
        baris = ambil_semua("""SELECT id_pengumuman, judul, tanggal_publikasi, status_pengumuman
                               FROM pengumuman ORDER BY 1""")
        tampil_tabel(["ID", "Judul", "Tanggal", "Status"], baris)
    elif pilih == "Buat baru":
        # Pengumuman selalu terkait satu penetapan
        id_t = pilih_id("""
            SELECT t.id_penetapan, pg.nama_pengguna, j.nama_jalur, t.status_keputusan::text
            FROM penetapan t
            JOIN pendaftaran pd ON pd.id_pendaftaran = t.id_pendaftaran
            JOIN pengguna pg ON pg.id_pengguna = pd.id_pengguna
            JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
            ORDER BY 1""", (), ["ID Penetapan", "Mahasiswa", "Jalur", "Keputusan"], "ID penetapan")
        if id_t != 0:
            status = menu("STATUS", ["Draft", "Terbit"])
            judul_baru = tanya("Judul")
            isi = tanya("Isi")
            if ubah("""INSERT INTO pengumuman (judul, isi_pengumuman, tanggal_publikasi, status_pengumuman,
                                               id_penetapan, id_pengguna)
                       VALUES (%s, %s, CURRENT_DATE, %s, %s, %s)""", (judul_baru, isi, status, id_t, uid)):
                print("Pengumuman disimpan.")
    elif pilih == "Terbitkan draft":
        id_p = pilih_id("SELECT id_pengumuman, judul FROM pengumuman WHERE status_pengumuman = 'Draft' ORDER BY 1",
                        (), ["ID", "Judul"], "ID pengumuman")
        if id_p != 0:
            if ubah("""UPDATE pengumuman SET status_pengumuman = 'Terbit', tanggal_publikasi = CURRENT_DATE
                       WHERE id_pengumuman = %s""", (id_p,)):
                print("Pengumuman diterbitkan.")


def dashboard_verifikator(uid, nama):
    while True:
        banner()
        print("Halo, " + nama + "! (Verifikator " + jenis_verifikator(uid) + ")")
        pilih = menu("MENU VERIFIKATOR", ["Data pendaftaran", "Verifikasi dokumen", "Nilai pendaftar",
                                          "Tetapkan penerima", "Pengumuman", "Logout"])
        if pilih == "Data pendaftaran":
            vf_pendaftaran(uid)
        elif pilih == "Verifikasi dokumen":
            vf_verifikasi(uid)
        elif pilih == "Nilai pendaftar":
            vf_nilai(uid)
        elif pilih == "Tetapkan penerima":
            vf_tetapkan(uid)
        elif pilih == "Pengumuman":
            vf_pengumuman(uid)
        else:
            return
        tunggu()


# =====================================================
# 7. FITUR PETUGAS PENCAIRAN
# =====================================================
def pt_penerima(uid):
    judul("PENERIMA BEASISWA")
    baris = ambil_semua("""
        SELECT t.id_penetapan, pg.nama_pengguna, j.nama_jalur,
               COALESCE((SELECT string_agg(r.nama_bank || ' (' || r.status_validasi || ')', ', ')
                         FROM rekening_bank r WHERE r.id_mahasiswa = pd.id_pengguna),
                        'Belum ada rekening'),
               COALESCE(c.status_pencairan, 'Belum dicairkan')
        FROM penetapan t
        JOIN pendaftaran pd ON pd.id_pendaftaran = t.id_pendaftaran
        JOIN pengguna pg ON pg.id_pengguna = pd.id_pengguna
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        LEFT JOIN pencairan c ON c.id_penetapan = t.id_penetapan
        WHERE t.status_keputusan = 'Diterima'
        ORDER BY 1""")
    tampil_tabel(["ID Penetapan", "Mahasiswa", "Jalur", "Rekening", "Pencairan"], baris)


def pt_validasi(uid):
    judul("VALIDASI REKENING")
    id_rek = pilih_id("""
        SELECT r.id_rekening, pg.nama_pengguna, r.nama_bank, r.nomor_rekening, r.nama_pemilik_rekening
        FROM rekening_bank r JOIN pengguna pg ON pg.id_pengguna = r.id_mahasiswa
        WHERE r.status_validasi = 'Belum Valid'
        ORDER BY 1""", (), ["ID", "Mahasiswa", "Bank", "No. Rekening", "Atas nama"], "ID rekening")
    if id_rek == 0:
        return
    if input("Nama pemilik sesuai dan rekening aktif? Validasi (y/n): ") == "y":
        if ubah("""UPDATE rekening_bank SET status_validasi = 'Valid', id_pengguna = %s
                   WHERE id_rekening = %s""", (uid, id_rek)):
            print("Rekening divalidasi.")


def pt_cairkan(uid):
    judul("PROSES PENCAIRAN")
    id_t = pilih_id("""
        SELECT t.id_penetapan, pg.nama_pengguna, j.nama_jalur, COALESCE(c.status_pencairan, 'Belum dicairkan')
        FROM penetapan t
        JOIN pendaftaran pd ON pd.id_pendaftaran = t.id_pendaftaran
        JOIN pengguna pg ON pg.id_pengguna = pd.id_pengguna
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        LEFT JOIN pencairan c ON c.id_penetapan = t.id_penetapan
        WHERE t.status_keputusan = 'Diterima' AND (c.id_pencairan IS NULL OR c.status_pencairan = 'Tertunda')
        ORDER BY 1""", (), ["ID Penetapan", "Mahasiswa", "Jalur", "Status"], "ID penetapan")
    if id_t == 0:
        return

    rek = ambil_satu("""
        SELECT r.id_rekening, r.nama_bank, r.nomor_rekening
        FROM rekening_bank r
        JOIN pendaftaran pd ON pd.id_pengguna = r.id_mahasiswa
        JOIN penetapan t ON t.id_pendaftaran = pd.id_pendaftaran
        WHERE t.id_penetapan = %s AND r.status_validasi = 'Valid'
        ORDER BY 1 LIMIT 1""", (id_t,))
    if rek is None:
        print("Penerima belum punya rekening berstatus Valid. Validasi rekening dulu.")
        return
    print("Rekening tujuan: " + str(rek[1]) + " " + str(rek[2]))
    nominal = tanya_angka("Nominal (Rp)", 1)

    # Pencairan wajib terkait satu anggaran: pakai anggaran terbaru yang sisanya cukup
    anggaran = ambil_satu("""SELECT id_anggaran FROM anggaran_beasiswa
                             WHERE sisa_anggaran >= %s
                             ORDER BY tahun_anggaran DESC, id_anggaran LIMIT 1""", (nominal,))
    if anggaran is None:
        print("Tidak ada anggaran beasiswa dengan sisa yang cukup.")
        return

    # Nomor referensi: TRX-tanggal-nomor urut (dibuat oleh SQL)
    referensi = ("'TRX-' || to_char(CURRENT_DATE, 'YYYYMMDD') || '-' || "
                 "LPAD((SELECT COUNT(*) + 1 FROM pencairan)::text, 3, '0')")
    sudah_ada = ambil_satu("SELECT id_pencairan FROM pencairan WHERE id_penetapan = %s", (id_t,))

    # Pencairan + pengurangan sisa anggaran dalam satu transaksi
    try:
        if sudah_ada is not None:      # sebelumnya Tertunda: ubah jadi Berhasil
            cur.execute("UPDATE pencairan SET status_pencairan = 'Berhasil', tanggal_pencairan = CURRENT_DATE, "
                        "nominal = %s, referensi_transaksi = " + referensi + ", id_rekening = %s, "
                        "id_pengguna = %s, id_anggaran = %s WHERE id_penetapan = %s",
                        (nominal, rek[0], uid, anggaran[0], id_t))
        else:
            cur.execute("INSERT INTO pencairan (tanggal_pencairan, nominal, status_pencairan, referensi_transaksi, "
                        "id_penetapan, id_rekening, id_pengguna, id_anggaran) "
                        "VALUES (CURRENT_DATE, %s, 'Berhasil', " + referensi + ", %s, %s, %s, %s)",
                        (nominal, id_t, rek[0], uid, anggaran[0]))
        cur.execute("UPDATE anggaran_beasiswa SET sisa_anggaran = sisa_anggaran - %s WHERE id_anggaran = %s",
                    (nominal, anggaran[0]))
        conn.commit()
        print("Pencairan berhasil.")
    except Exception as e:
        conn.rollback()
        print("[ERROR]", str(e).split("\n")[0])


def pt_riwayat(uid):
    judul("RIWAYAT PENCAIRAN")
    baris = ambil_semua("""
        SELECT c.id_pencairan, c.tanggal_pencairan, pg.nama_pengguna, c.nominal, c.status_pencairan,
               COALESCE(c.referensi_transaksi, '-')
        FROM pencairan c
        JOIN penetapan t ON t.id_penetapan = c.id_penetapan
        JOIN pendaftaran pd ON pd.id_pendaftaran = t.id_pendaftaran
        JOIN pengguna pg ON pg.id_pengguna = pd.id_pengguna
        ORDER BY c.id_pencairan""")
    tampil_tabel(["ID", "Tanggal", "Mahasiswa", "Nominal", "Status", "Referensi"], baris)


def pt_anggaran(uid):
    judul("SISA ANGGARAN")
    baris = ambil_semua("""
        SELECT id_anggaran, nama_anggaran, tahun_anggaran,
               total_anggaran, total_anggaran - sisa_anggaran, sisa_anggaran,
               ROUND(sisa_anggaran * 100.0 / NULLIF(total_anggaran, 0), 1)
        FROM anggaran_beasiswa
        ORDER BY tahun_anggaran DESC, id_anggaran""")
    hasil = []
    for b in baris:
        hasil.append((b[0], b[1], b[2], rupiah(b[3]), rupiah(b[4]), rupiah(b[5]), str(b[6]) + "%"))
    tampil_tabel(["ID", "Nama", "Tahun", "Total", "Terpakai", "Sisa", "Sisa (%)"], hasil)


def dashboard_petugas(uid, nama):
    while True:
        banner()
        print("Halo, " + nama + "! (Petugas Pencairan)")
        pilih = menu("MENU PETUGAS PENCAIRAN", ["Daftar penerima beasiswa", "Validasi rekening",
                                                "Proses pencairan", "Riwayat pencairan",
                                                "Lihat anggaran", "Logout"])
        if pilih == "Daftar penerima beasiswa":
            pt_penerima(uid)
        elif pilih == "Validasi rekening":
            pt_validasi(uid)
        elif pilih == "Proses pencairan":
            pt_cairkan(uid)
        elif pilih == "Riwayat pencairan":
            pt_riwayat(uid)
        elif pilih == "Lihat anggaran":
            pt_anggaran(uid)
        else:
            return
        tunggu()


# =====================================================
# 8. MENU UTAMA
# =====================================================
def main():
    while True:
        banner()
        pilih = menu("MENU UTAMA", ["Login", "Registrasi (Mahasiswa)", "Keluar"])
        if pilih == "Login":
            data = login()
            if data is None:
                tunggu()
            elif data[2] == "mahasiswa":
                dashboard_mahasiswa(data[0], data[1])
            elif data[2] == "verifikator":
                dashboard_verifikator(data[0], data[1])
            else:
                dashboard_petugas(data[0], data[1])
        elif pilih == "Registrasi (Mahasiswa)":
            register_mahasiswa()
            tunggu()
        else:
            print("Sampai jumpa!")
            conn.close()
            return


main()