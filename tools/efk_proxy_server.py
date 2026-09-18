#!/usr/bin/env python3
"""
Serveur proxy pour le dongle Sweetlight D512S (VID:PID 1069:1044, fabricant "EFK") - tourne sur la
machine ou le vrai dongle est branche (typiquement le Pi, a cote du serveur VirtualHere existant -
independant, meme dongle physique partage differemment).

Contexte : VirtualHere (client officiel) n'est plus installable sur les Mac trop vieux (macOS < 12).
Sweetlight parle au dongle via une petite lib maison (efk_usb.dylib, cf tools/efk_usb_shim.c) qui
utilise l'USB generique (pas de driver systeme, canal "vendor specific"). Ce serveur reexpose les
memes operations (ouvrir le device, transferts bulk/interrupt/control) via un protocole reseau
simple, pour qu'une dylib de remplacement sur le vieux Mac puisse piloter le VRAI dongle a distance.

Protocole : une ligne JSON par requete sur un socket TCP, une ligne JSON par reponse (meme connexion,
requete/reponse strictement sequentielles - un seul client a la fois, un seul dongle a partager).
Requetes :
  {"op": "find"}                                          -> {"ok": true, "vid":.., "pid":..}
  {"op": "open"}                                           -> {"ok": true} ou {"ok": false, "err":..}
  {"op": "claim", "interface": N}                          -> {"ok": true}
  {"op": "bulk_write", "ep": N, "data": "<hex>"}           -> {"ok": true, "sent": N}
  {"op": "bulk_read", "ep": N, "length": N, "timeout": ms} -> {"ok": true, "data": "<hex>"}
  {"op": "interrupt_read", "ep": N, "length": N, "timeout": ms} -> idem bulk_read
  {"op": "control", "bmRequestType":N, "bRequest":N, "wValue":N, "wIndex":N, "data":"<hex>"} (OUT)
  {"op": "control_in", "bmRequestType":N, "bRequest":N, "wValue":N, "wIndex":N, "length":N} (IN)
  {"op": "close"}                                          -> {"ok": true}

Lancement : python3 efk_proxy_server.py [--port 9091]
"""
import sys
import json
import socket
import argparse
import binascii

try:
    import usb.core
    import usb.util
except ImportError:
    print("Il manque pyusb : sudo pip3 install pyusb")
    sys.exit(1)

VID, PID = 0x1069, 0x1044


class Session:
    def __init__(self):
        self.dev = None

    def find(self):
        self.dev = usb.core.find(idVendor=VID, idProduct=PID)
        if self.dev is None:
            return {"ok": False, "err": "device not found"}
        return {"ok": True, "vid": VID, "pid": PID}

    def open(self):
        if self.dev is None:
            r = self.find()
            if not r["ok"]:
                return r
        try:
            # Detache un driver noyau eventuel (rare pour un device vendor-specific, mais au cas ou).
            if self.dev.is_kernel_driver_active(0):
                self.dev.detach_kernel_driver(0)
        except Exception:
            pass
        try:
            self.dev.set_configuration()
        except usb.core.USBError as e:
            return {"ok": False, "err": "set_configuration: %s" % e}
        return {"ok": True}

    def claim(self, interface):
        try:
            usb.util.claim_interface(self.dev, interface)
        except Exception as e:
            return {"ok": False, "err": str(e)}
        return {"ok": True}

    def bulk_write(self, ep, data_hex):
        data = binascii.unhexlify(data_hex)
        try:
            n = self.dev.write(ep, data, timeout=2000)
        except usb.core.USBError as e:
            return {"ok": False, "err": str(e)}
        return {"ok": True, "sent": n}

    def bulk_read(self, ep, length, timeout):
        try:
            data = self.dev.read(ep, length, timeout=timeout)
        except usb.core.USBError as e:
            return {"ok": False, "err": str(e)}
        return {"ok": True, "data": binascii.hexlify(bytes(data)).decode()}

    def control_out(self, bmRequestType, bRequest, wValue, wIndex, data_hex):
        data = binascii.unhexlify(data_hex) if data_hex else b""
        try:
            n = self.dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data, timeout=2000)
        except usb.core.USBError as e:
            return {"ok": False, "err": str(e)}
        return {"ok": True, "sent": n}

    def control_in(self, bmRequestType, bRequest, wValue, wIndex, length):
        try:
            data = self.dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, length, timeout=2000)
        except usb.core.USBError as e:
            return {"ok": False, "err": str(e)}
        return {"ok": True, "data": binascii.hexlify(bytes(data)).decode()}

    def close(self):
        try:
            usb.util.dispose_resources(self.dev)
        except Exception:
            pass
        self.dev = None
        return {"ok": True}


def handle(conn, sess):
    buf = b""
    while True:
        chunk = conn.recv(65536)
        if not chunk:
            return
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            if not line.strip():
                continue
            try:
                # decode() explicite : json.loads() n'accepte des bytes qu'a partir de Python 3.6,
                # le Pi tourne encore en 3.5.
                req = json.loads(line.decode('utf-8'))
            except Exception as e:
                conn.sendall((json.dumps({"ok": False, "err": "bad json: %s" % e}) + "\n").encode())
                continue
            op = req.get("op")
            try:
                if op == "find":
                    resp = sess.find()
                elif op == "open":
                    resp = sess.open()
                elif op == "claim":
                    resp = sess.claim(req["interface"])
                elif op == "bulk_write":
                    resp = sess.bulk_write(req["ep"], req["data"])
                elif op == "bulk_read":
                    resp = sess.bulk_read(req["ep"], req["length"], req.get("timeout", 2000))
                elif op == "interrupt_read":
                    resp = sess.bulk_read(req["ep"], req["length"], req.get("timeout", 2000))
                elif op == "control":
                    resp = sess.control_out(req["bmRequestType"], req["bRequest"], req["wValue"], req["wIndex"], req.get("data", ""))
                elif op == "control_in":
                    resp = sess.control_in(req["bmRequestType"], req["bRequest"], req["wValue"], req["wIndex"], req["length"])
                elif op == "close":
                    resp = sess.close()
                else:
                    resp = {"ok": False, "err": "unknown op %r" % op}
            except Exception as e:
                resp = {"ok": False, "err": "exception: %s" % e}
            conn.sendall((json.dumps(resp) + "\n").encode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9091)
    args = ap.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", args.port))
    srv.listen(1)
    print("Serveur proxy D512S sur le port %d (VID:PID %04x:%04x)" % (args.port, VID, PID))
    while True:
        conn, addr = srv.accept()
        print("Connexion de", addr)
        sess = Session()
        try:
            handle(conn, sess)
        except Exception as e:
            print("Erreur session:", e)
        finally:
            sess.close()
            conn.close()
            print("Deconnecte", addr)


if __name__ == "__main__":
    main()
