# ATA-AÖF & Anadolu AÖF Soru Bankası Araçları

Bu proje, Anadolu Üniversitesi (AÖF) ve Atatürk Üniversitesi (ATA-AÖF) açıköğretim sistemlerinden deneme sorularını, sınav kitapçıklarını ve ders özetlerini indirmek ve düzenlemek için geliştirilmiş araçları içerir.

## 🚀 Yeni Özellikler

- ✅ **Paralel İşlem Desteği**: Çoklu ders işleme için 3x daha hızlı performans
- ✅ **PDF İndirme**: Resmi sınav ve cevap anahtarı PDF'lerini indirme
- ✅ **Bölüm Bilgisi Çekme**: Ders bölüm (chapter) bilgilerini API'den alma
- ✅ **Cache Yönetimi**: `--no-cache` ile cache'i bypass etme
- ✅ **CLI Filtreleme**: Ders ve ünite bazlı seçici işlem

## Kurulum

Öncelikle gerekli Python paketlerini yükleyin:

```bash
pip3 install -r requirements.txt
```

### Ortam Değişkenleri

`.env` dosyası oluşturun ve Anadolu AÖF token'ınızı ekleyin:

```bash
ANADOLU_AUTH_TOKEN=your_token_here
```

## Proje Yapısı

```
.
├── anadolu/          # Anadolu AÖF araçları
│   └── fetch.py      # Ana soru çekme scripti
├── ata/              # ATA-AÖF araçları
│   ├── fetch.py      # Soru çekme
│   └── utils/        # Yardımcı araçlar
├── libs/             # Ortak kütüphaneler
│   ├── pipeline.py   # Base pipeline sınıfı
│   ├── anadolu_lib.py
│   ├── ata_lib.py
│   └── shared.py     # HTML temizleme, Markdown dönüştürme
├── tests/            # Unit testler
└── output/           # Çıktı dosyaları
    ├── anadolu/      # Anadolu AÖF çıktıları
    │   ├── raw/      # Ham JSON veriler
    │   ├── json/     # Temizlenmiş JSON
    │   ├── full/     # Tüm sorular (ders bazlı)
    │   ├── md/       # Markdown formatı
    │   └── pdf/      # İndirilen PDF'ler
    └── ata/          # ATA-AÖF çıktıları
```

## Kullanım

### 1. Anadolu AÖF Araçları

#### Temel Kullanım

```bash
# Tüm derslerin sorularını çek
python3 anadolu/fetch.py

# Belirli bir dersi çek (ders adı veya kodu ile)
python3 anadolu/fetch.py --course "Tarih"
python3 anadolu/fetch.py --course "GIT301U"

# Belirli bir üniteyi çek
python3 anadolu/fetch.py --course "Tarih" --unit 1
```

#### PDF İndirme

```bash
# Sınav ve cevap anahtarı PDF'lerini indir
python3 anadolu/fetch.py --course "Tarih" --pdf

# Belirli bir ünite için PDF indir
python3 anadolu/fetch.py --course "Tarih" --unit 1 --pdf
```

#### Bölüm Bilgisi Çekme

```bash
# Ders bölüm bilgilerini çek
python3 anadolu/fetch.py --course "GIT301U" --chapters
```

#### Paralel İşlem (⚡ Hızlı!)

```bash
# 4 paralel worker ile işle (3x daha hızlı)
python3 anadolu/fetch.py --parallel 4

# 8 paralel worker ile tüm dersleri işle
python3 anadolu/fetch.py --parallel 8

# Paralel işlem + PDF indirme
python3 anadolu/fetch.py --parallel 4 --pdf
```

#### Cache Yönetimi

```bash
# Cache kullanmadan API'den çek (test için)
python3 anadolu/fetch.py --course "Tarih" --no-cache

# Cache kullanmadan paralel işlem
python3 anadolu/fetch.py --parallel 4 --no-cache
```

#### Kombine Kullanım

```bash
# Tüm özellikleri birlikte kullan
python3 anadolu/fetch.py \
  --course "Görsel" \
  --unit 1 \
  --pdf \
  --chapters \
  --parallel 4 \
  --no-cache
```

### 2. ATA-AÖF Araçları

#### Soru İndirme

```bash
# Tüm derslerin sorularını çek
python3 ata/fetch.py

# Belirli bir dersi çek
python3 ata/fetch.py --course "Matematik"

# Belirli bir üniteyi çek
python3 ata/fetch.py --course "Matematik" --unit 1

# Paralel işlem ile
python3 ata/fetch.py --parallel 4
```

#### Sınav Kitapçıkları

```bash
# Bütünleme sınavı kitapçıklarını indir
python3 ata/utils/fetch_books.py
```

#### Ünite PDF'leri

```bash
# Ünite PDF'lerini indir
python3 ata/utils/fetch_units.py
```

#### Kısa Özetler

```bash
# Kısa özet PDF'lerini indir
python3 ata/utils/fetch_short_summary.py

# PDF'leri Markdown'a dönüştür
python3 ata/utils/process_short_summary.py
```

## Performans Karşılaştırması

| İşlem Modu | 6 Ders İçin Süre | Hızlanma |
|------------|------------------|----------|
| Sequential (`--parallel 1`) | 35.88s | 1x (baseline) |
| Parallel (`--parallel 4`) | 12.26s | **2.93x daha hızlı** |
| Parallel (`--parallel 8`) | ~8-10s | **~4x daha hızlı** |

### Önerilen Worker Sayıları

- **2-4 ders**: `--parallel 2`
- **5-10 ders**: `--parallel 4`
- **10+ ders**: `--parallel 8`
- **Tüm dersler**: `--parallel 16` (API rate limit'e dikkat!)

## Test

Tüm testleri çalıştırın:

```bash
# Tüm testler
python3 -m unittest discover tests -v

# Sadece Anadolu testleri
python3 -m unittest tests/test_anadolu.py -v
python3 -m unittest tests/test_anadolu_pdf.py -v

# Sadece paralel işlem testleri
python3 -m unittest tests/test_parallel.py -v

# Sadece ATA testleri
python3 -m unittest tests/test_ata.py -v
python3 -m unittest tests/test_ata_utils.py -v
```

## CLI Argümanları

### Anadolu AÖF (`anadolu/fetch.py`)

```
--course COURSE       Ders adı veya kodu ile filtrele (kısmi eşleşme)
--unit UNIT          Sadece belirli bir üniteyi çek
--pdf                Sınav ve cevap anahtarı PDF'lerini indir
--chapters           Ders bölüm bilgilerini çek
--parallel N         N sayıda paralel worker kullan (varsayılan: 1)
--no-cache           Cache'i bypass et, API'den çek
```

### ATA-AÖF (`ata/fetch.py`)

```
--course COURSE       Ders adı ile filtrele (kısmi eşleşme)
--unit UNIT          Sadece belirli bir üniteyi çek
--parallel N         N sayıda paralel worker kullan (varsayılan: 1)
```

## Çıktı Formatları

### JSON Formatı

```json
{
  "SoruID": 12345,
  "SoruMetni": "Soru metni...",
  "A": "Seçenek A",
  "B": "Seçenek B",
  "C": "Seçenek C",
  "D": "Seçenek D",
  "E": "Seçenek E",
  "DogruCevap": "A",
  "Aciklama": "Açıklama metni...",
  "Unite": 1,
  "Donem": 1
}
```

### Markdown Formatı

```markdown
## Unite 1

### Soru 1
Soru metni...

**A)** Seçenek A
**B)** Seçenek B
**C)** Seçenek C
**D)** Seçenek D
**E)** Seçenek E

**Doğru Cevap:** A

**Açıklama:** Açıklama metni...
```

## Önemli Notlar

- **API Rate Limiting**: Çok fazla paralel worker kullanırsanız API rate limit'e takılabilirsiniz
- **Cache Kullanımı**: Varsayılan olarak cache kullanılır, `--no-cache` ile devre dışı bırakılabilir
- **Thread Safety**: Paralel işlem thread-safe'tir, veri kaybı riski yoktur
- **Hata Yönetimi**: Bir worker'ın hatası diğerlerini etkilemez

## Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## Sorun Giderme

### "ModuleNotFoundError" hatası alıyorum

```bash
pip3 install -r requirements.txt
```

### "ANADOLU_AUTH_TOKEN not found" hatası

`.env` dosyası oluşturun ve token'ınızı ekleyin:

```bash
echo "ANADOLU_AUTH_TOKEN=your_token_here" > .env
```

### Paralel işlem çalışmıyor

Python 3.7+ gereklidir. Sürümünüzü kontrol edin:

```bash
python3 --version
```

### API rate limit hatası

Daha az worker kullanın:

```bash
python3 anadolu/fetch.py --parallel 2  # 4 yerine 2
```

## İletişim

Sorularınız için issue açabilirsiniz.
