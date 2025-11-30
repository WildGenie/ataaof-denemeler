import json

with open('sorular-anadolu/sorular.json', 'r') as f:
    data = json.load(f)

for semester in data:
    donem = semester['donem']
    for course in semester['dersler']:
        ders_adi = course['dersAdi']
        # Link format: <Anadolu - Dönem X - Ders Adı - Sorular>
        link_text = f"Dönem {donem} - {ders_adi}"
        link_target = f"Anadolu - Dönem {donem} - {ders_adi} - Sorular"
        print(f"- [{link_text}](<{link_target}>)<br />")
