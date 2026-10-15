# Aplikasi Teori Graf

Aplikasi desktop untuk membangun dan mempelajari graf tak berarah berbobot.
Antarmukanya dibuat dengan Tkinter, sedangkan graf dirender menggunakan
Matplotlib.

## Fitur

- Menentukan jumlah simpul dan nama setiap simpul.
- Menambahkan dan menghapus sisi dengan bobot jarak atau waktu.
- Menampilkan adjacency list dan adjacency matrix berbobot.
- Mencari rute terpendek dengan Dijkstra, lintasan Euler, lintasan Hamilton,
  atau memeriksa rute yang dimasukkan secara manual.
- Memisahkan pencarian Dijkstra, pemetaan Euler/Hamilton, dan rute manual ke
  tab fitur tersendiri.
- Menampilkan rute pada graf langkah demi langkah, dengan sisi aktif berpanah,
  posisi saat ini, dan bobot akumulatif.
- Mewarnai simpul dengan algoritma greedy dan memilih palet warna.
- Menghitung bilangan kromatik secara tepat. Karena pewarnaan greedy tidak
  selalu menghasilkan jumlah warna minimum, aplikasi menampilkan hasil greedy
  dan bilangan kromatik secara terpisah.

Graf yang digunakan adalah **tak berarah**. Semua bobot dalam satu graf
menggunakan satuan yang sedang dipilih. Bobot harus berupa angka positif.
Untuk Dijkstra, pilih simpul awal dan tujuan. Lintasan Euler mencoba melewati
setiap sisi tepat satu kali (simpul tujuan diabaikan); lintasan Hamilton
mengunjungi setiap simpul tepat satu kali dari simpul awal sampai tujuan.
Gunakan tombol sebelumnya/berikutnya untuk menelusuri ketiga algoritma lintasan.
Panel kontrol memiliki scrollbar agar semua fitur dapat dijangkau pada jendela
atau resolusi layar yang lebih kecil. Pencarian lintasan Hamilton dan bilangan
kromatik eksak dapat memerlukan waktu lebih lama pada graf besar.

## Menjalankan

Pastikan Python 3.10 atau lebih baru dan Tkinter tersedia. Instal Matplotlib,
lalu jalankan aplikasi:

```powershell
python -m pip install -r requirements.txt
python app.py
```

## Pengujian

Jalankan pengujian algoritma graf dengan:

```powershell
python -m unittest discover -s tests -v
```
