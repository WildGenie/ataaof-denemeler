import json, glob, os

def load_aciklamalar():
    mapping = {}
    for path in glob.glob('data/aciklamalar/*.json'):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data:
                mapping[entry['SoruID']] = entry['Aciklama']
    return mapping

def merge_into_ata(mapping):
    for path in glob.glob('output/ata/**/*.json', recursive=True):
        with open(path, 'r', encoding='utf-8') as f:
            ata_data = json.load(f)
        changed = False
        for q in ata_data:
            sid = q.get('SoruID')
            if sid and sid in mapping and 'Aciklama' not in q:
                q['Aciklama'] = mapping[sid]
                changed = True
        if changed:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(ata_data, f, ensure_ascii=False, indent=4)
            print(f'Merged into {path}')

if __name__ == '__main__':
    mapping = load_aciklamalar()
    merge_into_ata(mapping)
