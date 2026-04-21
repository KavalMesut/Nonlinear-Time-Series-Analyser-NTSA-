\# NONLINEAR TIME SERIES ANALYZER — BUILD SPEC



\## AMAÇ



Bu uygulama:



\* TXT / CSV zaman serisi

\* Diferansiyel denklem sistemleri

\* Ayrık map’ler



üzerinde doğrulanabilir nonlinear zaman serisi analizi yapar.



Zorunlu referans sistemler:



\* Lorenz system

\* Rössler system

\* Logistic map



\---



\## PLATFORM (KESİN KARAR)



Bu proje \*\*desktop uygulaması (.exe)\*\* olacaktır.



\### Teknoloji



\* UI: PySide6

\* Grafik: PyQtGraph



\### Paketleme



\* PyInstaller



\### YASAKLAR



\* Web UI YOK

\* Sunucu bağımlılığı YOK

\* Offline çalışmak zorunda



\---



\## GENEL MİMARİ



\### Katmanlar



1\. core → veri ve sistem üretimi

2\. pipeline → bağımlılık ve yürütme

3\. analysis → tüm matematik

4\. ui → görselleştirme



\---



\## KLASÖR YAPISI



```id="k1"

core/

&#x20;   timeseries.py

&#x20;   generators.py

&#x20;   integrators.py



pipeline/

&#x20;   node.py

&#x20;   engine.py



analysis/

&#x20;   acf.py

&#x20;   pacf.py

&#x20;   fft.py

&#x20;   ami.py

&#x20;   fnn.py

&#x20;   embedding.py

&#x20;   lyapunov.py

&#x20;   fractal.py



ui/

&#x20;   main\_window.py

&#x20;   panels/



tests/

examples/

```



\---



\## FAZ 1 — CORE



\### TimeSeries



```python id="k2"

class TimeSeries:

&#x20;   data: np.ndarray

&#x20;   dt: float

&#x20;   metadata: dict

```



\### Giriş türleri



\* CSV / TXT loader (tek sütun başlangıç)

\* RK4 integrator (kendin yaz)

\* Map generator



Desteklenecek:



\* Lorenz

\* Rössler

\* Logistic map



\---



\## FAZ 2 — PIPELINE (KRİTİK)



\### Node yapısı



```python id="k3"

class Node:

&#x20;   name: str

&#x20;   requires: list

&#x20;   produces: list

&#x20;   def run(state, params): ...

```



\### Engine



\* dependency check

\* eksik veri → çalıştırma

\* sonuç cache

\* state dictionary kullan



\---



\## FAZ 3 — ANALİZLER



\### Lineer



\* ACF

\* PACF

\* FFT (power spectrum, windowing ile)



\### Nonlineer



\* AMI → τ

\* FNN → m

\* Embedding



\---



\## FAZ 4 — KAOS ANALİZİ



\* Lyapunov exponent (Wolf)

\* Correlation dimension

\* Entropy (sample / permutation)

\* Recurrence plot (opsiyonel)



\---



\## FAZ 5 — PARAMETRE YÖNETİMİ



\* τ otomatik: AMI first minimum

\* m otomatik: FNN threshold

\* manuel override

\* sapma varsa uyarı



\---



\## FAZ 6 — UI



\### Layout



\* Sol panel: adımlar listesi (kilitli/açık)

\* Sağ panel:



&#x20; \* veri görünümü

&#x20; \* grafik alanı



\### Grafik özellikleri



\* zoom / pan

\* ROI seç → yeni veri üret

\* lag slider (τ)

\* overlay grafik



\---



\## FAZ 7 — DOĞRULAMA (ZORUNLU)



Beklenen sonuçlar:



Lorenz:



\* Lyapunov ≈ 0.9



Rössler:



\* Lyapunov ≈ 0.07



Logistic (r=4):



\* Lyapunov ≈ ln(2)



Negatif test:



\* sinüs

\* beyaz gürültü



\---



\## FAZ 8 — EXPORT



\* CSV → veri

\* PNG → grafik

\* JSON → parametreler + metadata



\---



\## FAZ 9 — PERFORMANS



\* multiprocessing veya thread

\* tekrar hesaplama yok (cache)



\---



\## GELİŞTİRME KURALLARI



\* Önce pipeline sonra UI

\* Her modül test edilmeli

\* Parametreler hardcode edilmeyecek

\* Ara sonuçlar kaybolmayacak



\---



\## KRİTİK UYARILAR



\* Lyapunov ve FNN yanlış implement edilirse tüm sonuç çöker

\* Parametre seçimi sonuçtan daha önemli

\* Test etmeden ilerlemek yasak



\---



\## GELİŞTİRME SIRASI



1\. core

2\. pipeline

3\. analizler

4\. doğrulama

5\. ui

6\. export


Sıra değiştirme.


\---

## GELECEK GÖREVLER (TODO)

### Yüksek Öncelik
- [ ] PyInstaller ile .exe paketleme
  - Windows için standalone executable
  - Tüm bağımlılıkları dahil et (scipy, PySide6, pyqtgraph)
  - İkon ve metadata ekle
  
- [ ] Kullanıcı Dokümantasyonu
  - Nasıl kullanılır kılavuzu (Türkçe + İngilizce)
  - Her analiz adımı için açıklamalar
  - Screenshot'lar ile örnek workflow
  - PDF export

### Orta Öncelik
- [ ] Embedding Visualization (Step 5)
  - 2D/3D phase space plot
  - Poincaré kesitleri
  
- [ ] Results Summary Panel (Step 7)
  - Tüm sonuçların özeti
  - Karşılaştırma tablosu
  - Export to LaTeX table

### Düşük Öncelik
- [ ] Batch Processing
  - Birden fazla dosya üzerinde otomatik analiz
  - Sonuçları CSV/Excel tablosuna export
  
- [ ] Advanced Preprocessing
  - Adaptive filtering
  - Signal decomposition (EMD, VMD)

\---


2\. pipeline

3\. analizler

4\. doğrulama

5\. ui

6\. export



Sıra değiştirme.



\---



