# Streamlit UI Geliştirme Planı

## 📋 Mevcut Durum Analizi

### Mevcut Özellikler
- ✅ Temel ders seçimi
- ✅ Soru bankası, çıkmış sorular, sorularla öğrenelim modları
- ✅ Ünite bazlı filtreleme
- ✅ Paralel işlem desteği
- ✅ Komut satırı önizlemesi
- ✅ Gerçek zamanlı çıktı gösterimi

### Eksik Özellikler
- ❌ AI zenginleştirme arayüzü
- ❌ Markdown dönüştürme arayüzü
- ❌ Yerel materyal eşleştirme arayüzü
- ❌ Toplu işlem arayüzü
- ❌ İndeks oluşturma arayüzü
- ❌ Sınav dönüştürme arayüzü
- ❌ İlerleme takibi (progress bar)
- ❌ Çıktı dosyalarını görüntüleme
- ❌ İstatistikler ve raporlar
- ❌ Modern ve görsel tasarım

## 🎯 Geliştirme Hedefleri

### 1. Çok Sayfalı Uygulama Yapısı
Streamlit'in multi-page özelliğini kullanarak modüler yapı:
- 🏠 Ana Sayfa (Dashboard)
- 📥 Veri İndirme (mevcut fetch.py arayüzü)
- 🤖 AI Zenginleştirme
- 📝 Markdown Dönüştürme
- 📁 Materyal Yönetimi
- 📊 Raporlar ve İstatistikler
- ⚙️ Ayarlar

### 2. Modern Dashboard
- Toplam ders sayısı
- İşlenmiş ders sayısı
- Zenginleştirilmiş soru sayısı
- Son işlemler
- Hızlı erişim butonları

### 3. AI Zenginleştirme Sayfası
- Ders seçimi (tekli veya toplu)
- Dönem/yarıyıl filtreleme
- Kayıtlı dersler filtresi
- İlerleme çubuğu
- Gerçek zamanlı log gösterimi
- Başarı/hata istatistikleri

### 4. Markdown Dönüştürme Sayfası
- Tek ders veya toplu dönüştürme
- Önizleme özelliği
- İndirme linki

### 5. Materyal Yönetimi Sayfası
- Eksik materyalleri gösterme
- Yerel materyal eşleştirme
- Eşleştirme raporu görüntüleme
- Manuel eşleştirme seçenekleri

### 6. Raporlar ve İstatistikler
- Ders bazlı soru sayıları
- Zenginleştirme durumu
- Materyal durumu
- Grafik ve tablolar

### 7. Gelişmiş Özellikler
- Tema desteği (açık/koyu mod)
- Dışa aktarma (Excel, CSV)
- Arama ve filtreleme
- Toplu işlem kuyruğu
- Bildirim sistemi

## 🛠️ Teknik Detaylar

### Dosya Yapısı
```
anadolu/
├── ui.py (ana giriş noktası)
└── pages/
    ├── 1_📥_Veri_Indirme.py
    ├── 2_🤖_AI_Zenginlestirme.py
    ├── 3_📝_Markdown_Donusturme.py
    ├── 4_📁_Materyal_Yonetimi.py
    ├── 5_📊_Raporlar.py
    └── 6_⚙️_Ayarlar.py
```

### Kullanılacak Kütüphaneler
- `streamlit` - Ana framework
- `plotly` - İnteraktif grafikler
- `pandas` - Veri işleme ve tablolar
- `streamlit-option-menu` - Modern menü
- `streamlit-aggrid` - Gelişmiş tablolar

### Yeni Bileşenler
1. **ProgressTracker**: İşlem ilerlemesini takip eden bileşen
2. **CourseSelector**: Gelişmiş ders seçici
3. **LogViewer**: Gerçek zamanlı log görüntüleyici
4. **StatsCard**: İstatistik kartları
5. **FileExplorer**: Çıktı dosyalarını görüntüleme

## 📝 Uygulama Adımları

### Faz 1: Temel Yapı (Öncelik: Yüksek)
1. ✅ Multi-page yapısını oluştur
2. ✅ Ana dashboard sayfasını tasarla
3. ✅ Mevcut fetch.py arayüzünü sayfaya taşı
4. ✅ Ortak bileşenleri utils modülüne taşı

### Faz 2: AI Zenginleştirme (Öncelik: Yüksek)
1. ✅ AI zenginleştirme sayfası oluştur
2. ✅ Toplu işlem desteği ekle
3. ✅ İlerleme takibi ekle
4. ✅ Gerçek zamanlı log gösterimi

### Faz 3: Diğer Özellikler (Öncelik: Orta)
1. ⏳ Markdown dönüştürme sayfası
2. ⏳ Materyal yönetimi sayfası
3. ⏳ Raporlar sayfası
4. ⏳ Ayarlar sayfası

### Faz 4: Görsel İyileştirmeler (Öncelik: Orta)
1. ⏳ Modern tema uygula
2. ⏳ İkonlar ve görsel öğeler ekle
3. ⏳ Responsive tasarım
4. ⏳ Animasyonlar ve geçişler

### Faz 5: Gelişmiş Özellikler (Öncelik: Düşük)
1. ⏳ Dışa aktarma özellikleri
2. ⏳ Arama ve filtreleme
3. ⏳ Bildirim sistemi
4. ⏳ Kullanıcı tercihleri kaydetme

## 🎨 Tasarım Prensipleri

1. **Basitlik**: Kullanıcı dostu ve sezgisel arayüz
2. **Tutarlılık**: Tüm sayfalarda tutarlı tasarım
3. **Geri Bildirim**: Her işlem için net geri bildirim
4. **Performans**: Hızlı yükleme ve sorunsuz çalışma
5. **Erişilebilirlik**: Tüm kullanıcılar için erişilebilir

## 📊 Başarı Kriterleri

- ✅ Tüm mevcut özellikler korunmalı
- ✅ Yeni özellikler sorunsuz çalışmalı
- ✅ Kullanıcı deneyimi iyileştirilmeli
- ✅ Kod temiz ve bakımı kolay olmalı
- ✅ Dokümantasyon güncel olmalı

## 🚀 Sonraki Adımlar

1. Kullanıcıdan onay al
2. Faz 1'i uygula (Multi-page yapısı)
3. Faz 2'yi uygula (AI Zenginleştirme)
4. Test et ve geri bildirim al
5. Diğer fazları sırayla uygula
