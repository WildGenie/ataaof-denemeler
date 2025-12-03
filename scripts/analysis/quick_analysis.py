import json

with open("report_unmatched_targets.json") as f:
    unmatched = json.load(f)

# Count by year
year_2024_25 = sum(1 for x in unmatched if "2024-2025" in x["TargetFile"])
year_2023_24 = sum(1 for x in unmatched if "2023-2024" in x["TargetFile"])
year_2022_23 = sum(1 for x in unmatched if "2022-2023" in x["TargetFile"])
year_2021_22 = sum(1 for x in unmatched if "2021-2022" in x["TargetFile"])

# Count by type
ara_sinav = sum(1 for x in unmatched if "Ara Sınav" in x["TargetFile"] or "Ara Sınav" in x["TargetFile"])
donem_sonu = sum(1 for x in unmatched if "Dönem Sonu" in x["TargetFile"])
yaz_okulu = sum(1 for x in unmatched if "Yaz Okulu" in x["TargetFile"])

print("=== EŞLEŞMEYEN DOSYALAR ANALİZİ ===")
print(f"\nToplam: {len(unmatched)} dosya")
print(f"\n📅 YILLARA GÖRE:")
print(f"  2024-2025: {year_2024_25} dosya ({year_2024_25*100//len(unmatched)}%)")
print(f"  2023-2024: {year_2023_24} dosya")
print(f"  2022-2023: {year_2022_23} dosya")
print(f"  2021-2022: {year_2021_22} dosya")
print(f"\n📝 TİPLERE GÖRE:")
print(f"  Ara Sınav: {ara_sinav} dosya")
print(f"  Dönem Sonu: {donem_sonu} dosya")
print(f"  Yaz Okulu: {yaz_okulu} dosya")

# Sample unmatched for Temel Sanat
temel_sanat = [x for x in unmatched if x["Course"] == "Temel Sanat ve Tasarım Eğitimi"]
print(f"\n📖 Temel Sanat ve Tasarım Eğitimi: {len(temel_sanat)} eşleşmemiş")
for item in temel_sanat[:3]:
    print(f"  ❌ {item['TargetFile']}")
