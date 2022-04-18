# Server Load Balancing
Berisikan eksplorasi tentang aplikasi serverload balancer di RYU.

Jalankan mininet dengan program yang telah dibuat di  semisal dengan perintah:
```
sudo python3 top
```

tentukan virtual ip server: 10.0.0.100

h1 sebagai client web untuk mengakses bisa gunakan: mininet> h1 curl 10.0.0.100

algoritme untuk berganti-ganti ke server web h2 - h4 cukup gunakan round-robin

h2 s/d h4 sebagai web server: semisal dijalankan dengan perintah dalam console " mininet> h2 python3 -m http.server 80 & " hal yg sama untuk h3 dan h4

Sebagai rujukan code, bisa melakukan modifikasi dari referensi berikut
