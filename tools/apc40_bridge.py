#!/usr/bin/env python3
"""
Pont MIDI entre un unique APC40 physique et Sweetlight, pour simuler N "faux APC40" (un par page
du light show) - contourne une limitation de Sweetlight confirmee par son developpeur sur le forum
(15/09/2026) : le logiciel n'a pas de notion de "page active" pour le routage MIDI. Un message
(device, canal, note) donne declenche TOUS les boutons qui l'utilisent, quelle que soit la page
affichee a l'ecran - donc un seul pad physique peut activer plusieurs boutons sur plusieurs pages
en meme temps.

Principe
--------
- Les boutons de la grille de l'APC40 (notes 0-39, les "cellules" clip-launch) ne sont transmis
  qu'a la page ACTUELLEMENT active - vers un peripherique MIDI virtuel dedie a cette page.
- Le bouton "changement de page" et les faders (Control Change) NE PASSENT PAS par le pont : ils
  restent sur le port MIDI reel de l'APC40, que Sweetlight ecoute en direct (CoreMIDI autorise
  plusieurs clients sur la meme source physique - le pont et Sweetlight recoivent chacun leur
  copie sans se genver). Pas besoin de virtualiser ca : ce sont des controles qui doivent de toute
  facon marcher pareil quelle que soit la page.
- Le pont observe quand meme lui-meme les boutons de changement de page (sans les reemettre nulle
  part) pour savoir quelle page est active, et router la grille en consequence.
- Retour LED : les messages que Sweetlight envoie sur le device de la page active sont repercutes
  sur l'APC40 physique ; ceux des pages inactives sont ignores (pas de conflit visuel entre pages).
  Le retour LED des faders/changement de page vient directement de Sweetlight vers l'APC40 reel,
  sans passer par le pont non plus.

Interface web (http://localhost:8090 par defaut)
-------------------------------------------------
- Page active, derniers messages MIDI recus/envoyes (debug "sur quel device je suis").
- Ajouter/retirer des pages (cree/ferme les ports virtuels correspondants a chaud).
- Reassigner quel bouton physique (note/canal) fait basculer vers quelle page.

⚠️ Les pages et leur ORDRE doivent rester coherents avec PAGE_ORDER dans generate_page.py. Les
devices MIDI sont 0-indexes cote Sweetlight (verifie dans ~/TheLightingController/param.ini) :
page 1 = device 0, page 2 = device 1, ... Le device suivant (= nombre de pages) est l'APC40 reel,
utilise directement par Sweetlight pour les faders/changement de page (REAL_APC_DEVICE dans
generate_page.py doit valoir le meme nombre de pages).

Lancement : python3 apc40_bridge.py [nom_a_chercher_dans_les_ports] [--http-port 8090]
Par defaut cherche "APC40" dans le nom des ports MIDI disponibles.
"""
import sys
import os
import time
import json
import threading
import argparse
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Etat (liste des pages + leurs bindings note/canal) sauvegarde hors du repo, pour survivre a un
# redemarrage du pont sans se retrouver commite par erreur dans git.
CONFIG_PATH = os.path.expanduser("~/.apc40_bridge_state.json")

try:
    import rtmidi
except ImportError:
    print("Il manque python-rtmidi : pip3 install python-rtmidi")
    sys.exit(1)

DEFAULT_PAGES = ["DJ LIVE", "COULEUR", "GOBO", "MANUEL", "STROBE", "FX", "MOUVEMENT"]
GRID_NOTE_MIN, GRID_NOTE_MAX = 0, 39   # notes des boutons de grille (5 lignes x 8 colonnes)
DEFAULT_SWITCH_NOTE = 52               # doit matcher buttonstabN_midi_note par defaut dans generate_page.py

lock = threading.Lock()


class State:
    """Etat partage entre le thread MIDI et le serveur web (proteger par `lock`)."""
    def __init__(self):
        self.pages = []            # [{"name":..., "device":int, "note":int, "channel":int,
                                    #   "to_sw":MidiOut, "from_sw":MidiIn}]
        self.current_page = 0      # index dans self.pages
        self.events = deque(maxlen=200)   # log pour l'UI web
        self.real_in = None
        self.real_out = None
        self.next_device = 0   # 0-indexe cote Sweetlight (page1=device0, page2=device1...)
        self.apc_connected = False   # APC40 physique detecte et ouvert (cf apc_watcher)
        self.apc_port_name = None

    def log(self, direction, dev_name, msg):
        note = msg[1] if len(msg) > 1 else None
        vel = msg[2] if len(msg) > 2 else None
        status = msg[0] & 0xF0
        chan = (msg[0] & 0x0F) + 1
        kind = {0x90: "note_on", 0x80: "note_off", 0xB0: "cc"}.get(status, "raw(%02x)" % msg[0])
        self.events.appendleft({
            "t": time.strftime("%H:%M:%S"), "dir": direction, "device": dev_name,
            "kind": kind, "channel": chan, "note": note, "value": vel,
        })


ST = State()


def find_port(ports, needle):
    for i, p in enumerate(ports):
        if needle.lower() in p.lower():
            return i
    return None


def make_led_cb(page_index):
    def cb(event, _data=None):
        msg, _dt = event
        with lock:
            name = ST.pages[page_index]["name"] if page_index is not None else "Global"
            ST.log("sweetlight->pont", name, msg)
            if page_index is not None and len(msg) > 1:
                # Memorise le dernier etat LED de ce pad pour cette page, pour pouvoir tout
                # reafficher d'un coup quand on rebascule sur cette page (cf on_physical).
                ST.pages[page_index]["led_cache"][msg[1]] = list(msg)
            if (page_index is None or page_index == ST.current_page) and ST.real_out is not None:
                ST.real_out.send_message(msg)
    return cb


def save_config():
    try:
        data = {"pages": [{"name": p["name"], "note": p["note"], "channel": p["channel"]} for p in ST.pages]}
        with open(CONFIG_PATH, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2)
    except Exception as e:
        print("Impossible de sauvegarder l'etat (%s) :" % CONFIG_PATH, e)


def load_config():
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding='utf-8') as fh:
                return json.load(fh).get("pages")
        except Exception as e:
            print("Impossible de charger l'etat sauvegarde (%s) :" % CONFIG_PATH, e)
    return None


def add_page(name, note=DEFAULT_SWITCH_NOTE, channel=None, _save=True):
    with lock:
        idx = len(ST.pages)
        device = ST.next_device        # 0-indexe (device MIDI reel cote Sweetlight)
        ST.next_device += 1
        page_num = device + 1          # 1-indexe, juste pour le nom du port (compat avec l'existant)
        if channel is None:
            channel = page_num         # canal MIDI du Clip Stop de cette page - independant du device
        to_sw = rtmidi.MidiOut()
        to_sw.open_virtual_port("SweetLight-P%d-%s" % (page_num, name))
        from_sw = rtmidi.MidiIn()
        from_sw.open_virtual_port("SweetLight-P%d-%s-Out" % (page_num, name))
        from_sw.ignore_types(sysex=False, timing=False, active_sense=False)
        from_sw.set_callback(make_led_cb(idx))
        ST.pages.append({"name": name, "device": device, "note": note, "channel": channel,
                          "to_sw": to_sw, "from_sw": from_sw, "led_cache": {}})
    if _save: save_config()
    return idx


def remove_page(idx):
    with lock:
        if not (0 <= idx < len(ST.pages)):
            return False
        p = ST.pages.pop(idx)
        p["to_sw"].close_port()
        p["from_sw"].close_port()
        if ST.current_page >= len(ST.pages):
            ST.current_page = max(0, len(ST.pages) - 1)
    save_config()
    return True


def on_physical(event, _data=None):
    msg, _dt = event
    if not msg:
        return
    with lock:
        status = msg[0] & 0xF0
        note = msg[1] if len(msg) > 1 else None
        chan = (msg[0] & 0x0F) + 1
        matched_switch = None
        if status in (0x90, 0x80):
            for i, p in enumerate(ST.pages):
                if p["note"] == note and p["channel"] == chan:
                    matched_switch = i
                    break
        if matched_switch is not None:
            # Changement de page : deja recu directement par Sweetlight depuis l'APC40 reel (pas
            # besoin de reemettre) - le pont note juste quelle page devient active, et reaffiche
            # d'un coup l'etat LED memorise de chaque pad de la grille pour cette page (sinon les
            # pads restent figes sur l'etat de la page precedente tant que Sweetlight ne retouche
            # pas chaque bouton individuellement).
            ST.current_page = matched_switch
            ST.log("apc40->observe", "Global (reel)", msg)
            if ST.real_out is not None:
                cache = ST.pages[matched_switch]["led_cache"]
                for n in range(GRID_NOTE_MIN, GRID_NOTE_MAX + 1):
                    ST.real_out.send_message(cache.get(n, [0x90, n, 0]))
        elif status in (0x90, 0x80) and note is not None and GRID_NOTE_MIN <= note <= GRID_NOTE_MAX:
            name = ST.pages[ST.current_page]["name"] if ST.pages else "?"
            ST.log("apc40->page", name, msg)
            if ST.pages:
                ST.pages[ST.current_page]["to_sw"].send_message(msg)
        else:
            # Faders (CC) et tout le reste : deja recus directement par Sweetlight depuis l'APC40
            # reel, rien a faire.
            ST.log("apc40->observe", "Global (reel)", msg)


def apc_watcher(needle, poll_interval=4):
    """Tourne en permanence dans un thread a part : cherche/ouvre l'APC40 physique, et redetecte
    une deconnexion/reconnexion (rtmidi ne notifie pas les branchements/debranchements - on
    reinterroge periodiquement la liste des ports). Ne fait jamais sys.exit() : le serveur web doit
    rester joignable meme si l'APC40 n'est jamais trouve (LaunchAgent + interface de supervision)."""
    first = True
    while True:
        probe_in, probe_out = rtmidi.MidiIn(), rtmidi.MidiOut()
        in_ports, out_ports = probe_in.get_ports(), probe_out.get_ports()
        if first:
            print("Entrees MIDI disponibles :", in_ports)
            print("Sorties MIDI disponibles :", out_ports)
            first = False
        ii, oi = find_port(in_ports, needle), find_port(out_ports, needle)
        with lock:
            was_connected = ST.apc_connected
        if ii is not None and oi is not None:
            if not was_connected:
                try:
                    real_in = rtmidi.MidiIn()
                    real_in.open_port(ii)
                    real_in.ignore_types(sysex=False, timing=False, active_sense=False)
                    real_in.set_callback(on_physical)
                    real_out = rtmidi.MidiOut()
                    real_out.open_port(oi)
                    with lock:
                        ST.real_in, ST.real_out = real_in, real_out
                        ST.apc_connected = True
                        ST.apc_port_name = in_ports[ii]
                    print("APC40 physique trouve : IN[%d]=%s  OUT[%d]=%s" % (ii, in_ports[ii], oi, out_ports[oi]))
                except Exception as e:
                    print("Erreur a l'ouverture de l'APC40 :", e)
        else:
            if was_connected:
                print("APC40 introuvable (debranche ?) - nouvelle tentative en boucle.")
                with lock:
                    old_in, old_out = ST.real_in, ST.real_out
                    ST.real_in = ST.real_out = None
                    ST.apc_connected = False
                    ST.apc_port_name = None
                for h in (old_in, old_out):
                    try:
                        if h: h.close_port()
                    except Exception:
                        pass
        time.sleep(poll_interval)


# ===================== Serveur web =====================
HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>APC40 Bridge</title>
<style>
body{font-family:-apple-system,sans-serif;background:#111;color:#eee;margin:0;padding:16px}
h1{font-size:18px}
.row{display:flex;gap:16px;flex-wrap:wrap}
.box{background:#1c1c1c;border-radius:8px;padding:12px;flex:1;min-width:280px}
table{width:100%;border-collapse:collapse;font-size:12px}
td,th{padding:3px 6px;text-align:left;border-bottom:1px solid #333}
.active{background:#264;font-weight:bold}
input{width:60px;background:#222;color:#eee;border:1px solid #444;border-radius:4px;padding:2px 4px}
button{background:#2a6;color:#fff;border:none;border-radius:4px;padding:4px 10px;cursor:pointer;margin:2px}
button.danger{background:#a33}
.log{max-height:400px;overflow:auto;font-family:monospace;font-size:11px}
.log div.in{color:#7c7}
.log div.out{color:#79f}
#apcstatus{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;margin-left:10px}
#apcstatus.ok{background:#264;color:#7f7}
#apcstatus.ko{background:#422;color:#f77}
</style></head><body>
<h1>APC40 Bridge - SweetLight <span id="apcstatus">...</span></h1>
<div class="row">
<div class="box">
<h2>Pages</h2>
<table id="pages"><thead><tr><th>#</th><th>Page</th><th>Device</th><th>Note</th><th>Canal</th><th></th></tr></thead><tbody></tbody></table>
<div style="margin-top:8px">
<input id="newname" placeholder="Nom page"> <button onclick="addPage()">+ Ajouter</button>
</div>
</div>
<div class="box">
<h2>Journal MIDI (derniers messages)</h2>
<div class="log" id="log"></div>
</div>
</div>
<script>
async function refresh(){
  const r = await fetch('/state'); const s = await r.json();
  const st = document.getElementById('apcstatus');
  if(s.apc_connected){ st.textContent = 'APC40 connecte (' + s.apc_port_name + ')'; st.className='ok'; }
  else { st.textContent = 'APC40 non detecte - branche-le et attends quelques secondes'; st.className='ko'; }
  const tb = document.querySelector('#pages tbody'); tb.innerHTML='';
  s.pages.forEach((p,i)=>{
    const tr = document.createElement('tr');
    if(i===s.current_page) tr.className='active';
    tr.innerHTML = `<td>${i+1}</td><td>${p.name}</td><td>${p.device}</td>
      <td><input value="${p.note}" onchange="rebind(${i},this.value,null)"></td>
      <td><input value="${p.channel}" onchange="rebind(${i},null,this.value)"></td>
      <td><button class="danger" onclick="removePage(${i})">Retirer</button></td>`;
    tb.appendChild(tr);
  });
  const log = document.getElementById('log'); log.innerHTML='';
  s.events.forEach(e=>{
    const d = document.createElement('div');
    d.className = e.dir.startsWith('apc40') ? 'in' : 'out';
    d.textContent = `${e.t} [${e.device}] ${e.dir} ${e.kind} ch${e.channel} note=${e.note} val=${e.value}`;
    log.appendChild(d);
  });
}
async function addPage(){
  const name = document.getElementById('newname').value.trim();
  if(!name) return;
  await fetch('/pages/add', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name})});
  document.getElementById('newname').value=''; refresh();
}
async function removePage(i){
  await fetch('/pages/remove', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({index:i})});
  refresh();
}
async function rebind(i, note, channel){
  const body = {index:i};
  if(note!==null) body.note = parseInt(note);
  if(channel!==null) body.channel = parseInt(channel);
  await fetch('/pages/bind', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  refresh();
}
setInterval(refresh, 500); refresh();
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # silence les logs http par defaut

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            body = HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == '/state':
            with lock:
                self._json({
                    "current_page": ST.current_page,
                    "pages": [{"name": p["name"], "device": p["device"], "note": p["note"],
                               "channel": p["channel"]} for p in ST.pages],
                    "events": list(ST.events),
                    "apc_connected": ST.apc_connected,
                    "apc_port_name": ST.apc_port_name,
                })
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        try:
            data = json.loads(self.rfile.read(length) or b'{}')
        except Exception:
            data = {}
        if self.path == '/pages/add':
            idx = add_page(data.get("name", "PAGE"))
            self._json({"ok": True, "index": idx})
        elif self.path == '/pages/remove':
            ok = remove_page(int(data.get("index", -1)))
            self._json({"ok": ok})
        elif self.path == '/pages/bind':
            with lock:
                i = int(data.get("index", -1))
                ok = 0 <= i < len(ST.pages)
                if ok:
                    if "note" in data: ST.pages[i]["note"] = int(data["note"])
                    if "channel" in data: ST.pages[i]["channel"] = int(data["channel"])
            if ok: save_config()
            self._json({"ok": ok}, 200 if ok else 400)
        else:
            self._json({"error": "not found"}, 404)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("needle", nargs="?", default="APC40")
    ap.add_argument("--http-port", type=int, default=8090)
    args = ap.parse_args()

    saved = load_config()
    if saved:
        print("Etat precedent charge depuis %s (%d pages)." % (CONFIG_PATH, len(saved)))
        for p in saved:
            add_page(p["name"], note=p.get("note", DEFAULT_SWITCH_NOTE), channel=p.get("channel"), _save=False)
    else:
        for i, name in enumerate(DEFAULT_PAGES, start=1):
            add_page(name, note=DEFAULT_SWITCH_NOTE, channel=i, _save=False)
        save_config()

    # Le serveur web demarre toujours, meme si l'APC40 n'est pas (encore) branche : c'est le seul
    # moyen de superviser/diagnostiquer l'etat de connexion depuis l'interface.
    server = ThreadingHTTPServer(('0.0.0.0', args.http_port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print("Interface web : http://localhost:%d" % args.http_port)

    # Recherche/(re)connexion de l'APC40 en tache de fond, en boucle - jamais de sys.exit() ici :
    # le pont doit rester joignable (et pret a se brancher tout seul) meme sans l'APC40.
    threading.Thread(target=apc_watcher, args=(args.needle,), daemon=True).start()

    print("Pont actif (page active : %s). Ctrl+C pour arreter." % ST.pages[0]["name"])
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Arret.")


if __name__ == "__main__":
    main()
