# 🏗️ Açık Öğretim Portal - Kapsamlı Yeniden Yapılandırma Planı

## 📋 Mevcut Durum Analizi

### Klasör Yapısı
```
ataaof-denemeler/
├── libs/                    # Python kütüphaneleri
│   ├── pipeline.py          # Base pipeline sınıfı
│   ├── anadolu_pipeline.py  # Anadolu AÖF veri çekme
│   ├── auzef_pipeline.py    # AUZEF veri çekme
│   └── shared.py            # Ortak fonksiyonlar
├── anadolu/                 # Anadolu AÖF scriptleri
│   ├── scripts/             # 43 script dosyası
│   └── fetch.py             # Ana veri çekici
├── scripts/                 # Genel scriptler (39 dosya)
├── output/                  # Çıktı dosyaları (1.8GB)
│   ├── Anadolu/             # Eski yapı
│   ├── ATA-AÖF/             # Eski yapı
│   └── Auzef/               # Eski yapı
└── config/                  # Yeni konfigürasyon
```

### Sorunlar
1. **Tutarsız isimlendirme**: Türkçe karakterler, boşluklar
2. **Dağınık veri yapısı**: Her üniversite farklı format
3. **Tekrarlayan kod**: Her pipeline benzer mantık
4. **Jekyll sınırlamaları**: İnteraktif özellikler kısıtlı
5. **Manuel deployment**: Otomasyoneksik

---

## 🎯 Hedef Mimari

### 1. Monorepo Yapısı
```
acik-ogretim/
├── apps/
│   └── portal/              # Astro web uygulaması
│       ├── src/
│       │   ├── content/     # Content Collections
│       │   │   ├── universities/
│       │   │   ├── departments/
│       │   │   ├── courses/
│       │   │   └── questions/
│       │   ├── components/  # React/Astro bileşenler
│       │   ├── layouts/
│       │   └── pages/
│       └── astro.config.mjs
│
├── packages/
│   ├── core/                # Ortak TypeScript/Python kodu
│   │   ├── schemas/         # JSON Schemas & Zod
│   │   ├── utils/           # Ortak yardımcılar
│   │   └── types/           # TypeScript tipleri
│   │
│   ├── data-pipeline/       # Veri işleme (Python)
│   │   ├── pipelines/
│   │   │   ├── base.py
│   │   │   ├── anadolu.py
│   │   │   ├── ataturk.py
│   │   │   └── auzef.py
│   │   ├── enrichers/       # AI zenginleştirme
│   │   └── exporters/       # Format dönüştürücüler
│   │
│   └── mcp-server/          # MCP Server
│       ├── tools/
│       │   ├── fetch_questions.py
│       │   ├── search_courses.py
│       │   └── generate_quiz.py
│       └── server.py
│
├── data/                    # Ham ve işlenmiş veriler
│   ├── raw/                 # API'den çekilen ham veri
│   ├── processed/           # Normalize edilmiş veri
│   └── cache/               # Önbellek
│
└── .github/
    └── workflows/
        ├── build-portal.yml
        ├── deploy-pages.yml
        └── sync-data.yml
```

### 2. Veri Şeması Standartları

#### Üniversite
```typescript
interface University {
  id: string;           // "anadolu-aof"
  name: string;         // "Anadolu Üniversitesi"
  shortName: string;    // "Anadolu AÖF"
  faculty: string;      // "Açıköğretim Fakültesi"
  website: string;
  logo: string;
  color: string;
  departments: Department[];
}
```

#### Bölüm
```typescript
interface Department {
  id: string;           // "gorsel-iletisim"
  universityId: string; // "anadolu-aof"
  name: string;         // "Görsel İletişim Tasarımı"
  code: string;         // "GIT"
  degree: "onlisans" | "lisans" | "yukseklisans";
  duration: number;     // 8
  courses: Course[];
}
```

#### Ders
```typescript
interface Course {
  id: string;           // "temel-fotografcilik"
  departmentId: string;
  name: string;         // "Temel Fotoğrafçılık"
  code?: string;
  semester: number;     // 1-8
  credits?: number;
  units: Unit[];
}
```

#### Soru
```typescript
interface Question {
  id: string;
  courseId: string;
  unitNumber: number;
  text: string;
  options: { key: string; text: string }[];
  correctAnswer: string;
  explanation?: string;
  source: "soru-bankasi" | "cikmis-soru" | "deneme";
  metadata: {
    year?: number;
    examType?: string;
    difficulty?: string;
    topics?: string[];
  };
  enrichment?: {
    aiExplanation?: string;
    relatedQuestions?: string[];
    enrichedAt?: string;
  };
}
```

---

## 🔧 Uygulama Adımları

### Faz 1: Temel Altyapı (1-2 gün)
- [ ] Astro projesi oluştur
- [ ] Content Collections yapılandır
- [ ] Temel layout ve bileşenler
- [ ] Tailwind CSS kurulumu

### Faz 2: Veri Migrasyonu (2-3 gün)
- [ ] Mevcut JSON'ları yeni şemaya dönüştür
- [ ] Klasör yapısını yeniden organize et
- [ ] İndex dosyalarını oluştur
- [ ] Veri doğrulama scriptleri

### Faz 3: MCP Server (1-2 gün)
- [ ] MCP server yapısı oluştur
- [ ] Temel araçları tanımla
- [ ] Agent workflow'ları

### Faz 4: Pipeline Refactoring (2-3 gün)
- [ ] Base pipeline sınıfını güncelle
- [ ] Üniversite-spesifik pipeline'ları refactor et
- [ ] Yeni şemaya uyumlu çıktı

### Faz 5: Deployment (1 gün)
- [ ] GitHub Actions workflow'ları
- [ ] acik-ogretim.github.io deploy
- [ ] CI/CD testleri

---

## 🤖 MCP Server Araçları

```python
# mcp-server/tools/

# 1. Soru Arama
def search_questions(
    university: str = None,
    department: str = None,
    course: str = None,
    unit: int = None,
    keyword: str = None,
    limit: int = 10
) -> List[Question]:
    """Soru bankasında arama yapar."""

# 2. Quiz Oluştur
def generate_quiz(
    course_id: str,
    unit_numbers: List[int] = None,
    question_count: int = 10,
    difficulty: str = None
) -> Quiz:
    """Belirtilen dersten quiz oluşturur."""

# 3. Ders Listele
def list_courses(
    university: str = None,
    department: str = None,
    semester: int = None
) -> List[Course]:
    """Dersleri listeler."""

# 4. İstatistik
def get_stats(
    university: str = None,
    department: str = None
) -> Stats:
    """Portal istatistiklerini döndürür."""

# 5. Veri Güncelle
def sync_data(
    university: str,
    department: str = None,
    course: str = None
) -> SyncResult:
    """Belirtilen kaynaktan veri günceller."""
```

---

## 📁 Agent Workflows

### .agent/workflows/add-course.md
```markdown
---
description: Yeni ders eklemek için adımlar
---
1. Ders bilgilerini al (ad, kod, dönem, ünite sayısı)
2. `data/processed/{university}/{department}/courses/{course-id}/` oluştur
3. `course.json` metadata dosyası oluştur
4. Pipeline'ı çalıştır: `python -m packages.data_pipeline.run --course {id}`
5. Portal'ı build et: `npm run build --workspace=apps/portal`
```

### .agent/workflows/sync-university.md
```markdown
---
description: Üniversite verilerini güncelle
---
1. Üniversite ID'sini belirle
2. Pipeline'ı çalıştır: `python -m packages.data_pipeline.sync --university {id}`
3. Değişiklikleri kontrol et
4. Portal'ı rebuild et
5. Deploy workflow'u tetikle
```

---

## ⏭️ Sonraki Adım

Onayınızla Faz 1'e başlayabiliriz: **Astro projesi kurulumu**

```bash
cd /Users/wildgenie/Projects
npx create-astro@latest acik-ogretim-portal --template minimal --typescript strict
```
