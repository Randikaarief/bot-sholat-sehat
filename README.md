# 🕌🌱 Bot Asisten Pengingat Sholat 5 Waktu, Jam Tidur & Pola Hidup Sehat

Bot Telegram serba bisa yang dirancang sebagai asisten pribadi untuk menjaga waktu ibadah, pola tidur berkualitas, hidrasi tubuh, dan pola hidup sehat, lengkap dengan integrasi pemicu alarm di HP.

---

## 🌟 Fitur Utama

1. **🕌 Jadwal Sholat 5 Waktu & Alarm Adzan Otomatis:**
   - Terhubung dengan API Jadwal Sholat resmi (Metode Kemenag RI / Aladhan API).
   - Pengingat berjenjang:
     - **10 menit sebelum waktu sholat**: Mengingatkan untuk mengambil wudhu dan bersiap.
     - **Tepat saat adzan berkumandang**: Notifikasi adzan lengkap dengan lafadz adzan, doa setelah adzan, dan penanda `#ALARM_SHOLAT`.
   - Lokasi default: **Surabaya** (dapat diubah dengan mudah melalui perintah `/kota <Nama Kota>`).

2. **🌙 Pola Tidur Sehat & Alarm Bangun Pagi:**
   - **Alarm Tidur Malam**: Mengingatkan tidur tepat waktu (default 22:00 WIB atau kustom via `/settidur`) disertai doa sebelum tidur dan tips relaksasi.
   - **Alarm Bangun Pagi**: Mengingatkan bangun segar (default 04:30 WIB atau kustom via `/setbangun`) disertai doa bangun tidur dan ajakan minum air hangat.

3. **💧 Pelacak & Pengingat Minum Air Putih:**
   - Pengingat hidrasi berkala di siang hari.
   - Tombol satu klik: `[💧 Catat Minum (+1 Gelas)]` dengan visual progress bar menuju target 8 gelas (~2 liter) per hari.

4. **🔔 Dukungan Pemicu Alarm di HP:**
   - **Metode 1 (Mudah):** Mengatur suara notifikasi khusus chat bot di Telegram menjadi nada alarm/adzan panjang.
   - **Metode 2 (Alarm Asli HP):** Menggunakan aplikasi otomasi Android (MacroDroid) dengan pemicu tagar `#ALARM_SHOLAT`, `#ALARM_TIDUR`, atau `#ALARM_BANGUN` agar jam weker sistem HP berdering dengan volume 100%.

---

## 📱 Daftar Perintah Bot Telegram

| Perintah | Deskripsi |
| :--- | :--- |
| `/start` | Memulai bot dan menampilkan menu navigasi utama |
| `/jadwal` | Menampilkan jadwal sholat 5 waktu hari ini |
| `/kota <nama>` | Mengganti kota lokasi jadwal sholat (contoh: `/kota Surabaya`) |
| `/sehat` | Membuka dashboard pola hidup sehat & pelacak hidrasi |
| `/minum` | Mencatat +1 gelas air putih hari ini |
| `/tidur` | Pengaturan jadwal alarm tidur dan bangun |
| `/settidur <JJ:MM>` | Mengatur jam alarm tidur malam (contoh: `/settidur 22:00`) |
| `/setbangun <JJ:MM>` | Mengatur jam alarm bangun pagi (contoh: `/setbangun 04:30`) |
| `/alarm` | Panduan lengkap menyetel alarm HP berdering keras |

---

## 🔔 Panduan Menjadikan Notifikasi Bot Sebagai Alarm di HP

### Cara 1: Nada Dering Khusus di Telegram (Paling Mudah)
1. Buka ruang obrolan dengan **@randikariefbot** di HP Anda.
2. Ketuk nama bot di bagian atas untuk membuka profil.
3. Ketuk menu **Notifikasi (*Notifications*)** -> pilih **Kustomisasi (*Customize*)**.
4. Aktifkan **Notifikasi Kustom**.
5. Pada bagian **Suara (*Sound*)**: Pilih nada alarm yang panjang atau file rekaman suara adzan.
6. Pada bagian **Prioritas (*Priority*)**: Pilih **Tinggi/Maksimal** agar tetap berdering saat HP terkunci.

### Cara 2: Membunyikan Jam Weker Sistem HP (via MacroDroid di Android)
1. Pasang aplikasi **MacroDroid** dari Google Play Store.
2. Tambahkan Macro baru:
   - **Pemicu (Trigger):** *Notifikasi Diterima -> Pilih Aplikasi Telegram -> Isi Teks Memuat:* `#ALARM`
   - **Tindakan (Action):** *Tanggal/Waktu -> Bunyikan Alarm (Set Alarm) atau Putar Audio Alarm pada Volume 100%*.
3. Selesai! Saat bot mengirim notifikasi sholat atau tidur, HP akan langsung membunyikan alarm jam weker sistem.

---

## 🚀 Menjalankan Bot Secara Lokal

```bash
# 1. Masuk ke direktori dan aktifkan venv
cd d:\ngoding\bot
.\.venv\Scripts\activate

# 2. Jalankan bot
python -m app.main
```
Endpoint monitoring dapat diakses di: `http://localhost:8000/health`.
