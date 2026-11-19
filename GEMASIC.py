"""
GEMASIC - Sistem Informasi Pengelolaan Beasiswa Cinta Bergema (versi CLI sederhana)
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

try:
    conn = psycopg2.connect(dbname="GEMASIC", user="postgres",
                            password="anjaybasda", host="localhost", port="5432")
    cur = conn.cursor()
except Exception as e:
    print("Gagal konek ke database:", e)
    exit()


# =====================================================
# 2. FUNGSI BANTU DATABASE
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
    """Jalankan INSERT / UPDATE. Kembalikan True jika berhasil."""
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
        while tombol != "\r":                 # ulangi sampai ENTER ditekan
            if tombol == "\b":                # Backspace
                if len(password) > 0:
                    password = password[:-1]
                    print("\b \b", end="", flush=True)
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
    """Format YYYY-MM-DD (nilai tanggal yang tidak ada akan ditolak oleh database)."""
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
        SELECT p.id_pengguna, p.nama_pengguna, p.status_akun,
               CASE WHEN m.id_mahasiswa IS NOT NULL THEN 'mahasiswa'
                    WHEN v.id_verifikator IS NOT NULL THEN 'verifikator'
                    ELSE 'petugas' END
        FROM pengguna p
        LEFT JOIN mahasiswa m ON m.id_pengguna = p.id_pengguna
        LEFT JOIN verifikator v ON v.id_pengguna = p.id_pengguna
        WHERE p.email = %s AND p.password = %s""", (email, password))
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
    hp = tanya_digit("No. HP", 8, 20)
    kelurahan = tanya("Kelurahan")
    kecamatan = tanya("Kecamatan")
    kabupaten = tanya("Kabupaten")
    univ = tanya("Nama universitas")
    prodi = tanya("Program studi")

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

        cur.execute("""INSERT INTO pengguna (nama_pengguna, email, password)
                       VALUES (%s, %s, %s) RETURNING id_pengguna""", (nama, email, password))
        id_pengguna = cur.fetchone()[0]

        cur.execute("""INSERT INTO mahasiswa (nim, nik, nama_mahasiswa, tanggal_lahir, no_hp, kelurahan,
                                              kecamatan, kabupaten, id_pengguna, id_program_studi)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (nim, nik, nama, tgl, hp, kelurahan, kecamatan, kabupaten, id_pengguna, id_prodi))
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
        if ubah("INSERT INTO pendaftaran (id_jalur, id_pengguna) VALUES (%s, %s)", (id_jalur, uid)):
            print("Pendaftaran berhasil. Lengkapi dokumen lewat menu Upload dokumen.")


def mhs_upload(uid):
    judul("UPLOAD DOKUMEN")
    id_jenis = pilih_id("SELECT id_jenis_dokumen, nama_jenis_dokumen FROM jenis_dokumen ORDER BY 1", (),
                        ["ID", "Jenis dokumen"], "ID jenis dokumen")
    if id_jenis == 0:
        return
    nama_file = tanya("Nama file (contoh: ktp_saya.pdf)")
    lokasi = tanya("Lokasi file (contoh: /uploads/mhs1/ktp_saya.pdf)")
    if ubah("""INSERT INTO dokumen_persyaratan (nama_file, lokasi_file, jenis_dokumen_id_jenis_dokumen,
                                                mahasiswa_id_pengguna) VALUES (%s, %s, %s, %s)""",
            (nama_file, lokasi, id_jenis, uid)):
        print("Dokumen tersimpan, menunggu verifikasi.")


def mhs_perbaiki(uid):
    judul("LENGKAPI BERKAS PERBAIKAN")
    id_dok = pilih_id("""
        SELECT d.id_dokumen, jd.nama_jenis_dokumen, d.nama_file, d.catatan_verifikasi
        FROM dokumen_persyaratan d
        JOIN jenis_dokumen jd ON jd.id_jenis_dokumen = d.jenis_dokumen_id_jenis_dokumen
        WHERE d.mahasiswa_id_pengguna = %s AND d.status_verifikasi = 'Perbaikan'
        ORDER BY 1""", (uid,), ["ID", "Jenis", "File lama", "Catatan verifikator"], "ID dokumen")
    if id_dok == 0:
        return
    nama_file = tanya("Nama file baru")
    lokasi = tanya("Lokasi file baru")
    if ubah("""UPDATE dokumen_persyaratan SET nama_file = %s, lokasi_file = %s,
               tanggal_upload = CURRENT_DATE, status_verifikasi = 'Menunggu'
               WHERE id_dokumen = %s""", (nama_file, lokasi, id_dok)):
        print("Berkas perbaikan terkirim.")


def mhs_status(uid):
    judul("STATUS PENDAFTARAN")
    baris = ambil_semua("""
        SELECT pd.id_pendaftaran, j.nama_jalur, pd.tanggal_daftar,
               COALESCE(pt.status_keputusan, 'Dalam proses'), COALESCE(c.status_pencairan, '-')
        FROM pendaftaran pd
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        LEFT JOIN penetapan pt ON pt.jalur_beasiswa_id_jalur = pd.id_jalur
                              AND pt.mahasiswa_id_pengguna = pd.id_pengguna
        LEFT JOIN pencairan c ON c.penetapan_id_penetapan = pt.id_penetapan
        WHERE pd.id_pengguna = %s
        ORDER BY pd.id_pendaftaran""", (uid,))
    tampil_tabel(["ID", "Jalur", "Tanggal daftar", "Status", "Pencairan"], baris)

    judul("STATUS DOKUMEN")
    baris = ambil_semua("""
        SELECT d.id_dokumen, jd.nama_jenis_dokumen, d.nama_file, d.status_verifikasi,
               COALESCE(d.catatan_verifikasi, '-')
        FROM dokumen_persyaratan d
        JOIN jenis_dokumen jd ON jd.id_jenis_dokumen = d.jenis_dokumen_id_jenis_dokumen
        WHERE d.mahasiswa_id_pengguna = %s
        ORDER BY d.id_dokumen""", (uid,))
    tampil_tabel(["ID", "Jenis", "File", "Status", "Catatan"], baris)


def mhs_pengumuman(uid):
    judul("PENGUMUMAN")
    baris = ambil_semua("""SELECT tanggal_publikasi, judul, isi_pengumuman FROM pengumuman
                           WHERE status_pengumuman = 'Terbit' ORDER BY tanggal_publikasi DESC""")
    if len(baris) == 0:
        print("(belum ada pengumuman)")
    for b in baris:
        print("\n[" + str(b[0]) + "] " + b[1])
        print("  " + b[2])


def mhs_rekening(uid):
    judul("REKENING BANK")
    baris = ambil_semua("""SELECT id_rekening, nama_bank, nomor_rekening, nama_pemilik_rekening, status_validasi
                           FROM rekening_bank WHERE mahasiswa_id_pengguna = %s ORDER BY 1""", (uid,))
    tampil_tabel(["ID", "Bank", "No. Rekening", "Atas nama", "Status"], baris)
    if input("Ajukan rekening baru? (y/n): ") == "y":
        bank = tanya("Nama bank")
        nomor = tanya_digit("Nomor rekening", 5, 30)
        atas_nama = tanya("Atas nama")
        if ubah("""INSERT INTO rekening_bank (nama_bank, nomor_rekening, nama_pemilik_rekening,
                                               mahasiswa_id_pengguna) VALUES (%s, %s, %s, %s)""",
                (bank, nomor, atas_nama, uid)):
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
def vf_info(uid):
    """Kembalikan (id_verifikator, jenis_verifikator)."""
    return ambil_satu("SELECT id_verifikator, jenis_verifikator FROM verifikator WHERE id_pengguna = %s", (uid,))


def vf_pendaftaran(uid):
    judul("DATA PENDAFTARAN")
    baris = ambil_semua("""
        SELECT pd.id_pendaftaran, m.nama_mahasiswa, u.nama_universitas, j.nama_jalur, pd.tanggal_daftar,
               COALESCE(pt.status_keputusan, 'Dalam proses')
        FROM pendaftaran pd
        JOIN mahasiswa m ON m.id_pengguna = pd.id_pengguna
        JOIN program_studi ps ON ps.id_program_studi = m.id_program_studi
        JOIN universitas u ON u.id_universitas = ps.id_universitas
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        LEFT JOIN penetapan pt ON pt.jalur_beasiswa_id_jalur = pd.id_jalur
                              AND pt.mahasiswa_id_pengguna = pd.id_pengguna
        ORDER BY pd.id_pendaftaran""")
    tampil_tabel(["ID", "Mahasiswa", "Universitas", "Jalur", "Tanggal", "Status"], baris)


def vf_verifikasi(uid):
    judul("VERIFIKASI DOKUMEN")
    info = vf_info(uid)
    id_verifikator = info[0]
    jenis = info[1]
    print("Verifikator " + jenis)

    # Tiap jenis verifikator hanya memeriksa dokumen miliknya
    if jenis == "Tahfidz":
        filter_jenis = "jd.nama_jenis_dokumen = 'Sertifikat Hafalan Al-Quran'"
    elif jenis == "PTN":
        filter_jenis = "jd.nama_jenis_dokumen IN ('Kartu Tanda Mahasiswa (KTM)', 'Transkrip Nilai')"
    else:
        filter_jenis = ("jd.nama_jenis_dokumen NOT IN ('Sertifikat Hafalan Al-Quran', "
                        "'Kartu Tanda Mahasiswa (KTM)', 'Transkrip Nilai')")

    sql = """
        SELECT d.id_dokumen, m.nama_mahasiswa, jd.nama_jenis_dokumen, d.nama_file
        FROM dokumen_persyaratan d
        JOIN jenis_dokumen jd ON jd.id_jenis_dokumen = d.jenis_dokumen_id_jenis_dokumen
        JOIN mahasiswa m ON m.id_pengguna = d.mahasiswa_id_pengguna
        WHERE d.status_verifikasi = 'Menunggu' AND """ + filter_jenis + " ORDER BY 1"
    id_dok = pilih_id(sql, (), ["ID", "Mahasiswa", "Jenis", "File"], "ID dokumen")
    if id_dok == 0:
        return

    hasil = menu("HASIL", ["Valid", "Perbaikan"])
    catatan = tanya("Catatan verifikasi")
    try:
        cur.execute("""UPDATE dokumen_persyaratan SET status_verifikasi = %s, catatan_verifikasi = %s,
                       verifikator_id_verifikator = %s WHERE id_dokumen = %s""",
                    (hasil, catatan, id_verifikator, id_dok))
        cur.execute("""UPDATE verifikator SET tanggal_verifikasi = CURRENT_DATE, catatan_verifikasi = %s
                       WHERE id_verifikator = %s""", (catatan, id_verifikator))
        conn.commit()
        print("Hasil verifikasi disimpan.")
    except Exception as e:
        conn.rollback()
        print("[ERROR]", str(e).split("\n")[0])


def vf_nilai(uid):
    judul("PENILAIAN KELAYAKAN")
    print("(hanya pendaftar yang seluruh dokumennya sudah Valid)")
    id_pd = pilih_id("""
        SELECT pd.id_pendaftaran, m.nama_mahasiswa, j.nama_jalur
        FROM pendaftaran pd
        JOIN mahasiswa m ON m.id_pengguna = pd.id_pengguna
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        WHERE EXISTS (SELECT 1 FROM dokumen_persyaratan d WHERE d.mahasiswa_id_pengguna = pd.id_pengguna)
          AND NOT EXISTS (SELECT 1 FROM dokumen_persyaratan d
                          WHERE d.mahasiswa_id_pengguna = pd.id_pengguna AND d.status_verifikasi <> 'Valid')
          AND NOT EXISTS (SELECT 1 FROM penilaian n
                          WHERE n.pendaftaran_id_pendaftaran = pd.id_pendaftaran AND n.pengguna_id_pengguna = %s)
        ORDER BY 1""", (uid,), ["ID", "Mahasiswa", "Jalur"], "ID pendaftaran")
    if id_pd == 0:
        return
    nilai = tanya_angka("Nilai (0-100)", 0, 100)
    catatan = tanya("Catatan penilaian")
    if ubah("""INSERT INTO penilaian (nilai, catatan_penilaian, pendaftaran_id_pendaftaran, pengguna_id_pengguna)
               VALUES (%s, %s, %s, %s)""", (nilai, catatan, id_pd, uid)):
        print("Penilaian tersimpan.")


def vf_tetapkan(uid):
    judul("PENETAPAN PENERIMA")
    id_pd = pilih_id("""
        SELECT pd.id_pendaftaran, m.nama_mahasiswa, j.nama_jalur, ROUND(AVG(n.nilai), 1)
        FROM pendaftaran pd
        JOIN mahasiswa m ON m.id_pengguna = pd.id_pengguna
        JOIN jalur_beasiswa j ON j.id_jalur = pd.id_jalur
        JOIN penilaian n ON n.pendaftaran_id_pendaftaran = pd.id_pendaftaran
        WHERE NOT EXISTS (SELECT 1 FROM penetapan t WHERE t.jalur_beasiswa_id_jalur = pd.id_jalur
                          AND t.mahasiswa_id_pengguna = pd.id_pengguna)
        GROUP BY pd.id_pendaftaran, m.nama_mahasiswa, j.nama_jalur
        ORDER BY 1""", (), ["ID", "Mahasiswa", "Jalur", "Rata-rata nilai"], "ID pendaftaran")
    if id_pd == 0:
        return
    keputusan = menu("KEPUTUSAN", ["Diterima", "Ditolak"])
    if keputusan == "Diterima":
        sisa = ambil_satu("""
            SELECT j.kuota - COUNT(t.id_penetapan)
            FROM jalur_beasiswa j
            LEFT JOIN penetapan t ON t.jalur_beasiswa_id_jalur = j.id_jalur AND t.status_keputusan = 'Diterima'
            WHERE j.id_jalur = (SELECT id_jalur FROM pendaftaran WHERE id_pendaftaran = %s)
            GROUP BY j.kuota""", (id_pd,))
        if sisa is not None and sisa[0] <= 0:
            print("Kuota jalur ini sudah penuh.")
            return
    catatan = input("Catatan keputusan (boleh kosong): ").strip()
    if catatan == "":
        catatan = None
    if ubah("""INSERT INTO penetapan (status_keputusan, catatan_keputusan, pengguna_id_pengguna,
                                      jalur_beasiswa_id_jalur, mahasiswa_id_pengguna)
               SELECT %s, %s, %s, id_jalur, id_pengguna FROM pendaftaran WHERE id_pendaftaran = %s""",
            (keputusan, catatan, uid, id_pd)):
        print("Keputusan " + keputusan + " tersimpan.")


def vf_pengumuman(uid):
    pilih = menu("PENGUMUMAN", ["Lihat semua", "Buat baru", "Terbitkan draft", "Kembali"])
    if pilih == "Lihat semua":
        baris = ambil_semua("""SELECT id_pengumuman, judul, tanggal_publikasi, status_pengumuman
                               FROM pengumuman ORDER BY 1""")
        tampil_tabel(["ID", "Judul", "Tanggal", "Status"], baris)
    elif pilih == "Buat baru":
        status = menu("STATUS", ["Draft", "Terbit"])
        judul_baru = tanya("Judul")
        isi = tanya("Isi")
        if ubah("""INSERT INTO pengumuman (judul, isi_pengumuman, status_pengumuman, pengguna_id_pengguna)
                   VALUES (%s, %s, %s, %s)""", (judul_baru, isi, status, uid)):
            print("Pengumuman disimpan.")
    elif pilih == "Terbitkan draft":
        id_p = pilih_id("SELECT id_pengumuman, judul FROM pengumuman WHERE status_pengumuman = 'Draft' ORDER BY 1",
                        (), ["ID", "Judul"], "ID pengumuman")
        if id_p != 0:
            if ubah("""UPDATE pengumuman SET status_pengumuman = 'Terbit', tanggal_publikasi = CURRENT_DATE
                       WHERE id_pengumuman = %s""", (id_p,)):
                print("Pengumuman diterbitkan.")


def vf_jalur(uid):
    pilih = menu("KELOLA JALUR & PERSYARATAN", ["Lihat", "Tambah jalur", "Tambah persyaratan", "Ubah kuota", "Kembali"])
    if pilih == "Lihat":
        baris = ambil_semua("""
            SELECT j.id_jalur, j.nama_jalur, j.kuota, COUNT(p.id_persyaratan)
            FROM jalur_beasiswa j LEFT JOIN persyaratan p ON p.id_jalur = j.id_jalur
            GROUP BY j.id_jalur ORDER BY 1""")
        tampil_tabel(["ID", "Jalur", "Kuota", "Jumlah persyaratan"], baris)
    elif pilih == "Tambah jalur":
        nama = tanya("Nama jalur")
        deskripsi = tanya("Deskripsi")
        kuota = tanya_angka("Kuota", 1)
        if ubah("""INSERT INTO jalur_beasiswa (nama_jalur, deskripsi, kuota, id_pengguna)
                   VALUES (%s, %s, %s, %s)""", (nama, deskripsi, kuota, uid)):
            print("Jalur ditambahkan.")
    elif pilih == "Tambah persyaratan":
        id_j = pilih_id("SELECT id_jalur, nama_jalur FROM jalur_beasiswa ORDER BY 1", (), ["ID", "Jalur"], "ID jalur")
        if id_j != 0:
            nama = tanya("Nama persyaratan")
            deskripsi = tanya("Deskripsi")
            if ubah("""INSERT INTO persyaratan (nama_persyaratan, deskripsi_persyaratan, id_jalur)
                       VALUES (%s, %s, %s)""", (nama, deskripsi, id_j)):
                print("Persyaratan ditambahkan.")
    elif pilih == "Ubah kuota":
        id_j = pilih_id("SELECT id_jalur, nama_jalur, kuota FROM jalur_beasiswa ORDER BY 1", (),
                        ["ID", "Jalur", "Kuota"], "ID jalur")
        if id_j != 0:
            kuota = tanya_angka("Kuota baru", 1)
            if ubah("UPDATE jalur_beasiswa SET kuota = %s WHERE id_jalur = %s", (kuota, id_j)):
                print("Kuota diperbarui.")


def vf_laporan(uid):
    judul("LAPORAN SISTEM")
    baris = ambil_semua("""
        SELECT j.nama_jalur, j.kuota,
               (SELECT COUNT(*) FROM pendaftaran pd WHERE pd.id_jalur = j.id_jalur),
               (SELECT COUNT(*) FROM penetapan t
                WHERE t.jalur_beasiswa_id_jalur = j.id_jalur AND t.status_keputusan = 'Diterima'),
               (SELECT COUNT(*) FROM penetapan t
                WHERE t.jalur_beasiswa_id_jalur = j.id_jalur AND t.status_keputusan = 'Ditolak')
        FROM jalur_beasiswa j ORDER BY j.id_jalur""")
    tampil_tabel(["Jalur", "Kuota", "Pendaftar", "Diterima", "Ditolak"], baris)
    total = ambil_satu("SELECT COALESCE(SUM(nominal), 0) FROM pencairan WHERE status_pencairan = 'Berhasil'")
    print("Total dana tersalurkan:", rupiah(total[0]))


def dashboard_verifikator(uid, nama):
    while True:
        banner()
        print("Halo, " + nama + "! (Verifikator " + vf_info(uid)[1] + ")")
        pilih = menu("MENU VERIFIKATOR", ["Data pendaftaran", "Verifikasi dokumen", "Nilai pendaftar",
                                          "Tetapkan penerima", "Pengumuman", "Kelola jalur & persyaratan",
                                          "Laporan sistem", "Logout"])
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
        elif pilih == "Kelola jalur & persyaratan":
            vf_jalur(uid)
        elif pilih == "Laporan sistem":
            vf_laporan(uid)
        else:
            return
        tunggu()


# =====================================================
# 7. FITUR PETUGAS PENCAIRAN
# =====================================================
def pt_penerima(uid):
    judul("PENERIMA BEASISWA")
    baris = ambil_semua("""
        SELECT t.id_penetapan, m.nama_mahasiswa, j.nama_jalur,
               COALESCE((SELECT string_agg(r.nama_bank || ' (' || r.status_validasi || ')', ', ')
                         FROM rekening_bank r WHERE r.mahasiswa_id_pengguna = t.mahasiswa_id_pengguna),
                        'Belum ada rekening'),
               COALESCE(c.status_pencairan, 'Belum dicairkan')
        FROM penetapan t
        JOIN mahasiswa m ON m.id_pengguna = t.mahasiswa_id_pengguna
        JOIN jalur_beasiswa j ON j.id_jalur = t.jalur_beasiswa_id_jalur
        LEFT JOIN pencairan c ON c.penetapan_id_penetapan = t.id_penetapan
        WHERE t.status_keputusan = 'Diterima'
        ORDER BY 1""")
    tampil_tabel(["ID Penetapan", "Mahasiswa", "Jalur", "Rekening", "Pencairan"], baris)


def pt_validasi(uid):
    judul("VALIDASI REKENING")
    id_rek = pilih_id("""
        SELECT r.id_rekening, m.nama_mahasiswa, r.nama_bank, r.nomor_rekening, r.nama_pemilik_rekening
        FROM rekening_bank r JOIN mahasiswa m ON m.id_pengguna = r.mahasiswa_id_pengguna
        WHERE r.status_validasi = 'Belum Valid'
        ORDER BY 1""", (), ["ID", "Mahasiswa", "Bank", "No. Rekening", "Atas nama"], "ID rekening")
    if id_rek == 0:
        return
    if input("Nama pemilik sesuai dan rekening aktif? Validasi (y/n): ") == "y":
        if ubah("""UPDATE rekening_bank SET status_validasi = 'Valid', pengguna_id_pengguna = %s
                   WHERE id_rekening = %s""", (uid, id_rek)):
            print("Rekening divalidasi.")


def pt_cairkan(uid):
    judul("PROSES PENCAIRAN")
    id_t = pilih_id("""
        SELECT t.id_penetapan, m.nama_mahasiswa, j.nama_jalur, COALESCE(c.status_pencairan, 'Belum dicairkan')
        FROM penetapan t
        JOIN mahasiswa m ON m.id_pengguna = t.mahasiswa_id_pengguna
        JOIN jalur_beasiswa j ON j.id_jalur = t.jalur_beasiswa_id_jalur
        LEFT JOIN pencairan c ON c.penetapan_id_penetapan = t.id_penetapan
        WHERE t.status_keputusan = 'Diterima' AND (c.id_pencairan IS NULL OR c.status_pencairan = 'Tertunda')
        ORDER BY 1""", (), ["ID Penetapan", "Mahasiswa", "Jalur", "Status"], "ID penetapan")
    if id_t == 0:
        return

    rek = ambil_satu("""
        SELECT r.id_rekening, r.nama_bank, r.nomor_rekening
        FROM rekening_bank r JOIN penetapan t ON t.mahasiswa_id_pengguna = r.mahasiswa_id_pengguna
        WHERE t.id_penetapan = %s AND r.status_validasi = 'Valid'
        ORDER BY 1 LIMIT 1""", (id_t,))
    if rek is None:
        print("Penerima belum punya rekening berstatus Valid. Validasi rekening dulu.")
        return
    print("Rekening tujuan: " + str(rek[1]) + " " + str(rek[2]))
    nominal = tanya_angka("Nominal (Rp)", 1)

    # Nomor referensi: TRX-tanggal-nomor urut (dibuat oleh SQL)
    referensi = ("'TRX-' || to_char(CURRENT_DATE, 'YYYYMMDD') || '-' || "
                 "LPAD((SELECT COUNT(*) + 1 FROM pencairan)::text, 3, '0')")
    sudah_ada = ambil_satu("SELECT id_pencairan FROM pencairan WHERE penetapan_id_penetapan = %s", (id_t,))
    if sudah_ada is not None:      # sebelumnya Tertunda: ubah jadi Berhasil
        sql = ("UPDATE pencairan SET status_pencairan = 'Berhasil', tanggal_pencairan = CURRENT_DATE, "
               "nominal = %s, referensi_transaksi = " + referensi + ", rekening_bank_id_rekening = %s, "
               "pengguna_id_pengguna = %s WHERE penetapan_id_penetapan = %s")
        berhasil = ubah(sql, (nominal, rek[0], uid, id_t))
    else:
        sql = ("INSERT INTO pencairan (nominal, status_pencairan, referensi_transaksi, penetapan_id_penetapan, "
               "rekening_bank_id_rekening, pengguna_id_pengguna) VALUES (%s, 'Berhasil', " + referensi +
               ", %s, %s, %s)")
        berhasil = ubah(sql, (nominal, id_t, rek[0], uid))
    if berhasil:
        print("Pencairan berhasil.")


def pt_riwayat(uid):
    judul("RIWAYAT PENCAIRAN")
    baris = ambil_semua("""
        SELECT c.id_pencairan, c.tanggal_pencairan, m.nama_mahasiswa, c.nominal, c.status_pencairan,
               COALESCE(c.referensi_transaksi, '-')
        FROM pencairan c
        JOIN penetapan t ON t.id_penetapan = c.penetapan_id_penetapan
        JOIN mahasiswa m ON m.id_pengguna = t.mahasiswa_id_pengguna
        ORDER BY c.id_pencairan""")
    tampil_tabel(["ID", "Tanggal", "Mahasiswa", "Nominal", "Status", "Referensi"], baris)


def dashboard_petugas(uid, nama):
    while True:
        banner()
        print("Halo, " + nama + "! (Petugas Pencairan)")
        pilih = menu("MENU PETUGAS PENCAIRAN", ["Daftar penerima beasiswa", "Validasi rekening",
                                                "Proses pencairan", "Riwayat pencairan", "Logout"])
        if pilih == "Daftar penerima beasiswa":
            pt_penerima(uid)
        elif pilih == "Validasi rekening":
            pt_validasi(uid)
        elif pilih == "Proses pencairan":
            pt_cairkan(uid)
        elif pilih == "Riwayat pencairan":
            pt_riwayat(uid)
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