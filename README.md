# Anadolu AÖF Soru Getirici

Bu proje, Anadolu Üniversitesi AÖF (Açıköğretim Fakültesi) öğrencileri için çıkmış soruları, deneme sınavlarını ve ders materyallerini indirmeyi, düzenlemeyi ve **AI ile zenginleştirmeyi** sağlayan kapsamlı bir araçtır.

## ✨ Özellikler

### 📚 Temel Özellikler
- **Soru Bankası:** Ders ve ünite bazlı soru indirme
- **Sorularla Öğrenelim:** "Sorularla Öğrenelim" modülündeki soruları ve PDF'leri indirme
- **Çıkmış Sorular:** Geçmiş dönem sınavlarını PDF olarak indirme
- **Materyaller:** Ders materyallerini listeleme ve indirme
- **Kullanıcı Arayüzü:** Streamlit tabanlı kolay kullanım arayüzü
- **Çıktı Formatları:** JSON ve Markdown formatında soru çıktıları

### 🤖 AI Zenginleştirme
- **Akıllı Açıklamalar:** Google Gemini AI ile her soru için detaylı açıklamalar
- **Konu Etiketleme:** Soruların otomatik konu sınıflandırması
- **Ünite Özeti Entegrasyonu:** Tüm ünite özetlerini kullanarak bağlamsal açıklamalar
- **Toplu İşlem:** Tüm dersler için otomatik zenginleştirme desteği

### 🔧 Gelişmiş Araçlar
- **Yerel Materyal Eşleştirme:** Google Drive'daki materyalleri otomatik eşleştirme ve kopyalama
- **Sınav Dönüştürme:** PDF sınavları JSON formatına dönüştürme
- **Markdown Üretimi:** Tüm içerikleri okunabilir Markdown formatına dönüştürme
- **İndeks Oluşturma:** Ders ve ünite bazlı otomatik indeks sayfaları

## 🚀 Kurulum

1. **Projeyi klonlayın:**
   ```bash
   git clone https://github.com/kullaniciadi/ataaof-denemeler.git
   cd ataaof-denemeler
   ```

2. **Gerekli paketleri yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ortam değişkenlerini ayarlayın:**

   `.env` dosyası oluşturun ve aşağıdaki değişkenleri ekleyin:
   ```env
   # Zorunlu: Anadolu AÖF kimlik doğrulama token'ı
   ANADOLU_AUTH_TOKEN=your_token_here

   # İsteğe bağlı: AI zenginleştirme için Gemini API anahtarı
   GEMINI_API_KEY=your_gemini_api_key

   # İsteğe bağlı: Yerel materyal eşleştirme için Google Drive yolu
   LOCAL_MATERIALS_ROOT=/path/to/your/materials
   ```

## 📖 Kullanım

### 🖥️ Kullanıcı Arayüzü (Önerilen)

Projeyi görsel arayüz ile kullanmak için:

```bash
streamlit run anadolu/ui.py
```

Bu komut tarayıcınızda bir arayüz açacaktır. Buradan ders seçimi yapabilir, istediğiniz işlemi (Soru Bankası, Çıkmış Sorular vb.) seçip çalıştırabilirsiniz.

### ⌨️ Komut Satırı (Gelişmiş)

#### Temel Veri İndirme

`anadolu/fetch.py` betiğini doğrudan komut satırından kullanabilirsiniz:

```bash
# Belirli bir dersin tüm ünitelerini indir
python anadolu/fetch.py --course "Ders Adı"

# Belirli bir üniteyi indir
python anadolu/fetch.py --course "Ders Adı" --unit 1

# Çıkmış soruları indir
python anadolu/fetch.py --course "Ders Adı" --download-exams

# Sorularla Öğrenelim modülünü indir
python anadolu/fetch.py --course "Ders Adı" --learn-questions
```

**Parametreler:**
- `--course`: Ders adı veya kodu (kısmi eşleşme)
- `--unit`: Sadece belirli bir üniteyi işle
- `--questions`: Standart soru bankasını indir (varsayılan)
- `--learn-questions`: "Sorularla Öğrenelim" sorularını indir
- `--download-exams`: Çıkmış sınavları indir
- `--materials`: Materyal listesini indir
- `--chapters`: Ünite bilgilerini indir
- `--pdf`: Soru ve cevap anahtarı PDF'lerini indir
- `--parallel`: Paralel işlem sayısı (örn: `--parallel 4`)
- `--no-cache`: Önbelleği yoksay
- `--local-only`: Sadece yerel dosyaları işle, API'ye gitme

#### AI Soru Zenginleştirme

Soruları AI ile zenginleştirmek için:

```bash
# Tek bir ders için zenginleştirme
python anadolu/scripts/enrich_questions.py --course "Ders Adı" --donem 1

# Önbelleği yoksayarak yeniden işle
python anadolu/scripts/enrich_questions.py --course "Ders Adı" --donem 1 --no-cache
```

**Toplu Zenginleştirme:**

```bash
# Tüm dersler için zenginleştirme
python anadolu/scripts/process_all_enrichments.py

# Sadece kayıtlı dersler için
python anadolu/scripts/process_all_enrichments.py --enrolled

# Belirli bir dönem için
python anadolu/scripts/process_all_enrichments.py --donem 3

# Belirli bir yarıyıl için (Güz veya Bahar)
python anadolu/scripts/process_all_enrichments.py --semester guz

# Ders adına göre filtrele
python anadolu/scripts/process_all_enrichments.py --course "Fotoğraf"
```

#### Markdown Dönüştürme

```bash
# Tek bir ders için Markdown oluştur
python anadolu/scripts/convert_to_markdown.py --course "Ders Adı" --donem 1

# Tüm dersler için Markdown oluştur
python anadolu/scripts/process_all_markdown.py

# Kayıtlı dersler için
python anadolu/scripts/process_all_markdown.py --enrolled
```

#### Yerel Materyal Eşleştirme

Google Drive'daki materyalleri otomatik olarak eşleştirip kopyalamak için:

```bash
# Tek bir ders için eşleştirme
python anadolu/scripts/match_local_materials.py --course "Ders Adı" --donem 1

# Tüm materyalleri kopyala
python scripts/copy_local_materials.py
```

#### Sınav Dönüştürme

PDF sınavları JSON formatına dönüştürmek için:

```bash
python anadolu/scripts/convert_exams_to_json.py --course "Ders Adı" --donem 1
```

#### İndeks Oluşturma

Ders ve ünite bazlı indeks sayfaları oluşturmak için:

```bash
# Tek bir ders için indeks
python anadolu/scripts/generate_index.py --course "Ders Adı" --donem 1

# Tüm dersler için indeks
python scripts/generate_indexes.py
```

## 📁 Proje Yapısı

```
ataaof-denemeler/
├── anadolu/                    # Ana uygulama kodları
│   ├── fetch.py               # Veri çekme ve işleme betiği
│   ├── ui.py                  # Streamlit kullanıcı arayüzü
│   ├── dersler.json           # Ders listesi
│   ├── enrolled_courses.json  # Kayıtlı dersler
│   ├── scripts/               # İşlem betikleri
│   │   ├── enrich_questions.py           # AI soru zenginleştirme
│   │   ├── process_all_enrichments.py    # Toplu zenginleştirme
│   │   ├── process_all_courses.py        # Toplu ders işleme
│   │   ├── process_all_markdown.py       # Toplu Markdown üretimi
│   │   ├── convert_to_markdown.py        # Markdown dönüştürücü
│   │   ├── convert_exams_to_json.py      # Sınav dönüştürücü
│   │   ├── generate_index.py             # İndeks oluşturucu
│   │   ├── match_local_materials.py      # Materyal eşleştirici
│   │   └── check_missing_materials.py    # Eksik materyal kontrolü
│   └── utils/                 # Yardımcı araçlar
├── libs/                      # Kütüphaneler
│   ├── anadolu_pipeline.py   # Anadolu AÖF işlem mantığı
│   ├── anadolu_lib.py        # Sabitler ve yardımcı fonksiyonlar
│   └── pipeline.py           # Genel soru işleme altyapısı
├── scripts/                   # Genel yardımcı betikler
│   ├── copy_local_materials.py  # Materyal kopyalayıcı
│   ├── generate_indexes.py      # Toplu indeks oluşturucu
│   ├── reverse_match.py         # Ters materyal eşleştirme
│   └── analysis/                # Analiz betikleri
├── output/                    # Çıktı dosyaları
│   └── Anadolu/
│       └── Donem X/
│           └── Ders Adı/
│               ├── questions.json           # Soru bankası
│               ├── questions_enriched.json  # Zenginleştirilmiş sorular
│               ├── index.md                 # Ders indeksi
│               ├── exams/                   # Çıkmış sınavlar
│               ├── materials/               # Ders materyalleri
│               └── summaries/               # Ünite özetleri
├── data/                      # Veri dosyaları
├── reports/                   # Raporlar
├── tests/                     # Test dosyaları
├── requirements.txt           # Python bağımlılıkları
└── .env                       # Ortam değişkenleri
```

## 🧪 Testler

Testleri çalıştırmak için:

```bash
python3 -m unittest tests/test_anadolu.py
python3 -m unittest tests/test_anadolu_repro.py
```

## 🔑 Gereksinimler

- Python 3.8+
- Anadolu AÖF hesabı ve kimlik doğrulama token'ı
- (İsteğe bağlı) Google Gemini API anahtarı (AI zenginleştirme için)
- (İsteğe bağlı) Google Drive erişimi (yerel materyal eşleştirme için)

## 📝 Notlar

- **AI Zenginleştirme:** Gemini API kullanımı için API anahtarı gereklidir. Ücretsiz kotalar mevcuttur.
- **Toplu İşlemler:** Büyük veri setleri için işlem süresi uzun olabilir. `tqdm` ile ilerleme takibi yapılır.
- **Önbellek:** İşlenmiş veriler önbelleklenir. Yeniden işlemek için `--no-cache` parametresini kullanın.
- **Materyal Eşleştirme:** Google Drive yolu `.env` dosyasında `LOCAL_MATERIALS_ROOT` olarak tanımlanmalıdır.

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen pull request göndermeden önce testleri çalıştırın.

## 📄 Lisans

Bu proje eğitim amaçlıdır ve Anadolu Üniversitesi AÖF öğrencileri için geliştirilmiştir.
