using System.Net.Http.Json;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.Json.Serialization;

public class Ders
{
    [JsonPropertyName("Semester")]
    public string? Semester { get; set; }

    [JsonPropertyName("Donem")]
    public string Donem { get; set; }

    [JsonPropertyName("DersId")]
    public string DersId { get; set; }

    [JsonPropertyName("DersKodu")]
    public string DersKodu { get; set; }

    [JsonPropertyName("CourseName")]
    public string CourseName { get; set; }

    [JsonPropertyName("DersiVeren")]
    public string DersiVeren { get; set; }
}

public class Soru
{
    [JsonPropertyName("SoruID")]
    public long SoruId { get; set; }

    [JsonPropertyName("SoruMetni")]
    public string SoruMetni { get; set; }

    [JsonPropertyName("A")]
    public string A { get; set; }

    [JsonPropertyName("B")]
    public string B { get; set; }

    [JsonPropertyName("C")]
    public string C { get; set; }

    [JsonPropertyName("D")]
    public string D { get; set; }

    [JsonPropertyName("E")]
    public string E { get; set; }

    [JsonPropertyName("DogruCevap")]
    public string DogruCevap { get; set; }

    [JsonPropertyName("DersAd")]
    public string DersAd { get; set; }

    [JsonPropertyName("Somestre")]
    public long Somestre { get; set; }

    [JsonPropertyName("DogruCevapSirasi")]
    public long? DogruCevapSirasi { get; set; }

    [JsonPropertyName("Unite")]
    public long Unite { get; set; }

    [JsonPropertyName("OlusturmaTarihi")]
    public DateTimeOffset OlusturmaTarihi { get; set; }

    [JsonPropertyName("GelYer")]
    public long GelYer { get; set; }

    [JsonPropertyName("DersId")]
    public long DersId { get; set; }

    [JsonPropertyName("OBSDersId")]
    public long ObsDersId { get; set; }

    [JsonPropertyName("CevapSira")]
    public long? CevapSira { get; set; }
}

public class Program
{
    private static readonly HttpClient client = new HttpClient();
    private static string outputDirectory;
    private static string jsonDirectory;
    private static string mdDirectory;
    private static string pdfDirectory;

    public static async Task Main(string[] args)
    {
        Console.WriteLine("Program başladı.");
        // Check for a force re-process argument
        bool forceReprocess = args.Contains("--force");
        if (forceReprocess)
        {
            Console.WriteLine("Yeniden işleme zorunlu kılındı (`--force`).");
        }

        // Create output directories
        SetupOutputDirectories();
        
        await SorularMain(forceReprocess);
        //await SinavKitapcikMain(args);
        Console.WriteLine("Program bitti.");
    }

    private static void SetupOutputDirectories()
    {
        Console.WriteLine("Çıktı dizinleri oluşturuluyor...");
        // Get project directory (parent of the executing directory)
        string projectDirectory = Directory.GetCurrentDirectory();
        // ./bin/Debug/net8.0
        // Get the parent directory
        projectDirectory = Directory.GetParent(projectDirectory).Parent.Parent.FullName;
        Console.WriteLine($"Proje dizini: {projectDirectory}");
        
        // Create main output directory
        outputDirectory = Path.Combine(projectDirectory, "output");
        Directory.CreateDirectory(outputDirectory);
        Console.WriteLine($"Ana çıktı dizini oluşturuldu: {outputDirectory}");
        
        // Create subdirectories
        jsonDirectory = Path.Combine(outputDirectory, "json");
        mdDirectory = Path.Combine(outputDirectory, "md");
        pdfDirectory = Path.Combine(outputDirectory, "pdf");
        
        Directory.CreateDirectory(jsonDirectory);
        Directory.CreateDirectory(mdDirectory);
        Directory.CreateDirectory(pdfDirectory);
        Console.WriteLine("Alt dizinler (json, md, pdf) oluşturuldu.");
    }

    public static async Task SorularMain(bool forceReprocess)
    {
        Console.WriteLine("SorularMain başladı.");
        // Ders listesini dersler.json dosyasından oku
        Console.WriteLine("dersler.json okunuyor...");
        var dersler = JsonSerializer.Deserialize<List<Ders>>(File.ReadAllText("dersler.json"));
        Console.WriteLine($"{dersler.Count} ders bulundu.");

        string readmeDosyaAdi = Path.Combine(mdDirectory, "readme.md");
        var readmeBuilder = new StringBuilder();
        readmeBuilder.AppendLine("# ATA-AÖF Grafik Sanatlar Soruları");

        foreach (var ders in dersler)
        {
            string jsonFileName = $"{ders.DersiVeren ?? "ATA-AÖF"} - Dönem {ders.Donem} - {ders.CourseName} - Tüm Sorular.json";
            string jsonFilePath = Path.Combine(jsonDirectory, jsonFileName);

            string markdownFileName = $"{ders.DersiVeren ?? "ATA-AÖF"} - Dönem {ders.Donem} - {ders.CourseName} - Sorular.md";
            
            // Add to README regardless of whether it's skipped or not, to keep it complete
            readmeBuilder.AppendLine($"- [Dönem {ders.Donem} - {ders.CourseName}](<{markdownFileName}>)");

            // Skip if not forcing and the file was modified in the last 12 hours
            if (!forceReprocess && File.Exists(jsonFilePath))
            {
                var lastWriteTime = File.GetLastWriteTimeUtc(jsonFilePath);
                if ((DateTime.UtcNow - lastWriteTime) < TimeSpan.FromHours(12))
                {
                    Console.WriteLine($"'{ders.CourseName}' dersi yakın zamanda işlenmiş, atlanıyor.");
                    continue;
                }
            }

            Console.WriteLine($"İşlenen ders: {ders.CourseName} (ID: {ders.DersId})");
            
            var markdownBuilder = new StringBuilder();
            markdownBuilder.AppendLine($"# {ders.CourseName}");

            List<Soru> tumSorular = new List<Soru>();

            for (int unite = 1; unite <= 14; unite++)
            {
                Console.WriteLine($"  -> Ünite {unite} için sorular getiriliyor...");
                markdownBuilder.AppendLine($"## Unite {unite}");
                var sorular = await GetSorular(ders.DersId, unite);
                Console.WriteLine($"  -> {sorular.Count} adet yeni soru bulundu.");
                tumSorular.AddRange(sorular);

                // Soruları Markdown formatında dosyaya ekle
                markdownBuilder.Append(SorulariMarkdownaDonustur(sorular));
            }

            // Tüm soruları JSON olarak dosyaya kaydet
            Console.WriteLine($"Tüm sorular JSON olarak kaydediliyor: {jsonFileName}");
            KaydetJson(jsonFilePath, tumSorular);

            Console.WriteLine($"Markdown dosyası yazılıyor: {markdownFileName}");
            File.WriteAllText(Path.Combine(mdDirectory, markdownFileName), markdownBuilder.ToString());
        }

        Console.WriteLine($"Readme dosyası yazılıyor: {readmeDosyaAdi}");
        File.WriteAllText(readmeDosyaAdi, readmeBuilder.ToString());
        Console.WriteLine("SorularMain bitti.");
    }

    public static async Task SinavKitapcikMain(string[] args)
    {
        Console.WriteLine("SinavKitapcikMain başladı.");
        var dersler = JsonSerializer.Deserialize<List<Ders>>(File.ReadAllText("dersler.json"));
        Console.WriteLine($"{dersler.Count} ders için sınav kitapçıkları indirilecek.");

        foreach (var ders in dersler)
        {
            try
            {
                Console.WriteLine($"Ders için PDF indiriliyor: {ders.CourseName} (ID: {ders.DersId})");
                // ders için olan pdf'leri indir ve ders ismiyle kaydet 
                using var response = await client.GetAsync($"https://oys.ataaof.edu.tr/ktpcik/{ders.DersId}.pdf");
                response.EnsureSuccessStatusCode();
                var pdfBytes = await response.Content.ReadAsByteArrayAsync();
                string pdfFileName = $"{ders.Donem} - {ders.CourseName} - 2024-2025 Bütünleme Sınavı Soruları - ATA-AÖF.pdf";
                string pdfFilePath = Path.Combine(pdfDirectory, pdfFileName);
                Console.WriteLine($"PDF dosyası kaydediliyor: {pdfFileName}");
                File.WriteAllBytes(pdfFilePath, pdfBytes);
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"PDF indirilemedi: {ders.CourseName} (ID: {ders.DersId}) - Hata: {ex.Message}");
            }
        }
        Console.WriteLine("SinavKitapcikMain bitti.");
    }

    private static async Task<List<Soru>> GetSorular(string dersId, int unite)
    {
        Console.WriteLine($"    GetSorular çağrıldı: dersId={dersId}, unite={unite}");
        var sorular = new List<Soru>();
        for (int i = 0; i < 7; i++)
        {
            Console.WriteLine($"      -> Deneme {i + 1}/7");
            var response = await client.GetAsync($"https://vtakip.ataaof.edu.tr/atametaservice.asmx/GetDenemeSoruByUnite?dersId={dersId}&unite={unite}");
            response.EnsureSuccessStatusCode();
            var gelenSorular = await response.Content.ReadFromJsonAsync<List<Soru>>();
            if (gelenSorular != null)
            {
                foreach (var soru in gelenSorular)
                {
                    if (!sorular.Any(s => s.SoruId == soru.SoruId))
                    {
                        sorular.Add(soru);
                    }
                }
            }
        }
        Console.WriteLine($"    GetSorular tamamlandı: {sorular.Count} adet özgün soru bulundu.");
        return sorular.OrderBy(s => s.SoruId).ToList();
    }

    private static string SorulariMarkdownaDonustur(List<Soru> sorular)
    {
        var markdownBuilder = new StringBuilder();
        foreach (var soru in sorular)
        {
            markdownBuilder.AppendLine($"1. {soru.SoruMetni}");
            markdownBuilder.AppendLine($"    - {(soru.DogruCevap == "A" ? "**Cevap " : "")}A-) {soru.A.Trim()}{(soru.DogruCevap == "A" ? "**" : "")}");
            markdownBuilder.AppendLine($"    - {(soru.DogruCevap == "B" ? "**Cevap " : "")}B-) {soru.B.Trim()}{(soru.DogruCevap == "B" ? "**" : "")}");
            markdownBuilder.AppendLine($"    - {(soru.DogruCevap == "C" ? "**Cevap " : "")}C-) {soru.C.Trim()}{(soru.DogruCevap == "C" ? "**" : "")}");
            markdownBuilder.AppendLine($"    - {(soru.DogruCevap == "D" ? "**Cevap " : "")}D-) {soru.D.Trim()}{(soru.DogruCevap == "D" ? "**" : "")}");
            markdownBuilder.AppendLine($"    - {(soru.DogruCevap == "E" ? "**Cevap " : "")}E-) {soru.E.Trim()}{(soru.DogruCevap == "E" ? "**" : "")}");
            markdownBuilder.AppendLine("    ***");
        }
        return markdownBuilder.ToString();
    }

    private static void KaydetJson(string dosyaAdi, object veri)
    {
        Console.WriteLine($"  KaydetJson çağrıldı: {dosyaAdi}");
        string json = JsonSerializer.Serialize(veri, new JsonSerializerOptions
        {
            WriteIndented = true,
            Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping
        });
        File.WriteAllText(dosyaAdi, json);
        Console.WriteLine($"  JSON dosyası başarıyla kaydedildi.");
    }
}
