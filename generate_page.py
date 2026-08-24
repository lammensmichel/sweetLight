#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere les scenes .scex, les generateurs .gpj et la/les page(s) live.ini pour Sweetlight.
Idempotent. Usage : python3 generate_page.py [dossier_du_show]"""
import os, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "/Users/mac-m3-michel/workspace/sweetLight/v1"
SCENES = os.path.join(BASE, "scenes")
LIVE = os.path.join(BASE, "Live", "live.ini")
OUT_GEN = os.path.join(BASE, "Editor", "Generator", "projects")


if __name__ == "__main__":
    pass
