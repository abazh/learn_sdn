# Shortest Path forwarding
Berisikan eksplorasi tentang aplikasi shortest path forwarding di RYU.

1. Jalankan mininet dengan program dengan perintah pada salah satu terminal console:
```
sudo python3 topo-spf_lab.py
```
2. Jalankan aplikasi `dijkstra_Ryu_controller.py` pada Ryu controller dengan `ryu-manager` pada terminal console lainnya:
```
ryu-manager --observe-links dijkstra_Ryu_controller.py
```

Pada program `topo-spf_lab.py` akan membentuk topologi yang terdapat loopnya seperti ![topology] yang terdiri atas 6 hosts (h1 - h6) dan 3 switch (s1, s2, s3) dengan skenario sebagai berikut:
- semua host (h1 - h6) harus dapat terhubung satu sama lain dan menggunakan jalur terpendek
  ```
  mininet> h1 ping h6
  ```
- ujicoba pemutusan salah satu jalur, semisal
  ```
  mininet> link s1 s2 down
  mininet> h1 ping h6
  ```
Pada saat ping sebelum dan setelah `link s1 s2 down` amati path terpilih pada terminal yang menjalankan aplikasi dijkstra dengan ryu-manager `dijkstra_Ryu_controller.py` 
Lakukan verifikasi pada table flow pada switch terkait apa saja yang berubah
```
mininet> dpctl dump-flows -O OpenFlow13
```
Lakukan beberapa ujicoba dengan kombinasi host lainnya atau pun pemutusan jalur lainnya, dan amati apa yang tampil pada terminal console yang menjalankan `ryu-manager --observe-links dijkstra_Ryu_controller.py` atau pun pada terminal console yang menjalankan `sudo python3 topo-spf_lab.py` 

