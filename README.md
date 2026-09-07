# Ürün Müşteri Excel — Fake Veri Üretici

`data/` içindeki içe-aktarma şablonlarına uygun fake veri üretir.
Şablonlar olduğu gibi kopyalanır (başlıklar, liste sayfaları, doğrulamalar korunur),
sadece ilk sayfaya veri satırı basılır.

## Yapı

- `generators/cari_generator.py` — cari (müşteri/tedarikçi) üretici
- `generators/stok_generator.py` — stok/ürün üretici
- `generators/template_reader.py` — şablondaki İl/Ülke/Birim/KDV/Teslimat/Sevkiyat listelerini okur
- `generators/writer.py` — şablonu kopyalayıp satır basar
- `generators/common.py` — tr_TR Faker + seed yardımcısı

## Kullanım

```bash
uv run python main.py --tip cari --satir 100
uv run python main.py --tip stok --satir 250 --seed 42
uv run python main.py --tip all --satir 50 --cikti output
```

- `--tip`: `cari` | `stok` | `all` (varsayılan `all`)
- `--satir`: 1-2000 (şablon limiti, varsayılan 100)
- `--seed`: tekrarlanabilir üretim için sayı
- `--cikti`: çıktı klasörü (varsayılan `./output`)

Çıktılar: `output/cari-fake-<n>.xlsx`, `output/stok-fake-<n>.xlsx`

## Kurallar

- Cari: Vergi No checksum'lu VKN (%70) / TCKN (%30); Tüzel ise Unvan dolu + Ad/Soyad boş, Gerçek ise tersi; Tip %45 Tüzel / %45 Gerçek / %10 boş; Şehir/Ülke şablon listelerinden.
- Stok: Birim Kodu şablon listesinden (C62 ağırlıklı), Fiyat ≥ 0 sayısal, Aktif ∈ {Aktif, Pasif}, KDV ∈ {0,1,8,10,18,20}.
