# tqdm Entegrasyonu - Değişiklik Özeti

## Yapılan Değişiklikler

### 1. **requirements.txt**
- ✅ `tqdm` paketi eklendi

### 2. **libs/pipeline.py**
- ✅ `from tqdm import tqdm` import eklendi
- ✅ Tüm `print()` çağrıları `tqdm.write()` ile değiştirildi
  - `print(f"...")` → `tqdm.write(f"...")`

### 3. **anadolu/fetch.py**
- ✅ `from tqdm import tqdm` import eklendi
- ✅ Tüm `print()` çağrıları `tqdm.write()` ile değiştirildi
- ✅ Progress bar'lar eklendi:
  - **Paralel işlem**: `tqdm(total=len(filtered_courses), desc="Processing courses", unit="course")`
  - **Sequential işlem**: `tqdm(filtered_courses, desc="Processing courses", unit="course")`
  - **PDF indirme**: `tqdm(range(1, 15), desc="Fetching PDFs", leave=False, unit="unit")`

## Neden tqdm.write()?

`print()` kullanıldığında progress bar bozulur ve çıktı karışır:
```
Processing courses:  50%|████▌    | 3/6
Some log message
Processing courses:  67%|██████▋  | 4/6
```

`tqdm.write()` kullanıldığında progress bar korunur:
```
Processing courses:  50%|████▌    | 3/6 [00:05<00:05, 1.2course/s]
Some log message
Processing courses:  67%|██████▋  | 4/6 [00:07<00:03, 1.3course/s]
```

## Görsel Örnekler

### Sequential İşlem
```
Found 42 courses, processing 1 courses.
Processing Görsel Estetik...
Processing Görsel Estetik (Dönem: 1)...
    Unit 1: Loaded 78 raw questions from cache.
  Saved 78 unique questions to ...
Processing courses: 100%|██████████| 1/1 [00:02<00:00, 2.87s/course]
```

### Paralel İşlem
```
Found 42 courses, processing 6 courses.
Using 4 parallel workers...
Processing courses: 100%|██████████| 6/6 [00:12<00:00, 2.1s/course, ✓ Görsel Estetik]
```

### PDF İndirme
```
Processing courses: 100%|██████████| 1/1 [00:45<00:00, 45.2s/course]
  Fetching PDFs:  64%|██████▍   | 9/14 [00:09<00:05, 1.08s/unit]
```

## Test Sonuçları

Tüm testler başarılı:
```
Ran 4 tests in 0.015s
OK
```

## Avantajlar

1. ✅ **Temiz Çıktı**: Progress bar bozulmadan log mesajları görüntülenir
2. ✅ **Gerçek Zamanlı İlerleme**: Kullanıcı işlemin ne kadar süreceğini görebilir
3. ✅ **Hız Metrikleri**: course/s veya unit/s göstergesi
4. ✅ **ETA (Tahmini Süre)**: Kalan süre tahmini
5. ✅ **Nested Progress Bars**: PDF indirme gibi alt işlemler için
6. ✅ **Renkli ve Görsel**: Terminal çıktısı daha profesyonel

## Kullanım Örnekleri

```bash
# Sequential (progress bar ile)
python3 anadolu/fetch.py --course "Tarih"

# Paralel (4 worker, progress bar ile)
python3 anadolu/fetch.py --course "Görsel" --parallel 4

# PDF indirme (nested progress bar)
python3 anadolu/fetch.py --course "Tarih" --pdf
```

## Notlar

- `tqdm.write()` thread-safe'tir, paralel işlemde güvenle kullanılabilir
- Progress bar otomatik olarak terminal genişliğine uyum sağlar
- `leave=False` parametresi ile geçici progress bar'lar oluşturulabilir
- `set_postfix_str()` ile progress bar'a dinamik bilgi eklenebilir
