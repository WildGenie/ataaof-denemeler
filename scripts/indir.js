const fs = require('fs');
const path = require('path');

// --- LOAD CONFIGURATION FROM .ENV ---
function loadEnv() {
    const envPath = path.join(__dirname, '../.env');
    if (fs.existsSync(envPath)) {
        const envContent = fs.readFileSync(envPath, 'utf8');
        envContent.split('\n').forEach(line => {
            const [key, ...valueParts] = line.split('=');
            if (key && valueParts.length > 0) {
                const value = valueParts.join('=').trim().replace(/^["']|["']$/g, '');
                process.env[key.trim()] = value;
            }
        });
    }
}
loadEnv();

const AUTH_TOKEN = process.env.AUZEF_BEARER_TOKEN;
// ------------------------------------

if (!AUTH_TOKEN) {
    console.error("❌ ERROR: AUZEF_BEARER_TOKEN not found in .env file.");
    process.exit(1);
}

const TARGET_COURSES = [
    { "id": 13579, "name": "ÇOCUK GELİŞİMİ UYGULAMALARI I" },
    { "id": 13576, "name": "OKUL ÖNCESİ DÖNEMDE DUYU EĞİTİMİ" },
    { "id": 18114, "name": "OYUN VE OYUN TERAPİSİ" },
    { "id": 13573, "name": "ÜSTÜN ZEKALI VE YETENEKLİ ÇOCUKLAR VE EĞİTİMLERİ" },
    { "id": 13577, "name": "ÇOCUKLUKTA YABANCI DİL OLARAK TÜRKÇE ÖĞRETİMİ" },
    { "id": 13571, "name": "İLKOKULA HAZIRLIK" },
    { "id": 13574, "name": "KORUYUCU RUH SAĞLIĞI VE DAYANIKLILIK" },
    { "id": 18128, "name": "PSİKOMETRİK - GELİŞİMSEL ÖLÇME VE DEĞERLENDİRME" },
    { "id": 13570, "name": "SOSYAL-DUYGUSAL GELİŞİM" }
];

const HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "tr,en-US;q=0.9,en;q=0.8",
    "authorization": AUTH_TOKEN,
    "content-type": "application/json",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "Referer": "https://auzefsinav.istanbul.edu.tr/"
};

const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Helper to normalize strings for comparison (handles Turkish characters)
function normalize(str) {
    if (!str) return "";
    return str
        .replace(/İ/g, 'i') // Handle uppercase dotted İ
        .replace(/I/g, 'i') // Handle uppercase dotless I
        .toLowerCase()
        .replace(/ı/g, 'i')
        .replace(/ğ/g, 'g')
        .replace(/ü/g, 'u')
        .replace(/ş/g, 's')
        .replace(/ö/g, 'o')
        .replace(/ç/g, 'c')
        .replace(/-/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

// Helper to find course directory in output/Auzef
function findCourseDir(courseName) {
    const baseDir = path.join(__dirname, '../output/Auzef');
    const terms = ['Donem 1', 'Donem 2', 'Donem 3', 'Donem 4', 'Donem 5', 'Donem 6', 'Donem 7', 'Donem 8'];

    const targetNorm = normalize(courseName);

    for (const term of terms) {
        const termPath = path.join(baseDir, term);
        if (!fs.existsSync(termPath)) continue;

        const dirs = fs.readdirSync(termPath);
        for (const dirName of dirs) {
            if (normalize(dirName) === targetNorm) {
                return path.join(termPath, dirName);
            }
        }
    }
    return null;
}

async function main() {
    console.log(`Starting download for ${TARGET_COURSES.length} courses...`);

    const sectionId = 47;
    const bookletType = 'A';

    for (const course of TARGET_COURSES) {
        console.log(`\n[Processing] ${course.name}`);

        const courseBaseDir = findCourseDir(course.name);
        if (!courseBaseDir) {
            console.error(`  ❌ ERROR: Could not find directory for "${course.name}" in output/Auzef/Donem X/`);
            continue;
        }

        const materyallerDir = path.join(courseBaseDir, 'Materyaller');
        if (!fs.existsSync(materyallerDir)) {
            fs.mkdirSync(materyallerDir, { recursive: true });
            console.log(`  Created directory: ${materyallerDir}`);
        }

        const fileName = "Dönem Sonu Sınavı 2025-2026.pdf";
        const filePath = path.join(materyallerDir, fileName);

        if (fs.existsSync(filePath)) {
            console.log(`  [Exists] ${filePath}`);
            // continue; // Re-download to be sure since it's a test? No, let's keep it if exists.
        }

        console.log(`  [Downloading] CourseID: ${course.id}, SectionID: ${sectionId}...`);

        try {
            const url = `https://service-auzefsinav.istanbul.edu.tr/api/Student/GetBooklet?sectionId=${sectionId}&courseId=${course.id}&bookletType=${bookletType}`;

            const response = await fetch(url, {
                method: 'GET',
                headers: HEADERS
            });

            if (!response.ok) {
                console.error(`  ❌ Failed: ${response.status} ${response.statusText}`);
                continue;
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                 const data = await response.json();
                 console.error(`  ❌ Received JSON instead of PDF:`, JSON.stringify(data).substring(0, 100));
                 continue;
            }

            const buffer = Buffer.from(await response.arrayBuffer());
            if (buffer.length < 5000) {
                console.warn(`  ⚠️ Warning: File size is very small (${buffer.length} bytes). Might not be a valid PDF.`);
            }

            fs.writeFileSync(filePath, buffer);
            console.log(`  ✅ Saved to: ${filePath} (${(buffer.length/1024).toFixed(2)} KB)`);

            await delay(1500);

        } catch (err) {
            console.error(`  ❌ Error:`, err.message);
        }
    }
}

main();
