# CLAUDE.md

Bu dosya, bu repoda çalışan Claude (Claude Code / Claude Agent) örnekleri için kalıcı yönergedir. Projeyi her oturumda baştan keşfetmesin diye hazırlanmıştır. **Türkçe** öncelikli, ama kod sembolleri ve commit mesajları İngilizce kalabilir.

---

## 1. Projenin Asıl Amacı

Bu uygulama, **kullanıcının kendi zaman serileri** veya **kendi tanımladığı ODE / discrete map sistemleri** üzerinde, doğrulanabilir nonlineer dinamik analiz yapan, tamamen offline çalışan bir masaüstü aracıdır (PySide6 + PyQtGraph, PyInstaller ile `.exe`).

Birincil kullanıcı senaryoları:

1. **Kendi verisini yükle:** CSV / TXT (tek sütun veya seçili kolon) → preprocessing → parametre tahmini (τ, m) → faz uzayı + tüm chaos analizleri.
2. **Kendi ODE sistemini kur:** RK4 ile entegre et → aynı pipeline'a sok.
3. **Kendi map'ini tanımla:** ayrık iterasyon → aynı pipeline.

Hazır 10 sistem (Lorenz, Rössler, Chua, Chen, Duffing, Logistic, Henon, Tent, Sine, Ikeda) **referans / validasyon** içindir; ürünün ana özelliği değildir. Yeni sistem eklemek bu projenin günlük işidir.

### Yasaklar (ROADMAP'ten miras)

- Web UI YOK, sunucu YOK, internet bağımlılığı YOK.
- Parametre tahmini her zaman **veri-tabanlıdır**: τ AMI ile, m FNN ile bulunur. Sabit varsayılan parametreyi UI'a gömme.
- Wolf algoritmasına dokunulurken orijinal MATLAB davranışı (Alan Wolf 1985) referans alınır; sapma yapılacaksa ayrı bir fonksiyon olarak eklenir, mevcut `lyapunov_wolf` değiştirilmez.

---

## 2. Mimarî (4 katman)

```
core/        → veri yapıları + sistem üreticileri + I/O
analysis/    → tüm matematik (lineer + nonlineer)
pipeline/    → bağımlılık çözümlü, önbellekli yürütme motoru
ui/          → PySide6 panelleri + PyQtGraph görselleştirme
```

**Akış kuralı:** ui → pipeline → analysis → core. Üst katman alt katmanı çağırır, ters yön yasak. `analysis/` modülleri `ui/`'yi import etmez; `core/` hiçbir analiz veya UI sembolü tanımaz.

### Kilit veri yapısı: `core/timeseries.TimeSeries`

Tek-boyutlu `np.ndarray` + `dt` + `metadata` + opsiyonel custom time array. Yeni özellik eklerken **bu sınıfı kırmama** zorunlu — UI ve session katmanları bu sözleşmeye dayanır.

### Kilit dosyalar

- `core/timeseries.py` — TimeSeries (dokunma).
- `core/integrators.py` — RK4 + 6 hazır ODE (Lorenz, Rössler, Chua, Chen, Duffing, çift sarkaç). **Yeni ODE buraya eklenir.**
- `core/generators.py` — discrete map'ler ve hazır üreteciler. **Yeni map buraya eklenir.**
- `core/loaders.py` — CSV/TXT yükleyici.
- `core/preprocessing.py` — 12 fonksiyon (normalize, detrend, outlier, smooth, difference, resample, filter, log/boxcox, windowing, denoise).
- `core/session.py` — `.tsa` (pickle) / `.json` session kaydet/yükle.
- `analysis/ami.py`, `analysis/fnn.py` — τ ve m otomatik tahmini.
- `analysis/embedding.py` — zaman gecikmeli gömme.
- `analysis/lyapunov.py` (1124 satır, en kritik dosya) — Wolf, Rosenstein, Kantz, `lyapunov_spectrum`, Theiler window tahmini.
- `analysis/fractal.py` — Grassberger–Procaccia korelasyon boyutu.
- `pipeline/engine.py` — bağımlılık tabanlı önbellekli runner. State değişince cache invalidate edilir.
- `ui/main_window.py`, `ui/panels/*.py` — adım bazlı UI (data load → preprocess → param est → embed → chaos → results).

---

## 3. Planlanan Yeni Özellikler ve Yerleşimleri

Aşağıdaki özellikler aktif yol haritasında. Her biri için **nereye gideceği** ve **dikkat edilecek noktalar** listelendi. Yeni geliştirmelerde bu yerleşim takip edilmeli.

### 3.1 Kullanıcı tanımlı ODE / Map girişi

- **Yer:** Yeni `ui/panels/custom_system_panel.py` + `core/custom_system.py` (henüz yok).
- **Yaklaşım:** Kullanıcı sembolik (string) RHS girer (`dx/dt = sigma*(y-x)` vb.). `sympy` ile parse → callable üret → `integrate_ode` veya iterate ile `TimeSeries` döndür.
- **Güvenlik:** `eval`/`exec` ile rasgele Python çalıştırma YASAK. `sympy.sympify` + sınırlı sembol listesiyle çalış.
- **Persist:** Kullanıcı sistemleri `~/.tsa/custom_systems.json` altında saklanmalı, session'a referans olarak girmeli.
- **Doğrulama:** Yeni sistem `tests/test_validation.py`'a opsiyonel eklenebilir; hazır 10 sisteme dokunma.

### 3.2 Poincaré Kesitleri

- **Yer:** `analysis/poincare.py` (yeni). UI: `ui/panels/poincare_panel.py` veya mevcut `chaos_analysis_panel`'a sekme olarak.
- **API taslağı:**
  ```python
  poincare_section(trajectory: np.ndarray, plane: dict, direction: int = 1) -> np.ndarray
  ```
  `plane` örn. `{"axis": 2, "value": 0.0}` (z=0 düzlemi) veya genel hiperdüzlem `{"normal": [...], "offset": ...}`. `direction` (+1 / -1 / 0) yönlü kesişim filtresi.
- **Implementasyon notu:** Lineer interpolasyon ile kesişim noktası tam yakalanmalı (sadece sign-change indeksi yetmez).
- **Görselleştirme:** PyQtGraph `ScatterPlotItem`. 3D ODE sistemleri için doğal; 1D zaman serileri gömme uzayında çalışır.
- **Bağımlılık:** Çok değişkenli ODE çıktısı gerek. Şu an `integrate_ode` yalnızca **ilk değişkeni** TimeSeries olarak döndürüyor (`integrators.py:51`). Poincaré için **tam state vektörü** lazım — `integrate_ode_full(...) -> np.ndarray (n_steps, dim)` ek bir API eklenmeli, mevcut fonksiyon kırılmamalı.

### 3.3 Fraktal Boyutlar (genişletme)

Mevcut: yalnızca **korelasyon boyutu** (Grassberger–Procaccia, `analysis/fractal.py`).

Eklenecekler — **aynı modül** içinde, aynı stilde fonksiyonlar:

- `box_counting_dimension(embedded, eps_range)` — log–log slope.
- `information_dimension(embedded, eps_range)` — D₁, Shannon-tabanlı.
- `generalized_dimension(embedded, q_values, eps_range)` — Dq spektrumu (multifractal).
- `higuchi_fractal_dimension(data, kmax)` — direkt zaman serisi üzerinde, gömme gerekmez.

**Performans kuralı:** `pdist` veya `cKDTree` kullan; saf Python iç içe döngü kabul edilmiyor. `max_points` ile alt-örnekleme paterni `correlation_sum`'daki gibi korunmalı.

**Test:** Henon ve Lorenz için literatür değerleri bilinen fraktal boyutlar (Henon ≈ 1.26, Lorenz ≈ 2.06) — `tests/test_validation.py`'a paralel bir bölüm eklenebilir.

### 3.4 Bifurcation Haritaları

- **Yer:** `analysis/bifurcation.py` (yeni). UI: `ui/panels/bifurcation_panel.py`.
- **API taslağı:**
  ```python
  bifurcation_diagram(
      system_factory: Callable[[float], Callable],   # parametre → RHS / map
      param_range: tuple[float, float, int],
      n_transient: int,
      n_record: int,
      observable: str | Callable = "x",              # hangi değişken / Poincaré sample
  ) -> tuple[np.ndarray, np.ndarray]                  # (param_values, points)
  ```
- **Veri büyüklüğü:** 1000 parametre × 500 örnek = 500k nokta. UI'da `pyqtgraph.ScatterPlotItem(useOpenGL=True)` veya `IsocurveItem` density tabanlı render.
- **ODE için:** Poincaré kesiti üzerinden örnekleme (sürekli sistemde "bifurcation" Poincaré dönüş haritasından gelir). 3.2 hazır olmadan ODE bifurcation tamamlanmamalı.
- **Map için:** Doğrudan iterate, transient at, kalan örnekleri biriktir (`generators.py`'deki `iterate_logistic` benzeri pattern).
- **Performans:** `numba` veya `numpy` vectorization. `multiprocessing` opsiyonel ama PyInstaller paketlemesinde sorun çıkartabilir, önce ölç.

### 3.5 Full Lyapunov Spektrumu

`analysis/lyapunov.py` zaten `lyapunov_spectrum` exportu yapıyor — **mevcut implementasyonu önce oku**, sıfırdan yazma. Beklenen:

- **Benettin / Shimada–Nagashima** Gram–Schmidt yöntemi: ODE + variational equations'i birlikte entegre et, periyodik QR ortonormalize et, log-rate'leri biriktir.
- **Variational equation:** Jacobian gerekir. Kullanıcı tanımlı sistemler için sembolik Jacobian (`sympy.diff`) veya `scipy.optimize.approx_fprime` ile sayısal türev.
- **Çıktı:** `np.ndarray` shape `(d,)`, sıralı (büyükten küçüğe). Tutarlılık testi: Σλᵢ ≈ trace(⟨J⟩) (sürekli sistemde divergence ortalaması).
- **Kaplan–Yorke boyutu:** Spektrumdan türetilir, fractal modülünden değil burada üretilmeli (`kaplan_yorke_dimension(spectrum)`).
- **Validasyon:** Lorenz için (≈ 0.906, 0, −14.572). Toleranslar `test_validation.py` patterniyle.

---

## 4. Komutlar

```bash
# Bağımlılıklar
pip install -r requirements.txt

# Uygulamayı çalıştır
python main.py

# Bilimsel doğrulama (10 sistem × 3 algoritma, ~43 sn)
python tests/test_validation.py

# Wolf MATLAB uyumluluk
python tests/test_wolf_matlab_match.py

# Preprocessing & UI testleri
python tests/test_preprocessing_workflow.py

# .exe build
pyinstaller main.py --noconsole --onefile --name TSAnalyzer
```

`pytest` kurulu (.pytest_cache/ var) ama testler düz `if __name__ == "__main__"` ile de çalışıyor — yeni test eklerken **her iki şekilde** çalışacak biçimde yaz.

---

## 5. Kod Stili ve Kuralları

- **Numpy-vector first.** Saf Python döngüsü ancak başka çare yoksa. KD-Tree (`scipy.spatial.cKDTree`) ve `pdist` standart.
- **Type hint zorunlu** public fonksiyonlarda. Docstring NumPy-style (mevcut dosyalardaki örüntü).
- **Türkçe yorum kabul** ama API isimleri (fonksiyon, parametre) İngilizce.
- **Yan etki yasağı:** `analysis/*` fonksiyonları girdiyi mutate etmez, dosya/IO yapmaz, plot çizmez. Yalnızca hesap döner.
- **Print yok:** Debug için `logging` modülü kullan, console kirletme. Son commit'lerde tüm `print` debug temizlendi (`f6bea8a`), bunu geri getirme.
- **UI–logic ayrımı:** Yeni analiz fonksiyonu eklerken önce `analysis/` veya `core/` altında testlenebilir, headless çalışan API yaz; sonra UI bağla.

---

## 6. Test Stratejisi

İki farklı test türü var, **karıştırma**:

1. `test_validation.py` → **bilimsel doğruluk** (literatür LE değeriyle karşılaştırma, veri-tabanlı parametre). Yeni algoritma eklersen buraya yeni sistemli vaka ekle, mevcut vakaları **bozma**.
2. `test_wolf_matlab_match.py` → **implementasyon doğruluğu** (Wolf MATLAB sabit parametreleriyle karşılaştırma). Wolf'a dokunursan bu test geçmeli (%4'ten kötüye gitme).

Yeni özellik eklerken mantıklı olan tarafa test ekle:

- Yeni algoritma (örn. box-counting) → `test_validation.py`'a literatür referanslı vaka.
- Yeni MATLAB/literatür replikasyonu → ayrı `test_*_match.py`.
- Yeni UI / preprocessing → `test_preprocessing_workflow.py`.

---

## 7. Bilinen Riskler / Tuzaklar

- **`integrate_ode` sadece ilk değişkeni döndürür** (`integrators.py:51`). 3D faz uzayı, Poincaré, full spectrum için bu yetersiz — `integrate_ode_full` ekle, mevcut imzayı bozma.
- **Pipeline cache invalidation**: `engine.set_state` ile state değişirse bağımlı node cache'leri otomatik silinir (`engine.py:38`). Yeni node eklerken `dependencies` listesini doğru kur, yoksa stale sonuç verir.
- **PyQtGraph thread-safety:** Plot çağrıları main thread'de. Uzun analizler `QThread`'de çalıştırılmalı, sonuç slot ile UI'a iletilmeli (mevcut panellerde örnek var).
- **PyInstaller paketleme:** Hidden import'lar eksik kalabiliyor (özellikle `scipy.spatial`). `--collect-submodules scipy` denenmeli.
- **Duffing %47.9 hata** (validasyonda). Forced osilatörlerde transient + dt seçimi hassas. Yeni forced sistem eklerken `transient` parametresini uzun tut, `dt` küçült.
- **Discrete map'lerde Wolf overestimate, Rosenstein underestimate**. Karşılaştırmalı sunmak gerekebilir, sessizce birini seçme.
- **`__pycache__` ve `test_table.py` repo'da** — yeni dosya eklerken `.gitignore`'u kontrol et.
- **PyQtGraph sağ-tık menüsü Türkçeleştirme YAPILMADI / kaldırıldı.** Önceki denemeler (`ui/pyqtgraph_tr.py` + QTranslator + ExportDialog monkey-patch) ciddi görünürlük hatalarına yol açtı (Export..., Plot Options öğeleri siyah/görünmez oluyordu) ve tüm kod kaldırıldı. Sıfırdan yapılacak. Temel zorluk: `addParentContextMenus` ile ViewBoxMenu'ya sonradan eklenen QAction'lar farklı parent'lara (GraphicsScene, PlotItem) sahip olduğundan MainWindow stylesheet'ini miras almıyor ve Windows dark mode aktifken invisible oluyor. Doğru çözüm: ViewBoxMenu'ya `setStyleSheet()` + QTranslator kombinasyonu, ama dikkatli test edilmeli. `vb.menu = None` YAPMA — PyQtGraph'ta `getMenu()` sadece `return self.menu` yapar, lazy creation yoktur; None atanırsa sağ tık tamamen çalışmaz.

---

## 8. Yeni Özellik Eklerken Mini-Akış

1. Önce ilgili `analysis/*.py` dosyasına saf-fonksiyon API ekle (numpy in, numpy out).
2. `tests/`'e literatür referanslı küçük bir test ekle, yeşil olduğunu gör.
3. `pipeline/engine`'e Node olarak kaydet (gerekiyorsa), bağımlılıkları belirt.
4. `ui/panels/*` altında ya mevcut panele sekme ekle ya da yeni panel oluştur, `panels/__init__.py`'ye export et.
5. `core/session.py` içinde state alanı varsa serialize/deserialize'a ekle.
6. README.md ve gerekirse ROADMAP.md güncelle.
   - **README.md her zaman İngilizce yazılır.**
   - README.md her güncellendiğinde `README(tr).md` de aynı anda güncellenir; içerik birebir aynı olmalı, yalnızca dil Türkçe olur.
   - İki dosya hiçbir zaman birbirinden farklı içerikte bırakılmaz.
7. Commit mesajı kısa İngilizce, son commit stiline uy: `Add Poincaré section module`, `Fix bifurcation diagram saturation`.

---

## 9. Hızlı Referans

| İhtiyaç | Modül |
|--------|-------|
| Kendi CSV/TXT'sini yüklemek | `core.loaders.load_csv`, `load_txt` |
| Kendi ODE'sini entegre etmek | `core.integrators.integrate_ode` (+ özel RHS) |
| Kendi map'ini iterate etmek | `core/generators.py` patterni |
| τ tahmini | `analysis.ami.compute_ami` + `find_first_minimum` |
| m tahmini | `analysis.fnn.compute_fnn` + `find_embedding_dimension` |
| Gömme | `analysis.embedding.embed_timeseries` |
| LE (sürekli) | `analysis.lyapunov.lyapunov_rosenstein` |
| LE (genel / referans) | `analysis.lyapunov.lyapunov_wolf` |
| Spektrum (planlı) | `analysis.lyapunov.lyapunov_spectrum` |
| Korelasyon boyutu | `analysis.fractal.correlation_dimension` |
| Session save/load | `core.session.AnalysisSession` |
| Pipeline | `pipeline.engine.PipelineEngine` |

---

Kısaca: **yeni iş, doğru katmana, headless API olarak, testle birlikte.** Wolf'u, TimeSeries'i ve `integrate_ode`'un mevcut imzasını kırma; üzerine ekle.
