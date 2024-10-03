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
    public long DogruCevapSirasi { get; set; }

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
    public long CevapSira { get; set; }
}

public class Program
{
    private static readonly HttpClient client = new HttpClient();

    public static async Task Main(string[] args)
    {
        // Ders listesini dersler.json dosyasından oku
        var dersler = JsonSerializer.Deserialize<List<Ders>>(File.ReadAllText("dersler.json"));
        string readmeDosyaAdi = $"readme.md";
        var readmeBuilder = new StringBuilder();
        readmeBuilder.AppendLine("# ATA-AÖF Grafik Sanatlar Soruları");

        foreach (var ders in dersler)
        {
            string markdownDosyaAdi = $"{ders.DersiVeren ?? "ATA-AÖF"} - Dönem {ders.Donem} - {ders.CourseName} - Sorular.md";
            readmeBuilder.AppendLine($"- [Dönem {ders.Donem} - {ders.CourseName}](<{markdownDosyaAdi}>)");

            var markdownBuilder = new StringBuilder();
            markdownBuilder.AppendLine($"# {ders.CourseName}");

            List<Soru> tumSorular = new List<Soru>();

            for (int unite = 1; unite <= 14; unite++)
            {
                markdownBuilder.AppendLine($"## Unite {unite}");
                var sorular = await GetSorular(ders.DersId, unite);
                tumSorular.AddRange(sorular);

                // Soruları Markdown formatında dosyaya ekle
                markdownBuilder.Append(SorulariMarkdownaDonustur(sorular));
            }

            // Tüm soruları JSON olarak dosyaya kaydet
            KaydetJson($"{ders.DersiVeren ?? "ATA-AÖF"} - Dönem {ders.Donem} - {ders.CourseName} - Tüm Sorular.json", tumSorular);

            File.WriteAllText(markdownDosyaAdi, markdownBuilder.ToString());
        }

        File.WriteAllText(readmeDosyaAdi, readmeBuilder.ToString());
    }

    public static async Task MainKitapcik(string[] args)
    {
        var dersler = JsonSerializer.Deserialize<List<Ders>>(File.ReadAllText("dersler.json"));

        foreach (var ders in dersler)
        {
            try
            {
                // ders için olan pdf'leri indir ve ders ismiyle kaydet 
                using var response = await client.GetAsync($"https://oys.ataaof.edu.tr/ktpcik/{ders.DersId}.pdf");
                response.EnsureSuccessStatusCode();
                var pdfBytes = await response.Content.ReadAsByteArrayAsync();
                File.WriteAllBytes($"{ders.CourseName} - 2024 Yaz Sınavı Soruları - {ders.DersiVeren ?? "ATA-AÖF"} - Dönem {ders.Donem}.pdf", pdfBytes);
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"PDF indirilemedi: {ex.Message}");
            }
        }
    }

    private static async Task<List<Soru>> GetSorular(string dersId, int unite)
    {
        var sorular = new List<Soru>();
        for (int i = 0; i < 7; i++)
        {
            var response = await client.GetAsync($"https://vtakip.ataaof.edu.tr/atametaservice.asmx/GetDenemeSoruByUnite?dersId={dersId}&unite={unite}");
            response.EnsureSuccessStatusCode();
            var gelenSorular = await response.Content.ReadFromJsonAsync<List<Soru>>();
            foreach (var soru in gelenSorular)
            {
                if (!sorular.Any(s => s.SoruId == soru.SoruId))
                {
                    sorular.Add(soru);
                }
            }
        }
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
        string json = JsonSerializer.Serialize(veri, new JsonSerializerOptions
        {
            WriteIndented = true,
            Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping
        });
        File.WriteAllText(dosyaAdi, json);
    }
}