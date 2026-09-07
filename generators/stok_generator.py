"""Stok/ürün fake veri üretici.

Şablon kolon sırası (Stoklar sayfası):
Stok Adı *, Birim Kodu *, Birim Adı, Fiyat *, Satıcı Kodu, Alıcı Kodu,
Üretici Kodu, Aktif *, GTİP Kodu, Marka, Model, Açıklama, Not,
Teslimat Kodu, Sevkiyat Kodu, KDV Oranı *
"""

from __future__ import annotations

import random
import string

from faker import Faker

from .common import make_faker
from .template_reader import StokLists

GRUPLAR = [
    "Çelik", "Alüminyum", "Plastik", "Ahşap", "Cam", "Bakır",
    "Galvaniz", "Krom", "Kompozit", "Pirinç", "Endüstriyel", "Sanayi Tipi",
]
URUNLER = [
    "Vida", "Cıvata", "Somun", "Pul", "Kablo", "Motor", "Pompa", "Rulman",
    "Conta", "Filtre", "Valf", "Boru", "Dirsek", "Flanş", "Klemens",
    "Sigorta", "Röle", "Sensör", "Lamba", "Panel", "Kilit", "Menteşe",
    "Profil", "Sac", "Kutu", "Yağ", "Boya", "Kayış", "Zincir", "Redüktör",
]
MARKALAR = [
    "Bosch", "Siemens", "ABB", "Schneider", "Eaton", "Legrand", "Viko",
    "Makel", "Kale", "Fırat", "Pimaş", "Philips", "Osram", "Vestel",
    "Arçelik", "Beko", "Baymak", "E.C.A.", "Demirdöküm", "Pilsa",
]
MODELLER = ["Pro", "Plus", "Max", "Mini", "Eco", "Ultra", "Endüstriyel", "HD", "XL"]


def _stok_adi(rng: random.Random) -> str:
    spec = rng.choice(
        [
            f"M{rng.randint(4, 24)}x{rng.randint(10, 120)}",
            f"Ø{rng.randint(10, 200)}",
            f'{rng.choice(["1/2", "3/4", "1", "2"])}"',
            f"{rng.randint(100, 5000)}W",
            f"{rng.randint(12, 400)}V",
            f"IP{rng.choice(['44', '55', '65', '67'])}",
            f"{rng.randint(1, 500)} kg",
            f"{rng.randint(10, 1000)} lt",
        ]
    )
    return f"{rng.choice(GRUPLAR)} {rng.choice(URUNLER)} {spec}"


def _model(rng: random.Random) -> str:
    harf = "".join(rng.choices(string.ascii_uppercase, k=2))
    ek = f" {rng.choice(MODELLER)}" if rng.random() < 0.4 else ""
    return f"{harf}-{rng.randint(100, 9999)}{ek}"


def _gtip(rng: random.Random) -> str:
    return f"{rng.randint(1000, 9999)}.{rng.randint(10, 99)}.{rng.randint(0, 99):02d}.{rng.randint(0, 99):02d}"


def _birim_sec(rng: random.Random, lists: StokLists) -> tuple[str, str]:
    """Ağırlıklı birim kodu + karşılığındaki birim adı."""
    if not lists.birim_kodlari:
        return "C62", "ADET"
    agirlikli = ["C62", "KGM", "LTR", "MTR", "PK"]
    adaylar = [k for k in agirlikli if k in lists.birim_kodlari]
    if rng.random() < 0.8 and adaylar:
        kod = rng.choices(adaylar, weights=[40, 15, 10, 10, 5][: len(adaylar)])[0]
    else:
        kod = rng.choice(lists.birim_kodlari)
    return kod, lists.birim_adlari.get(kod, "")


def stok_satir(fake: Faker, rng: random.Random, lists: StokLists) -> list:
    birim_kodu, birim_adi = _birim_sec(rng, lists)
    kdvlar = lists.kdv_oranlari or [0, 1, 8, 10, 18, 20]
    kdv_agirlik = {0: 5, 1: 5, 8: 20, 10: 15, 18: 15, 20: 40}
    kdv = rng.choices(kdvlar, weights=[kdv_agirlik.get(k, 10) for k in kdvlar])[0]

    return [
        _stok_adi(rng),  # Stok Adı *
        birim_kodu,  # Birim Kodu *
        birim_adi,  # Birim Adı
        round(rng.uniform(10, 150_000), 2),  # Fiyat *
        f"STC-{rng.randint(100000, 999999)}" if rng.random() < 0.7 else "",  # Satıcı Kodu
        f"ALC-{rng.randint(100000, 999999)}" if rng.random() < 0.6 else "",  # Alıcı Kodu
        f"URT-{rng.randint(100000, 999999)}" if rng.random() < 0.5 else "",  # Üretici Kodu
        rng.choices(["Aktif", "Pasif"], weights=[85, 15])[0],  # Aktif *
        _gtip(rng) if rng.random() < 0.7 else "",  # GTİP Kodu
        rng.choice(MARKALAR) if rng.random() < 0.85 else "",  # Marka
        _model(rng),  # Model
        fake.sentence(nb_words=6),  # Açıklama
        fake.sentence(nb_words=8) if rng.random() < 0.5 else "",  # Not
        rng.choice(lists.teslimat_kodlari) if lists.teslimat_kodlari and rng.random() < 0.7 else "",  # Teslimat Kodu
        rng.choice(lists.sevkiyat_kodlari) if lists.sevkiyat_kodlari and rng.random() < 0.7 else "",  # Sevkiyat Kodu
        kdv,  # KDV Oranı *
    ]


def uret_stoklar(n: int, lists: StokLists, seed: int | None = None) -> list[list]:
    """n satır stok verisi üretir (en fazla 2000 - şablon limiti)."""
    if not 1 <= n <= 2000:
        raise ValueError("Stok satır sayısı 1-2000 arasında olmalı (şablon limiti).")
    fake = make_faker(seed)
    rng = random.Random(seed)
    return [stok_satir(fake, rng, lists) for _ in range(n)]
