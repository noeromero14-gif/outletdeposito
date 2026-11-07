# Add real unit photos (downloaded from the Drive folder "Fotos Outlet") to the page kit.
# Usage: python3 -I reales.py <kitdir> <outdir> <modified.json> <download1.json> [<download2.json> ...]
#   modified.json  = {"<driveFileId>": "<modifiedTime>"} for the files being added (from search_files)
#   downloadN.json = Google Drive download_file_content result: {"id", "title", "content" (base64)}
# File names must look like OUT-17.jpg, OUT-17_2.jpg (case/extension free). Others are reported and skipped.
# Writes <outdir>/reales/<OUT-17[_n]>.jpg (max 1280 px, JPEG q80) and updates <kitdir>/reales.json:
#   {"units": {"OUT-17": ["reales/OUT-17.jpg", "reales/OUT-17_2.jpg"]}, "seen": {"<driveFileId>": "<modifiedTime>"}}
import json, sys, os, re, io, base64
from PIL import Image, ImageOps

kit, outdir, f_mod = sys.argv[1:4]
mod = json.load(open(f_mod))
man_p = os.path.join(kit, 'reales.json')
man = json.load(open(man_p)) if os.path.exists(man_p) else {'units': {}, 'seen': {}}
os.makedirs(os.path.join(outdir, 'reales'), exist_ok=True)
added, skipped = [], []
for f in sys.argv[4:]:
    d = json.load(open(f))
    m = re.match(r'^\s*OUT[-_ ]?(\d+)(?:[-_ ](\d+))?\b', d.get('title', ''), re.I)
    if not m: skipped.append(d.get('title')); continue
    code = f'OUT-{int(m.group(1))}'
    name = code + (f'_{int(m.group(2))}' if m.group(2) else '') + '.jpg'
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(base64.b64decode(d['content'])))).convert('RGB')
    im.thumbnail((1280, 1280))
    im.save(os.path.join(outdir, 'reales', name), 'JPEG', quality=80, optimize=True)
    rel = 'reales/' + name
    lst = man['units'].setdefault(code, [])
    if rel not in lst: lst.append(rel)
    lst.sort(key=lambda s: (len(s), s))
    man['seen'][d['id']] = mod.get(d['id'], '')
    added.append(rel)
json.dump(man, open(man_p, 'w'), ensure_ascii=False, indent=0)
print(json.dumps({'agregadas': added, 'nombre_invalido': skipped}, ensure_ascii=False))
