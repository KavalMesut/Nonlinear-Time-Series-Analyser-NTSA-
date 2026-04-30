"""
Poincaré section computation.

Referans: Takens (1981), Eckmann & Ruelle (1985).

Desteklenen kesit tanimlari:
  - Eksen-hizali duzlem  : {"axis": int, "value": float}
  - Genel hiperduzlem    : {"normal": array-like, "offset": float}

Kesisim noktasi lineer interpolasyon ile yakalanir; sadece isaretli gecis
indeksi kullanmak hatali sonuclar uretebilir (kaybedilen veya fazladan
nokta) — bu implementasyonda gercek kesisim koordinati hesaplanir.
"""
import numpy as np
from typing import Union


def poincare_section(
    trajectory: np.ndarray,
    plane: dict,
    direction: int = 1,
) -> np.ndarray:
    """
    Bir yörüngenin verilen duzlemle kesisim noktalarini hesapla.

    Args:
        trajectory: shape (n_steps, dim) — tam durum vektoru yörüngesi.
                    Zaman-gecikmeli gomme ciktisi da kullanilabilir (dim = m).
        plane: Kesit duzlem tanimi.
               Eksen-hizali: {"axis": int, "value": float}
               Genel hiperduzlem: {"normal": array-like, "offset": float}
               "offset" yoksa 0 kabul edilir.
        direction: +1  = yalnizca yukari gecisler (dist artiyor)
                   -1  = yalnizca asagi gecisler (dist azaliyor)
                    0  = her iki yon

    Returns:
        crossings: shape (n_crossings, dim) — interpolasyonlu kesisim noktalari.
                   Kesisim bulunamazsa shape (0, dim) bos dizi doner.

    Raises:
        ValueError: Trajectory 1D ise ya da plane anahtarlari eksikse.

    Notes:
        Kesisim noktasi ``p(t*) = p(i) + alpha*(p(i+1) - p(i))`` ile
        yakalanir, burada ``alpha = -d(i) / (d(i+1) - d(i))`` ve d(i)
        noktanin duzleme imzali mesafesidir.
    """
    trajectory = np.asarray(trajectory, dtype=float)
    if trajectory.ndim != 2:
        raise ValueError(
            f"trajectory 2D olmali (n_steps, dim), alindi: {trajectory.shape}"
        )
    n_steps, dim = trajectory.shape

    # --- imzali mesafe dizisini olustur ---
    if "axis" in plane:
        axis = int(plane["axis"])
        value = float(plane["value"])
        if axis < 0 or axis >= dim:
            raise ValueError(
                f"plane['axis']={axis} boyut disinda (dim={dim})"
            )
        dist = trajectory[:, axis] - value
    elif "normal" in plane:
        normal = np.asarray(plane["normal"], dtype=float)
        if normal.shape != (dim,):
            raise ValueError(
                f"plane['normal'] boyutu ({normal.shape}) trajectory dim ({dim}) ile uyusmuyor"
            )
        norm = np.linalg.norm(normal)
        if norm < 1e-15:
            raise ValueError("plane['normal'] sifir vektor olamaz")
        normal = normal / norm
        offset = float(plane.get("offset", 0.0))
        dist = trajectory @ normal - offset
    else:
        raise ValueError(
            "plane sozlugu 'axis' ya da 'normal' anahtari icermeli"
        )

    # --- isaretli gecisleri bul ve interpolasyon uygula ---
    crossings = []
    for i in range(n_steps - 1):
        d0, d1 = dist[i], dist[i + 1]

        # Yalnizca isaretli gecis: d0 ve d1 farkli isaretli olmali
        if d0 * d1 >= 0.0:
            continue

        # Gecis yonu filtresi
        cross_dir = 1 if d1 > d0 else -1
        if direction != 0 and cross_dir != direction:
            continue

        # Lineer interpolasyon: alpha in (0, 1)
        denom = d1 - d0
        alpha = -d0 / denom          # tam kesisim parametresi
        point = trajectory[i] + alpha * (trajectory[i + 1] - trajectory[i])
        crossings.append(point)

    if not crossings:
        return np.empty((0, dim))
    return np.array(crossings)


def poincare_from_timeseries(
    data: np.ndarray,
    m: int,
    tau: int,
    plane: dict,
    direction: int = 1,
) -> np.ndarray:
    """
    Zaman serisini gomme uzayina tasiyip Poincaré kesiti hesapla.

    Kolaylik fonksiyonu — embed_timeseries + poincare_section zincirini
    tek satirda cagirmak icin.

    Args:
        data: 1D zaman serisi
        m: gomme boyutu
        tau: zaman gecikmesi
        plane: poincare_section ile ayni format
        direction: poincare_section ile ayni anlam

    Returns:
        crossings: shape (n_crossings, m)
    """
    from .embedding import embed_timeseries
    embedded = embed_timeseries(data, m, tau)
    return poincare_section(embedded, plane, direction)
