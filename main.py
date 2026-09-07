"""Fake cari / stok / fatura Excel üretici CLI.

Örnekler:
    python main.py --tip cari --satir 100
    python main.py --tip stok --satir 250 --seed 42
    python main.py --tip fatura --satir 50 --seed 42
    python main.py --tip all --satir 50 --cikti output
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

from generators.cari_generator import uret_cariler
from generators.fatura_generator import uret_faturalar
from generators.stok_generator import uret_stoklar
from generators.template_reader import read_cari_lists, read_fatura_lists, read_stok_lists
from generators.writer import sablona_yaz

# Şablonlardaki eski tip veri doğrulama eklentisi için openpyxl'in
# verdiği zararsız uyarıyı gizle (çıktıyı kirletmesin).
warnings.filterwarnings(
    "ignore", message="Data Validation extension is not supported.*"
)

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
CARI_TEMPLATE = DATA / "Cari-Excel-Ice-Aktarma-Sablonu.xlsx"
STOK_TEMPLATE = DATA / "Stok-Excel-Ice-Aktarma-Sablonu.xlsx"
FATURA_TEMPLATE = DATA / "taslak-faturalar.xlsx"


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Şablonlara uygun fake cari/stok Excel üretir.")
    p.add_argument("--tip", choices=["cari", "stok", "fatura", "all"], default="all",
                   help="Hangi dosya üretilecek (varsayılan: all)")
    p.add_argument("--satir", type=int, default=100,
                   help="Dosya başına veri satırı (1-2000, varsayılan: 100)")
    p.add_argument("--seed", type=int, default=None, help="Tekrarlanabilirlik için seed")
    p.add_argument("--cikti", type=Path, default=BASE / "output",
                   help="Çıktı klasörü (varsayılan: ./output)")
    return p.parse_args(argv)


def uret_cari(n: int, seed: int | None, cikti: Path) -> Path:
    lists = read_cari_lists(CARI_TEMPLATE)
    rows = uret_cariler(n, lists, seed=seed)
    out = cikti / f"cari-fake-{n}.xlsx"
    return sablona_yaz(CARI_TEMPLATE, out, rows)


def uret_stok(n: int, seed: int | None, cikti: Path) -> Path:
    lists = read_stok_lists(STOK_TEMPLATE)
    rows = uret_stoklar(n, lists, seed=seed)
    out = cikti / f"stok-fake-{n}.xlsx"
    return sablona_yaz(STOK_TEMPLATE, out, rows)


def uret_fatura(n: int, seed: int | None, cikti: Path) -> Path:
    lists = read_fatura_lists(FATURA_TEMPLATE)
    rows = uret_faturalar(n, lists, seed=seed)
    out = cikti / f"fatura-fake-{n}.xlsx"
    return sablona_yaz(FATURA_TEMPLATE, out, rows, header_rows=3)


def main(argv=None) -> None:
    args = parse_args(argv)
    if not CARI_TEMPLATE.exists():
        raise FileNotFoundError(f"Cari şablon bulunamadı: {CARI_TEMPLATE}")
    if not STOK_TEMPLATE.exists():
        raise FileNotFoundError(f"Stok şablon bulunamadı: {STOK_TEMPLATE}")
    if not FATURA_TEMPLATE.exists():
        raise FileNotFoundError(f"Fatura şablon bulunamadı: {FATURA_TEMPLATE}")

    uretilen: list[Path] = []
    if args.tip in ("cari", "all"):
        uretilen.append(uret_cari(args.satir, args.seed, args.cikti))
    if args.tip in ("stok", "all"):
        seed_stok = None if args.seed is None else args.seed + 1
        uretilen.append(uret_stok(args.satir, seed_stok, args.cikti))
    if args.tip in ("fatura", "all"):
        seed_fatura = None if args.seed is None else args.seed + 2
        uretilen.append(uret_fatura(args.satir, seed_fatura, args.cikti))

    for dosya in uretilen:
        print(f"OK: {dosya}")


if __name__ == "__main__":
    main()
