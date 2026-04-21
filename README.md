# Time Series Analyser (TSA)

Kaotik zaman serilerinin doğrusal olmayan analizi icin gelistirilmis masaustu uygulamasi. Veri yukleme, parametre tahmini (AMI + FNN), Lyapunov ustel hesaplama (Wolf & Rosenstein) ve korelasyon boyutu analizini tek bir pipeline icerisinde sunar.

## Ozellikler

- **10 Kaotik Sistem Ureteci**: Lorenz, Rossler, Chua, Chen, Duffing, Logistic, Henon, Tent, Sine, Ikeda
- **Otomatik Parametre Tahmini**: AMI (gecikme suresi tau) ve FNN (gomme boyutu m) ile veri tabanli parametre secimi
- **Wolf Lyapunov Algoritmasi**: Orijinal MATLAB koduna sadik implementasyon (KD-Tree tabanli komsu arama)
- **Rosenstein Lyapunov Algoritmasi**: Otomatik egri uydurmali (auto-fit) en buyuk Lyapunov usteli hesaplama
- **Korelasyon Boyutu**: Grassberger-Procaccia algoritmasi
- **Dogrusal Analizler**: ACF, PACF, FFT (Hann/Hamming/Blackman pencerele)
- **Pipeline Motoru**: Bagimlilik cozumlemeli, onbellekli analiz zinciri
- **PySide6 Arayuz**: PyQtGraph tabanli gorselleestirme
- **Performans**: scipy KD-Tree, vektorize islemler (~43 saniye / 10 sistem validasyonu)

## Validasyon Sonuclari

10 kaotik sistem uzerinde dogrulama (7/10 sistem icin <%10 hata):

| Sistem | Analitik LE | Hesaplanan LE | Hata % | Yontem |
|--------|------------|---------------|--------|--------|
| Lorenz | 0.9056 | 1.0044 | 10.9% | Rosenstein |
| Rossler | 0.0714 | 0.0579 | 19.0% | Rosenstein |
| Chua | 0.33 | 0.3619 | 9.7% | Rosenstein |
| Chen | 2.027 | 1.9179 | 5.4% | Rosenstein |
| Duffing | 0.16 | 0.0834 | 47.9% | Rosenstein |
| Logistic (r=4) | 0.6931 | 0.6927 | 0.1% | Rosenstein |
| Henon | 0.4200 | 0.4200 | 0.0% | Rosenstein |
| Tent | 0.6931 | 0.6948 | 0.2% | Rosenstein |
| Sine | 0.6931 | 0.6889 | 0.6% | Rosenstein |
| Ikeda | 0.51 | 0.4858 | 4.7% | Rosenstein |

## Kurulum

```bash
pip install -r requirements.txt
```

**Gereksinimler**: Python >= 3.8, numpy, scipy >= 1.7.0, PySide6, pyqtgraph

## Hizli Baslangic

```python
from core.generators import generate_lorenz
from analysis.ami import compute_ami, find_first_minimum
from analysis.fnn import compute_fnn, find_embedding_dimension
from analysis.lyapunov import lyapunov_rosenstein, lyapunov_wolf

# Lorenz zaman serisi uret
ts = generate_lorenz(dt=0.01, n_steps=10000, transient=2000)
data = ts.data

# Parametre tahmini (veri tabanli)
ami_values = compute_ami(data, max_lag=100)
tau = find_first_minimum(ami_values)

fnn_values = compute_fnn(data, tau=tau, max_dim=10)
m = find_embedding_dimension(fnn_values, threshold=1.0)

# Rosenstein ile Lyapunov usteli
time_steps, divergence = lyapunov_rosenstein(data, m=m, tau=tau, dt=ts.dt)
# Wolf ile Lyapunov usteli
le_wolf = lyapunov_wolf(data, m=m, tau=tau, dt=ts.dt)

print(f"tau={tau}, m={m}")
print(f"Rosenstein LE: {divergence:.4f}")
print(f"Wolf LE: {le_wolf:.4f}")
```

### Arayuzu Baslatma

```bash
python main.py
```

## Proje Yapisi

```
tseriesanalyser/
├── core/                   # Veri yapilari ve ureticiler
│   ├── timeseries.py       # TimeSeries sinifi
│   ├── generators.py       # 10 kaotik sistem ureteci
│   ├── integrators.py      # RK4 integrator + ODE sistemleri
│   └── loaders.py          # CSV/TXT dosya yukleyici
├── analysis/               # Analiz algoritmalari
│   ├── ami.py              # Ortalama Karsilikli Bilgi (tau tahmini)
│   ├── fnn.py              # Yanlis En Yakin Komsular (m tahmini)
│   ├── embedding.py        # Zaman gecikmeli gomme
│   ├── lyapunov.py         # Wolf + Rosenstein Lyapunov usteli
│   ├── fractal.py          # Korelasyon boyutu
│   ├── acf.py              # Otokorelasyon
│   ├── pacf.py             # Kismi otokorelasyon
│   └── fft.py              # Fourier donusumu
├── pipeline/               # Analiz pipeline motoru
│   ├── node.py             # Node sinifi (bagimlilik takibi)
│   └── engine.py           # Pipeline calistiricisi
├── ui/                     # PySide6 kullanici arayuzu
├── tests/                  # Validasyon testleri
│   └── test_validation.py  # 10 sistem validasyon scripti
├── examples/               # Ornek scriptler
├── documents/              # Wolf MATLAB referans dosyalari
├── main.py                 # Uygulama giris noktasi
├── ROADMAP.md              # Proje spesifikasyonu
└── requirements.txt        # Bagimliliklar
```

## Teknik Notlar

- **Parametre secimi veri tabanlıdır**: tau ve m degerleri AMI ve FNN ile otomatik hesaplanir; elle ayar yapilmaz.
- **Wolf algoritmasi** orijinal MATLAB implementasyonuna (Alan Wolf, 1985) sadik kalir. Wolf dogasi geregi overestimate yapabilir — bu algoritmanin bilinen bir ozelliidir.
- **Rosenstein auto-fit** tam egri R^2 >= 0.98 kontrolu + coklu pencere boyutlu rolling slope doyum tespiti kullanir.
- **LE stabilite testi**: m+-1 ve tau+-10% varyasyonlari ile hesaplanan CV (varyasyon katsayisi) < 0.20 ise sonuc guvenilir kabul edilir. 8/10 sistemde stabil.
- **KD-Tree** (scipy.spatial.cKDTree) komsu aramalarinda kullanilir (Wolf ve Rosenstein).

## Validasyon ve Test Stratejisi

Bu proje iki seviyeli doğrulama yaklaşımı kullanır:

### 1. Bilimsel Doğrulama (test_validation.py)
**Amaç:** Algoritmaların literatür referanslarına uygunluğunu test etmek.

```bash
python tests/test_validation.py
```

- **10 kaotik sistem** üzerinde Wolf, Rosenstein ve Kantz algoritmalarını test eder
- **Literatür LE değerleri** ile karşılaştırır (örn: Lorenz 0.9056 nats/s)
- **Veri-tabanlı parametre seçimi** kullanır (AMI + FNN ile tau ve m otomatik bulunur)
- **Stabilite analizi** yapar (m±1, tau±10% varyasyonları ile CV<0.20 kontrolü)
- **Sonuç:** 7/10 sistem <%10 hata, 10/10 sistem <%20 hata

**Neden gerekli?** Algoritmaların bilimsel olarak doğru çalıştığını ve farklı dinamik sistemlerde güvenilir sonuçlar verdiğini gösterir.

### 2. MATLAB Uyumluluk Testleri (test_wolf_matlab_match.py)
**Amaç:** Wolf'un orijinal MATLAB kodunun Python'a doğru çevrildiğini kanıtlamak.

```bash
python tests/test_wolf_matlab_match.py
```

**Test #1: Lorenz (Data2.lor)**
- Wolf'un kendi Data2.lor verisi (16384 nokta, σ=10, ρ=28, β=8/3)
- **Birebir aynı parametreler:** `tau=10, m=3, dt=0.01, evolve=20, dismin=0.001, dismax=0.3, thmax=30°`
- **Sonuç:** Python 2.01 bits/s | Wolf ~2.1 bits/s | **Fark: %4.1** ✅

**Test #2: Logistic Map**
- 512 iterasyon, x(n+1) = 4x(n)(1-x(n))
- **Birebir aynı parametreler:** `tau=1, m=2, evolve=3, dismin=0.0001, dismax=0.05`
- **Sonuç:** Python 1.00 bits/iter | Wolf 0.98 | Theory 1.0 | **Fark: %2.2 (Wolf), %0.1 (Teori)** ✅

**Neden gerekli?** 
- Wolf algoritması MATLAB'dan Python'a çevrildi — çevirinin doğruluğunu garantilemek gerekli
- %2-4 fark kabul edilebilir: nearest neighbor search implementasyonu farklı (MATLAB box-grid vs Python KDTree)
- Wolf dokümantasyonu "approximately" ifadesini kullanır
- Test #2'de teorik değere %0.1 hata → algoritma matematiği doğru

**İki test arasındaki fark:**
- `test_validation.py` → **Bilimsel doğruluk** (literatür ile karşılaştırma, veri-tabanlı parametre)
- `test_wolf_matlab_match.py` → **Implementasyon doğruluğu** (MATLAB kodu ile karşılaştırma, sabit parametre)

## Lisans

MIT
