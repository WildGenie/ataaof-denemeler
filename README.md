# Anadolu AÖF Soru Getirici

Bu proje, Anadolu Üniversitesi AÖF (Açıköğretim Fakültesi) öğrencileri için çıkmış soruları, deneme sınavlarını ve ders materyallerini indirmeyi ve düzenlemeyi sağlayan bir araçtır.

## Özellikler

- **Soru Bankası:** Ders ve ünite bazlı soru indirme.
- **Sorularla Öğrenelim:** "Sorularla Öğrenelim" modülündeki soruları ve PDF'leri indirme.
- **Çıkmış Sorular:** Geçmiş dönem sınavlarını PDF olarak indirme.
- **Materyaller:** Ders materyallerini listeleme ve indirme.
- **Kullanıcı Arayüzü:** Streamlit tabanlı kolay kullanım arayüzü.
- **Çıktı Formatları:** JSON ve Markdown formatında soru çıktıları.

## Kurulum

1. Projeyi klonlayın:
   ```bash
   git clone https://github.com/kullaniciadi/ataaof-denemeler.git
   cd ataaof-denemeler
   ```

2. Gerekli paketleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. `.env` dosyasını oluşturun ve `ANADOLU_AUTH_TOKEN` değişkenini ayarlayın.

## Kullanım

### Kullanıcı Arayüzü (Önerilen)

Projeyi görsel arayüz ile kullanmak için:

```bash
streamlit run anadolu/ui.py
```

Bu komut tarayıcınızda bir arayüz açacaktır. Buradan ders seçimi yapabilir, istediğiniz işlemi (Soru Bankası, Çıkmış Sorular vb.) seçip çalıştırabilirsiniz.

### Komut Satırı (Gelişmiş)

`anadolu/fetch.py` betiğini doğrudan komut satırından da kullanabilirsiniz:

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
- `--course`: Ders adı veya kodu (kısmi eşleşme).
- `--unit`: Sadece belirli bir üniteyi işlem.
- `--questions`: Standart soru bankasını indir (varsayılan).
- `--learn-questions`: "Sorularla Öğrenelim" sorularını indir.
- `--download-exams`: Çıkmış sınavları indir.
- `--materials`: Materyal listesini indir.
- `--chapters`: Ünite bilgilerini indir.
- `--pdf`: Soru ve cevap anahtarı PDF'lerini indir.
- `--parallel`: Paralel işlem sayısı (örn: `--parallel 4`).
- `--no-cache`: Önbelleği yoksay.
- `--local-only`: Sadece yerel dosyaları işle, API'ye gitme.

## Proje Yapısı

- `anadolu/`: Ana uygulama kodları.
    - `fetch.py`: Veri çekme ve işleme betiği.
    - `ui.py`: Streamlit kullanıcı arayüzü.
    - `dersler.json`: Ders listesi.
- `libs/`: Yardımcı kütüphaneler ve sınıflar.
    - `anadolu_pipeline.py`: Anadolu AÖF işlem mantığı.
    - `anadolu_lib.py`: Sabitler ve yardımcı fonksiyonlar.
    - `pipeline.py`: Genel soru işleme altyapısı.
- `output/`: İndirilen ve oluşturulan dosyalar.
    - `Anadolu/Donem X/Ders Adı/`: Ders bazlı çıktılar (JSON, Markdown, PDF).
- `scripts/`: Yardımcı ve bakım betikleri.
- `tests/`: Test dosyaları.

## Testler

Testleri çalıştırmak için:

```bash
python3 -m unittest tests/test_anadolu.py
python3 -m unittest tests/test_anadolu_repro.py
```
