# Rebuild the Outlet sales page from live sheet extracts.
# Usage: python3 -I build.py <kitdir> <outlet.json> <inv.json> <liq_mla.json> <liq_px.json> <out.html> <fecha YYYY-MM-DD>
#   outlet.json  = get_values RMA_Dorrego  Outlet!A3:M2000          (header row first)
#   inv.json     = get_values Control Dep. 'Inventario empresa'!A2:I3000
#   liq_mla.json = get_values LIQ mensual  'LIQ. REAL'!B4:D7000      (MLA, fecha, SKU)
#   liq_px.json  = get_values LIQ mensual  'LIQ. REAL'!C4:H7000      (fecha, SKU, cant, envío, cargo, bruto)
# Writes out.html, index.html (same folder, full document for GitHub Pages), kitdir/catalog.json (curated catalog, grows with new SKUs) and kitdir/report.json.
import json, sys, os, statistics, collections

kit, f_out, f_inv, f_mla, f_px, out_html, fecha = sys.argv[1:8]
vals = lambda p: json.load(open(p)).get('values', [])
num = lambda s: float(str(s).replace('$', '').replace('.', '').replace(',', '.').strip() or 0)

cat = json.load(open(os.path.join(kit, 'catalog.json')))      # sku -> curated product (no unidades, no foto)
fotos = json.load(open(os.path.join(kit, 'fotos.json')))
tpl = open(os.path.join(kit, 'template.txt')).read()
reales_p = os.path.join(kit, 'reales.json')
reales = json.load(open(reales_p))['units'] if os.path.exists(reales_p) else {}   # OUT-n -> ['reales/OUT-n.jpg', ...]

inv = {}
for r in vals(f_inv):
    r = r + [''] * (9 - len(r))
    if r[0].strip():
        inv[r[0].strip()] = dict(producto=r[1].strip(), negocio=r[2].strip(), categoria=r[3].strip(),
                                 subcat=r[4].strip(), proveedor=r[5].strip(), costo=num(r[8]))
mla = collections.defaultdict(collections.Counter)
for r in vals(f_mla):
    if len(r) >= 3 and r[0].startswith('MLA'): mla[r[2].strip()][r[0]] += 1
px = collections.defaultdict(list)
for r in vals(f_px):
    if len(r) >= 6:
        try:
            q = num(r[2]); b = num(r[5])
            if q > 0 and b > 0: px[r[1].strip()].append(b / q)
        except ValueError: pass

NEG = {'CHINA': 'Importados', 'DEPORTES/RECREACION': 'Deportes'}
tc = lambda s: ' '.join(w.capitalize() for w in s.split())

rows = vals(f_out)[1:]                       # skip header (sheet row 3)
units = collections.OrderedDict()
for i, r in enumerate(rows):
    r = r + [''] * (13 - len(r))
    sku = r[2].strip()
    if not sku or r[12].strip().upper() == 'VENDIDO': continue
    f = r[1].strip().split('-')
    ing = f'2026-{f[1].zfill(2)}-{f[0].zfill(2)}' if len(f) == 2 else ''
    code = f'OUT-{i + 4}'
    units.setdefault(sku, []).append({'code': code, 'ingreso': ing, 'detalle': r[8].strip(), 'fotos': reales.get(code, [])})

prods, nuevos, sin_costo = [], [], []
for sku, us in units.items():
    iv = inv.get(sku)
    if sku not in cat:
        name = iv['producto'] if iv else next((r[3] for r in rows if len(r) > 3 and r[2].strip() == sku), sku)
        p = dict(sku=sku, nombre=tc(name), negocio=NEG.get(iv['negocio'], tc(iv['negocio'])) if iv else 'Otros',
                 categoria=tc(iv['categoria']) if iv else '', subcat=tc(iv['subcat']) if iv else '',
                 proveedor=iv['proveedor'] if iv else '', mla=None, meli=None, lista=None, specs=[])
        if mla[sku]: p['mla'] = mla[sku].most_common(1)[0][0]
        if px[sku]: p['meli'] = round(statistics.median(px[sku]))
        cat[sku] = p; nuevos.append(sku)
    p = dict(cat[sku])
    if iv and iv['costo'] > 0: p['costo'] = iv['costo']          # COSTO FINAL, live
    if not p.get('costo'): sin_costo.append(sku); continue
    p['lista'] = None if p.get('meli') else round(p['costo'] / 0.6 / 100) * 100
    p['unidades'] = us; p['foto'] = fotos.get(sku) or next((u['fotos'][0] for u in us if u['fotos']), None)   # sin foto de catálogo: usa la primera foto real
    prods.append(p)

json.dump(cat, open(os.path.join(kit, 'catalog.json'), 'w'), ensure_ascii=False)
data = {'actualizado': fecha, 'productos': prods}
open(out_html, 'w').write(tpl.replace('__DATA__', json.dumps(data, ensure_ascii=False)))
# Standalone copy for GitHub Pages: full document with charset + mobile viewport (the artifact host adds these itself)
page = tpl.replace('__DATA__', json.dumps(data, ensure_ascii=False))
open(os.path.join(os.path.dirname(os.path.abspath(out_html)), 'index.html'), 'w').write(
    '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n' + page + '\n</body>\n</html>\n')
rep = dict(productos=len(prods), unidades=sum(len(p['unidades']) for p in prods), con_foto_real=sum(1 for p in prods for u in p['unidades'] if u['fotos']), nuevos=nuevos,
           sin_foto=[p['sku'] for p in prods if not p['foto']], sin_costo=sin_costo)
json.dump(rep, open(os.path.join(kit, 'report.json'), 'w'), ensure_ascii=False)
print(json.dumps(rep, ensure_ascii=False))
