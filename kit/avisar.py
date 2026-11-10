# Avisa por un issue de GitHub (llega por mail a la dueña del repo) cuando hay productos sin foto de catálogo.
# Lee kit/report.json (lo genera build.py) y recuerda en kit/avisos.json a qué SKUs ya se avisó.
import json, os, subprocess, datetime
KIT = os.path.dirname(os.path.abspath(__file__))
rep = json.load(open(os.path.join(KIT, 'report.json')))
cat = json.load(open(os.path.join(KIT, 'catalog.json')))
av_p = os.path.join(KIT, 'avisos.json')
avisados = set(json.load(open(av_p))) if os.path.exists(av_p) else set()
sin = set(rep.get('sin_foto', []))
nuevos = sorted(sin - avisados)
if nuevos:
    lineas = '\n'.join(f"- **{cat.get(s, {}).get('nombre', s)}** (SKU {s})" for s in nuevos)
    cuerpo = ("Estos productos del Outlet se publicaron sin foto de catálogo y se ven con el recuadro gris en la página:\n\n"
              + lineas + "\n\nPasale las fotos a Claude en la conversación del Outlet y las carga.\n\nhttps://noeromero14-gif.github.io/outletdeposito/")
    hoy = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-3))).strftime('%d/%m %H:%M')
    subprocess.run(['gh', 'issue', 'create', '--title', f'Faltan fotos de catálogo ({len(nuevos)}) — {hoy}', '--body', cuerpo], check=True)
json.dump(sorted(sin), open(av_p, 'w'), ensure_ascii=False)   # se olvida de los que ya tienen foto, por si vuelven a faltar
print('Sin foto:', sorted(sin), '| avisados ahora:', nuevos)
