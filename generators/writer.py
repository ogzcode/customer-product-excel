"""Şablonu bozmeden veri satırı basar.

Strateji: şablon workbook'u olduğu gibi yükle, ilk sayfadaki
başlık satırını koru, eski veri satırlarını temizle, yeni
satırları append et. Böylece başlıklar, liste sayfaları,
doğrulamalar, filtre ve dondurma ayarları aynen korunur.
Satır sayısı 1001'i aşarsa veri doğrulama ve filtre aralıkları
da yeni son satıra kadar genişletilir.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from openpyxl import load_workbook

# Windows'ta antivirüs/OneDrive/arama dizini openpyxl'in geçici
# dosyasını kısa süreli kilitleyebiliyor (WinError 32). Kayıt bu
# yüzden birkaç kez denenir.
_KAYIT_DENEMESI = 5


def _aralik_genislet(ws, son_satir: int) -> None:
    """1001 veya 1048576'da biten doğrulama/filtre aralıklarını son satıra uzatır."""
    if son_satir <= 1001:
        return
    for dv in ws.data_validations.dataValidation:
        yeni = str(dv.sqref)
        for eski in ("1048576", "1001"):
            yeni = yeni.replace(eski, str(son_satir))
        if yeni != str(dv.sqref):
            dv.sqref = yeni
    if ws.auto_filter.ref:
        ref = ws.auto_filter.ref
        for eski in ("1048576", "1001"):
            ref = ref.replace(eski, str(son_satir))
        ws.auto_filter.ref = ref


def _kaydet(wb, output: Path) -> None:
    """wb.save'i geçici dosya kilitlerine karşı tekrar dener."""
    son_hata: PermissionError | None = None
    for deneme in range(1, _KAYIT_DENEMESI + 1):
        try:
            wb.save(output)
            return
        except PermissionError as e:
            son_hata = e
            time.sleep(0.5 * deneme)
    raise PermissionError(
        f"Excel kaydedilemedi: {output}. Çıktı dosyası Excel'de açıksa kapatıp "
        f"tekrar deneyin (geçici dosya başka işlem tarafından kilitli)."
    ) from son_hata


def sablona_yaz(template: Path, output: Path, rows: list[list], header_rows: int = 1) -> Path:
    if not 1 <= len(rows) <= 2000:
        raise ValueError("Şablon limiti: tek dosyada en fazla 2000 veri satırı.")
    wb = load_workbook(template)
    try:
        ws = wb.worksheets[0]
        if ws.max_row > header_rows:
            ws.delete_rows(header_rows + 1, ws.max_row - header_rows)
        for row in rows:
            ws.append(list(row))
        _aralik_genislet(ws, header_rows + len(rows))
        output.parent.mkdir(parents=True, exist_ok=True)
        _kaydet(wb, output)
    finally:
        wb.close()
    return output
