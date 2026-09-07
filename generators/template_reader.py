"""Şablon Excel'lerdeki liste sayfalarını okur.

Sayfa adlarındaki Türkçe karakterler bazı şablonlarda bozuk
kaydedildiği için sayfalar önce sırayla (pozisyonla), tutmazsa
isim eşleşmesiyle bulunur. Liste verisi her zaman A sütunundan,
başlık satırı atlanarak okunur.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from openpyxl import load_workbook


@dataclass
class CariLists:
    iller: list[str]
    ulkeler: list[str]


@dataclass
class StokLists:
    birim_kodlari: list[str]  # ["C62", "PK", ...]
    birim_adlari: dict[str, str]  # {"C62": "ADET", ...}
    birim_ham: list[str]  # ham satırlar ["C62 - ADET", ...]
    kdv_oranlari: list[int]
    teslimat_kodlari: list[str]
    sevkiyat_kodlari: list[str]


@dataclass
class FaturaLists:
    ulkeler: list[str]
    birim_kodlari: list[str]
    birim_adlari: dict[str, str]


def _col_a_values(path: Path, sheet_index: int, name_hints: tuple[str, ...]) -> list:
    wb = load_workbook(path, data_only=True, read_only=True)
    try:
        ws = _pick_sheet(wb, sheet_index, name_hints)
        return [
            ws.cell(row=r, column=1).value
            for r in range(2, ws.max_row + 1)
            if ws.cell(row=r, column=1).value not in (None, "")
        ]
    finally:
        wb.close()


def _pick_sheet(wb, index: int, hints: tuple[str, ...]):
    titles = [ws.title.lower() for ws in wb.worksheets]
    for hint in hints:
        for ws, title in zip(wb.worksheets, titles):
            if hint in title:
                return ws
    return wb.worksheets[index]


def read_cari_lists(template: Path) -> CariLists:
    # Cariler=0, Açıklamalar=1, İl=2, Ülke=3
    iller = _col_a_values(template, 2, ("l listesi", "il ", "iller"))
    ulkeler = _col_a_values(template, 3, ("lke listesi", "ülke", "ulkeler"))
    return CariLists(
        iller=[str(v).strip() for v in iller],
        ulkeler=[str(v).strip() for v in ulkeler],
    )


def read_stok_lists(template: Path) -> StokLists:
    # Stoklar=0, Açıklamalar=1, Birim=2, KDV=3, Teslimat=4, Sevkiyat=5
    birim_ham = [str(v).strip() for v in _col_a_values(template, 2, ("birim",))]
    kdv_ham = _col_a_values(template, 3, ("kdv",))
    teslimat_ham = [str(v).strip() for v in _col_a_values(template, 4, ("teslimat",))]
    sevkiyat_ham = [str(v).strip() for v in _col_a_values(template, 5, ("sevkiyat",))]

    kodlar: list[str] = []
    adlar: dict[str, str] = {}
    for satir in birim_ham:
        kod, _, ad = satir.partition(" - ")
        kod = kod.strip()
        if kod and kod not in kodlar:
            kodlar.append(kod)
            adlar[kod] = ad.strip()

    kdvler = sorted({int(v) for v in kdv_ham})
    teslimatlar = [s.partition(" - ")[0].strip() for s in teslimat_ham if s.strip()]
    sevkiyatlar = [s.partition(" - ")[0].strip() for s in sevkiyat_ham if s.strip()]

    return StokLists(
        birim_kodlari=kodlar,
        birim_adlari=adlar,
        birim_ham=birim_ham,
        kdv_oranlari=kdvler,
        teslimat_kodlari=teslimatlar,
        sevkiyat_kodlari=sevkiyatlar,
    )


def read_fatura_lists(template: Path) -> FaturaLists:
    # Fatura Bilgileri=0, Ornek=1, Ulke=2, Birim=3, KDV=4
    ulkeler = _col_a_values(template, 2, ("lke listesi", "ülke", "ulkeler"))
    birim_ham = [str(v).strip() for v in _col_a_values(template, 3, ("birim",))]

    kodlar: list[str] = []
    adlar: dict[str, str] = {}
    for satir in birim_ham:
        satir = satir.replace("\xa0", " ")
        parts = satir.split(" - ")
        kod = parts[0].strip()
        if kod and kod not in kodlar:
            kodlar.append(kod)
            adlar[kod] = parts[1].strip() if len(parts) > 1 else ""

    return FaturaLists(
        ulkeler=[str(v).strip() for v in ulkeler],
        birim_kodlari=kodlar,
        birim_adlari=adlar,
    )
