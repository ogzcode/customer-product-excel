"""Fatura fake veri üretici.

Şablon kolon sırası (Fatura Bilgileri sayfası, 52 kolon):
Müşteri Bilgileri (0-11): Ünvan, Vkn-Tckn, Vergi Dairesi, Adres, İlçe,
    Şehir, Ülke, Posta Kodu, Telefon, Faks, Web Site, E-Posta
Genel Bilgiler (12-35): Fatura Seri, Fatura Şablonu UUID, Para Birimi,
    Döviz Kuru, Fatura Senaryosu, Fatura Tipi, Fatura Tarihi,
    KDV İstisna Sebebi, Kamu Harcama Birimi, İnternet Satış Vkn-Tckn,
    İnternet Satış Ünvan, Fatura Notu, Etiketler, Özel Kod,
    Gönderim Tipi, Satış Kanalı, Web Sitesi, Ödeme Yöntemi,
    Ödeme Yöntemi Açıklaması, Ödeme Aracısı, Ödeme Tarihi,
    Taşıyıcı Ünvan, Taşıyıcı Vkn-Tckn, Taşıma Tarihi
Mal/Hizmet Bilgileri (36-51): Mal/Hizmet Adı, Miktar, Birim,
    Birim Fiyat, KDV (%), KDV Tevkifat Kodu, İskonto Oranı (%),
    İskonto Tutarı, Toplam Tutar, Satıcı Kodu, Alıcı Kodu,
    Üretici Kodu, Marka, Model, Açıklama, Not
"""

from __future__ import annotations

import random
import re
import string
from datetime import date, timedelta

from faker import Faker

from .cari_generator import ILCELER, UNVAN_EKLERI, VERGI_DAIRESI_SEMTLERI, uret_tckn, uret_vkn
from .common import make_faker
from .template_reader import FaturaLists

FATURA_SENARYOLARI = ["TICARIFATURA", "TEMELFATURA", "EARSIVFATURA"]
PARA_BIRIMLERI = ["TRY", "USD", "EUR", "GBP"]
GONDERIM_TIPLERI = ["ELEKTRONIK", "KAGIT"]
SATIS_KANALLARI = ["INTERNET", "MAGAZA", "SAHA"]
ODEME_YONTEMLERI = ["KREDIKARTI/BANKAKARTI", "HAVALE/EFT", "KAPIDAODEME", "CEK"]

URUN_ADLARI = [
    "Endüstriyel Vida", "Paslanmaz Cıvata", "Çelik Somun", "Bakır Pul",
    "Kablo Kanalı", "Elektrik Motoru", "Su Pompası", "Rulman Seti",
    "Silikon Conta", "Hava Filtresi", "Pirinç Valf", "Çelik Boru",
    "PVC Dirsek", "Flanş Seti", "Klemens Bloğu", "Otomatik Sigorta",
    "Röle Kartı", "Endüstriyel Sensör", "LED Panel", "Jeneratör",
    "Hizmet - Montaj", "Hizmet - Bakım", "Hizmet - Danışmanlık",
    "Hizmet - Taşıma", "Hizmet - Temizlik",
]
MARKALAR = [
    "Bosch", "Siemens", "ABB", "Schneider", "Eaton", "Legrand", "Viko",
    "Makel", "Kale", "Fırat", "Pimaş", "Philips", "Osram", "Vestel",
    "Arçelik", "Beko", "Baymak", "E.C.A.", "Demirdöküm", "Pilsa",
]
MODELLER = ["Pro", "Plus", "Max", "Mini", "Eco", "Ultra", "Endüstriyel", "HD", "XL"]

KDV_ORANLARI = [0, 1, 8, 10, 18, 20]
KDV_AGIRLIK = {0: 5, 1: 5, 8: 20, 10: 15, 18: 15, 20: 40}


def _slug(text: str) -> str:
    tr = str.maketrans("çÇğĞıİöÖşŞüÜ", "ccggii oossuu".replace(" ", ""))
    text = text.translate(tr)
    text = re.sub(r"[^a-zA-Z0-9]+", "", text)
    return text.lower() or "firma"


def _model(rng: random.Random) -> str:
    harf = "".join(rng.choices(string.ascii_uppercase, k=2))
    ek = f" {rng.choice(MODELLER)}" if rng.random() < 0.4 else ""
    return f"{harf}-{rng.randint(100, 9999)}{ek}"


def _birim_sec(rng: random.Random, lists: FaturaLists) -> str:
    if not lists.birim_kodlari:
        return "C62"
    agirlikli = ["C62", "KGM", "LTR", "MTR", "PK"]
    adaylar = [k for k in agirlikli if k in lists.birim_kodlari]
    if rng.random() < 0.8 and adaylar:
        return rng.choices(adaylar, weights=[40, 15, 10, 10, 5][: len(adaylar)])[0]
    return rng.choice(lists.birim_kodlari)


def _kdv_orani(rng: random.Random) -> int:
    return rng.choices(KDV_ORANLARI, weights=[KDV_AGIRLIK.get(k, 10) for k in KDV_ORANLARI])[0]


def _tarih(rng: random.Random) -> str:
    bugun = date.today()
    baslangic = bugun - timedelta(days=730)
    gun = rng.randint(0, 730)
    tarih = baslangic + timedelta(days=gun)
    return f"{tarih.day:02d}/{tarih.month:02d}/{tarih.year}"


def _musteri_blok(fake: Faker, rng: random.Random, lists: FaturaLists) -> list:
    tip = rng.choices(["Tüzel", "Gerçek"], weights=[70, 30])[0]
    tuzel = tip == "Tüzel"

    vergi_no = uret_vkn(rng) if rng.random() < 0.7 else uret_tckn(rng)

    if tuzel:
        unvan = f"{fake.company()} {rng.choice(UNVAN_EKLERI)}"
        ad, soyad = "", ""
    else:
        unvan = ""
        ad, soyad = fake.first_name(), fake.last_name()

    sehir = fake.city()
    ilce = rng.choice(ILCELER)
    ulke = next((u for u in lists.ulkeler if "türkiye" in u.lower()), "Türkiye")
    if not ulke and lists.ulkeler:
        ulke = lists.ulkeler[0]

    kaynak = unvan if tuzel else f"{ad} {soyad}"
    domain = f"{_slug(kaynak)[:20] or 'firma'}{rng.choice(['.com', '.com.tr', '.net'])}"
    eposta = f"info@{domain}" if tuzel else f"{_slug(ad)}.{_slug(soyad)}@{domain}"

    blok = [None] * 52
    blok[0] = unvan
    blok[1] = vergi_no
    blok[2] = f"{sehir} {rng.choice(VERGI_DAIRESI_SEMTLERI)} Vergi Dairesi"
    blok[3] = f"{fake.street_name()} Mah. {fake.street_name()} Cad. No:{rng.randint(1, 150)}"
    blok[4] = ilce
    blok[5] = sehir
    blok[6] = ulke
    blok[7] = f"{rng.randint(10000, 81999):05d}" if rng.random() < 0.6 else None
    blok[8] = f"0{rng.randint(212, 505)} {rng.randint(100, 999)} {rng.randint(10, 99)} {rng.randint(10, 99)}" if rng.random() < 0.7 else None
    blok[11] = eposta.lower()
    return blok


def _genel_blok(fake: Faker, rng: random.Random, lists: FaturaLists, senaryo: str, fatura_tipi: str) -> list:
    blok = [None] * 52

    para = rng.choice(PARA_BIRIMLERI)
    blok[14] = para if para != "TRY" else None
    if para != "TRY" and rng.random() < 0.5:
        blok[15] = round(rng.uniform(1.0, 50.0), 4)

    blok[16] = senaryo
    blok[17] = fatura_tipi
    blok[18] = _tarih(rng)

    if rng.random() < 0.5:
        blok[22] = fake.sentence(nb_words=8)

    if rng.random() < 0.4:
        etiketler = [fake.word() for _ in range(rng.randint(1, 3))]
        blok[23] = ";".join(etiketler)

    if senaryo == "EARSIVFATURA":
        blok[25] = rng.choice(GONDERIM_TIPLERI)
        if rng.random() < 0.5:
            blok[26] = rng.choice(SATIS_KANALLARI)
        if rng.random() < 0.4:
            blok[27] = f"www.{_slug(fake.company())}.com"
        if rng.random() < 0.6:
            blok[28] = rng.choice(ODEME_YONTEMLERI)
        if rng.random() < 0.3:
            blok[30] = _tarih(rng)

    return blok


def _mal_hizmet_blok(fake: Faker, rng: random.Random, lists: FaturaLists) -> tuple[list, float, float, float]:
    blok = [None] * 52

    blok[35] = rng.choice(URUN_ADLARI)
    miktar = rng.randint(1, 100)
    blok[36] = miktar
    blok[37] = _birim_sec(rng, lists)
    birim_fiyat = round(rng.uniform(10, 50_000), 2)
    blok[38] = birim_fiyat

    kdv = _kdv_orani(rng)
    blok[39] = kdv

    ana_tutar = miktar * birim_fiyat
    iskonto_tutar = 0.0

    if rng.random() < 0.3:
        iskonto_orani = rng.randint(1, 100)
        blok[41] = iskonto_orani
        iskonto_tutar = round(ana_tutar * iskonto_orani / 100, 2)
        blok[42] = iskonto_tutar
    elif rng.random() < 0.2:
        iskonto_tutar = round(rng.uniform(10, ana_tutar * 0.1), 2) if ana_tutar > 100 else 0
        blok[42] = iskonto_tutar if iskonto_tutar > 0 else None

    kdv_matrah = ana_tutar - iskonto_tutar
    kdv_tutar = kdv_matrah * kdv / 100
    toplam = round(kdv_matrah + kdv_tutar, 3)
    blok[43] = toplam

    if rng.random() < 0.5:
        blok[44] = f"STC-{rng.randint(100000, 999999)}"
    if rng.random() < 0.4:
        blok[45] = f"ALC-{rng.randint(100000, 999999)}"
    if rng.random() < 0.3:
        blok[46] = f"URT-{rng.randint(100000, 999999)}"
    if rng.random() < 0.7:
        blok[47] = rng.choice(MARKALAR)
    blok[48] = _model(rng)
    if rng.random() < 0.5:
        blok[49] = fake.sentence(nb_words=5)
    if rng.random() < 0.3:
        blok[50] = fake.sentence(nb_words=6)

    return blok, ana_tutar, iskonto_tutar, toplam


def _fatura_olustur(
    fake: Faker, rng: random.Random, lists: FaturaLists, kalem_sayisi: int
) -> list[list]:
    senaryo = rng.choice(FATURA_SENARYOLARI)
    fatura_tipi = "SATIS"

    musteri = _musteri_blok(fake, rng, lists)
    genel = _genel_blok(fake, rng, lists, senaryo, fatura_tipi)

    satirlar: list[list] = []
    for i in range(kalem_sayisi):
        mal, _, _, _ = _mal_hizmet_blok(fake, rng, lists)
        if i == 0:
            satir = list(musteri)
            for j in range(12, 35):
                satir[j] = genel[j]
            for j in range(35, 51):
                satir[j] = mal[j]
        else:
            satir = [None] * 52
            for j in range(35, 51):
                satir[j] = mal[j]
        satirlar.append(satir)

    return satirlar


def uret_faturalar(n: int, lists: FaturaLists, seed: int | None = None) -> list[list]:
    """n satır fatura verisi üretir (en fazla 2000 - şablon limiti).

    Satırlar faturalara gruplanır: her fatura 1-5 kalem içerir.
    Her faturanın ilk kaleminde müşteri + genel bilgiler dolu,
    sonraki kalemlerde sadece mal/hizmet bilgileri vardır.
    """
    if not 1 <= n <= 2000:
        raise ValueError("Fatura satır sayısı 1-2000 arasında olmalı (şablon limiti).")
    fake = make_faker(seed)
    rng = random.Random(seed)

    satirlar: list[list] = []
    while len(satirlar) < n:
        kalan = n - len(satirlar)
        kalem = min(rng.randint(1, 5), kalan)
        satirlar.extend(_fatura_olustur(fake, rng, lists, kalem))

    return satirlar[:n]
