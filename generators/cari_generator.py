"""Cari (müşteri/tedarikçi) fake veri üretici.

Şablon kolon sırası (Cariler sayfası):
Vergi No *, Unvan, Ad, Soyad, Vergi Dairesi, Adres, İlçe, Şehir,
Ülke, Ülke Kodu, Posta Kodu, Telefon, Faks, E-posta, Web Sitesi, Tip
"""

from __future__ import annotations

import random
import re

from faker import Faker

from .common import make_faker
from .template_reader import CariLists

UNVAN_EKLERI = ["A.Ş.", "Ltd. Şti.", "Tic. Ltd. Şti.", "San. ve Tic. A.Ş.", "Grup A.Ş.", "Ticaret A.Ş."]
VERGI_DAIRESI_SEMTLERI = ["Merkez", "Çankaya", "Kadıköy", "Beşiktaş", "Konak", "Osmangazi", "Seyhan", "Muratpaşa"]
ILCELER = [
    "Merkez", "Çankaya", "Kadıköy", "Beşiktaş", "Üsküdar", "Konak", "Karşıyaka",
    "Osmangazi", "Nilüfer", "Seyhan", "Çukurova", "Muratpaşa", "Kepez",
    "Tepebaşı", "Odunpazarı", "İzmit", "Gebze", "Tarsus", "Alanya", "Ürgüp",
]
ALAN_KODLARI = ["212", "216", "312", "232", "222", "322", "332", "352", "532", "533", "542", "505", "506"]


def uret_tckn(rng: random.Random) -> str:
    """Geçerli checksum'lu 11 haneli TCKN üretir."""
    d = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(8)]
    d10 = (sum(d[0::2]) * 7 - sum(d[1::2])) % 10
    d.append(d10)
    d.append(sum(d[:10]) % 10)
    return "".join(map(str, d))


def uret_vkn(rng: random.Random) -> str:
    """GİB algoritmasına uygun 10 haneli VKN üretir."""
    ilk9 = [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(8)]
    toplam = 0
    for i, rakam in enumerate(ilk9, start=1):
        tmp = (rakam + 10 - i) % 10
        carpan = pow(2, 10 - i, 9)
        b = (tmp * carpan) % 9
        if tmp != 0 and b == 0:
            b = 9
        toplam += b
    kontrol = (10 - toplam % 10) % 10
    return "".join(map(str, ilk9 + [kontrol]))


def _slug(text: str) -> str:
    tr = str.maketrans("çÇğĞıİöÖşŞüÜ", "ccggii oossuu".replace(" ", ""))
    text = text.translate(tr)
    text = re.sub(r"[^a-zA-Z0-9]+", "", text)
    return text.lower() or "firma"


def _telefon(rng: random.Random) -> str:
    return f"0{rng.choice(ALAN_KODLARI)} {rng.randint(100, 999)} {rng.randint(10, 99)} {rng.randint(10, 99)}"


def cari_satir(fake: Faker, rng: random.Random, lists: CariLists) -> list:
    # Tip dağılımı: %45 Tüzel, %45 Gerçek, %10 boş (şablon buna izin veriyor)
    tip = rng.choices(["Tüzel", "Gerçek", ""], weights=[45, 45, 10])[0]
    tuzel = tip != "Gerçek"  # boş tipte tüzel gibi davran (Unvan zorunlu mantığı)

    vergi_no = uret_vkn(rng) if rng.random() < 0.7 else uret_tckn(rng)

    if tuzel:
        unvan = f"{fake.company()} {rng.choice(UNVAN_EKLERI)}"
        ad, soyad = "", ""
    else:
        unvan = ""
        ad, soyad = fake.first_name(), fake.last_name()

    sehir = rng.choice(lists.iller) if lists.iller else fake.city()
    if rng.random() < 0.9 or not lists.ulkeler:
        ulke = next((u for u in lists.ulkeler if u.lower() == "türkiye"), "Türkiye")
        ulke_kodu = "TR"
    else:
        ulke = rng.choice(lists.ulkeler)
        ulke_kodu = "TR" if ulke.lower() == "türkiye" else fake.country_code()

    # Domain'i unvan/ad-soyad'dan türet ki e-posta ile tutarlı olsun
    kaynak = unvan if tuzel else f"{ad} {soyad}"
    domain = f"{_slug(kaynak)[:20] or 'firma'}{rng.choice(['.com', '.com.tr', '.net', '.net.tr'])}"
    eposta = f"info@{domain}" if tuzel else f"{_slug(ad)}.{_slug(soyad)}@{domain}"

    return [
        vergi_no,  # Vergi No *
        unvan,  # Unvan
        ad,  # Ad
        soyad,  # Soyad
        f"{sehir} {rng.choice(VERGI_DAIRESI_SEMTLERI)} Vergi Dairesi",  # Vergi Dairesi
        f"{fake.street_name()} Mah. {fake.street_name()} Cad. No:{rng.randint(1, 150)} D:{rng.randint(1, 40)}",  # Adres
        rng.choice(ILCELER),  # İlçe
        sehir,  # Şehir
        ulke,  # Ülke
        ulke_kodu,  # Ülke Kodu
        f"{rng.randint(10000, 81999):05d}",  # Posta Kodu
        _telefon(rng),  # Telefon
        _telefon(rng) if rng.random() < 0.5 else "",  # Faks
        eposta.lower(),  # E-posta
        f"www.{domain.lower()}" if (tuzel and rng.random() < 0.7) or rng.random() < 0.3 else "",  # Web Sitesi
        tip,  # Tip
    ]


def uret_cariler(n: int, lists: CariLists, seed: int | None = None) -> list[list]:
    """n satır cari verisi üretir (en fazla 2000 - şablon limiti)."""
    if not 1 <= n <= 2000:
        raise ValueError("Cari satır sayısı 1-2000 arasında olmalı (şablon limiti).")
    fake = make_faker(seed)
    rng = random.Random(seed)
    return [cari_satir(fake, rng, lists) for _ in range(n)]
