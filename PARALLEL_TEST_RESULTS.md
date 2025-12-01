# Paralel İşlem Test Sonuçları

## Test Senaryosu
- **Dersler**: 6 adet "Görsel" içeren ders
- **İşlem**: Her dersin 1. ünitesini çekme (cache kullanmadan)
- **Toplam API çağrısı**: ~120 (6 ders × 20 retry)

## Performans Karşılaştırması

### Sequential (--parallel 1)
```
Total time: 35.884 seconds
CPU usage: 5%
```

### Parallel (--parallel 4)
```
Total time: 12.262 seconds
CPU usage: 15%
```

## Sonuçlar

| Metrik | Sequential | Parallel (4 workers) | İyileştirme |
|--------|-----------|---------------------|-------------|
| **Toplam Süre** | 35.88s | 12.26s | **2.93x daha hızlı** |
| **CPU Kullanımı** | 5% | 15% | 3x artış |
| **Verimlilik** | Düşük | Yüksek | - |

## Çıkarımlar

1. **Hız Kazancı**: Paralel işlem ile ~3x hızlanma sağlandı
2. **CPU Optimizasyonu**: CPU kullanımı artsa da toplam süre çok daha kısa
3. **I/O Bound**: API çağrıları I/O-bound olduğu için paralel işlem çok etkili
4. **Ölçeklenebilirlik**: Daha fazla ders için kazanç daha da artacak

## Öneriler

- **2-4 ders için**: `--parallel 2`
- **5-10 ders için**: `--parallel 4`
- **10+ ders için**: `--parallel 8`
- **Tüm dersler için**: `--parallel 16` (API rate limit'e dikkat!)

## Örnek Kullanım

```bash
# Hızlı test (cache kullanmadan)
python3 anadolu/fetch.py --course "Görsel" --unit 1 --no-cache --parallel 4

# Tüm üniteler için paralel işlem
python3 anadolu/fetch.py --course "Tarih" --parallel 8

# PDF indirme ile paralel işlem
python3 anadolu/fetch.py --parallel 4 --pdf

# Chapter bilgisi ile paralel işlem
python3 anadolu/fetch.py --parallel 8 --chapters
```

## Notlar

- `--no-cache` bayrağı cache'i bypass eder ve her seferinde API'den çeker
- Paralel işlem thread-safe'tir, veri kaybı riski yoktur
- Her worker bağımsız çalışır, bir hata diğerlerini etkilemez
