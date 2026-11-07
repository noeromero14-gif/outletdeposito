# Actualiza la página del Outlet desde el Apps Script de la planilla RMA_Dorrego.
# Lo corre GitHub Actions (.github/workflows/actualizar.yml). Uso local: python3 kit/actualizar.py
import json, os, sys, subprocess, urllib.request, datetime

API = os.environ.get('OUTLET_API', 'https://script.google.com/macros/s/AKfycbzD_LpLNRPwdjtSiUpH85K12ZtoXvieToTr_YtS4KYLJQ--efCcOtHLnr5mJ-aFPPGd4w/exec')
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(RAIZ, 'kit')
TMP = os.path.join(RAIZ, '.tmp')
os.makedirs(TMP, exist_ok=True)

def get(q):
    with urllib.request.urlopen(API + q, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))

def guardar(nombre, valores):
    p = os.path.join(TMP, nombre)
    json.dump({'values': valores}, open(p, 'w'), ensure_ascii=False)
    return p

d = get('?datos=1')
if not d.get('outlet') or len(d['outlet']) < 2:
    sys.exit('La hoja Outlet vino vacía: no publico nada.')

f_out = guardar('outlet.json', d['outlet'])
f_inv = guardar('inv.json', d['inv'])
f_mla = guardar('liq_mla.json', [r[0:3] for r in d['liq']])   # B:D  (MLA, fecha, SKU)
f_px = guardar('liq_px.json', [r[1:7] for r in d['liq']])     # C:H  (fecha, SKU, cant, envío, cargo, bruto)

# Fotos reales nuevas o cambiadas
man_p = os.path.join(KIT, 'reales.json')
seen = json.load(open(man_p)).get('seen', {}) if os.path.exists(man_p) else {}
pend = [f for f in d.get('fotos', []) if seen.get(f['id']) != f['modificado']]
if pend:
    mod = {f['id']: f['modificado'] for f in pend}
    f_mod = os.path.join(TMP, 'mod.json'); json.dump(mod, open(f_mod, 'w'))
    archivos = []
    for f in pend:
        foto = get('?foto=' + f['id'])
        if not foto.get('ok'): print('Foto omitida', f['nombre'], foto); continue
        p = os.path.join(TMP, 'foto_' + f['id'] + '.json'); json.dump(foto, open(p, 'w')); archivos.append(p)
    if archivos:
        subprocess.run([sys.executable, '-I', os.path.join(KIT, 'reales.py'), KIT, RAIZ, f_mod] + archivos, check=True)

AR = datetime.timezone(datetime.timedelta(hours=-3))   # Argentina, UTC-3 sin horario de verano
hoy = datetime.datetime.now(AR).strftime('%Y-%m-%d')
subprocess.run([sys.executable, '-I', os.path.join(KIT, 'build.py'), KIT, f_out, f_inv, f_mla, f_px,
                os.path.join(TMP, 'outlet-venta.html'), hoy], check=True)
os.replace(os.path.join(TMP, 'index.html'), os.path.join(RAIZ, 'index.html'))
print('Página generada.')
