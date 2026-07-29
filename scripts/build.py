#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Narrative Porti — build dei prodotti (index.html + PDF) dai dati in data/."""
import json, re, datetime, pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
OUT  = BASE / "output"
OUT.mkdir(exist_ok=True)

VERSIONE = (BASE / "VERSION").read_text().strip()
OGGI = datetime.date.today().strftime("%d.%m.%Y")
REPO = "github.com/wavyforseafarers/Narrative-Porti"

# ---------------------------------------------------------------- dati
def carica(cartella):
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((BASE/"data"/cartella).glob("*.json"))]

PORTI = carica("porti")
ROTTE = carica("rotte")

def ddm_to_dec(txt):
    m = re.match(r"(\d+)°\s*([\d.]+)'?\s*([NSEW])", txt.strip())
    v = int(m.group(1)) + float(m.group(2))/60.0
    return -v if m.group(3) in "SW" else v

import math

def dist_rl(a, b):
    """Distanza lossodromica in NM fra due waypoint."""
    la1, la2 = math.radians(a["lat"]), math.radians(b["lat"])
    dlat = la2 - la1
    dlon = math.radians(b["lon"] - a["lon"])
    if abs(dlon) > math.pi:
        dlon -= math.copysign(2*math.pi, dlon)
    dpsi = math.log(math.tan(math.pi/4 + la2/2) / math.tan(math.pi/4 + la1/2))
    q = dlat/dpsi if abs(dpsi) > 1e-12 else math.cos(la1)
    return math.degrees(math.hypot(dlat, q*dlon)) * 60.0

for r in ROTTE:
    for w in r["waypoints"]:
        w["lat"] = ddm_to_dec(w["lat_txt"]); w["lon"] = ddm_to_dec(w["lon_txt"])
    # distanza cumulata: usa i valori di bordo se presenti, altrimenti li calcola
    if r.get("distanza_nm") is None:
        tot = sum(dist_rl(x, y) for x, y in zip(r["waypoints"][:-1], r["waypoints"][1:]))
        r["distanza_nm"] = round(tot, 2)
        r["distanza_calcolata"] = True
    r.setdefault("colonne", ["n","nome","raggio_nm","lat_txt","lon_txt","bww","dist_enr","dist","sail"])

def porto_di(rotta):
    pid = rotta.get("porto_arrivo")
    for p_ in PORTI:
        if p_["id"] == pid: return p_
    return PORTI[0]

# ogni rotta è abbinata al proprio porto di arrivo, in ordine di inserimento
COPPIE = sorted(((porto_di(r), r) for r in ROTTE),
                key=lambda c: (c[0].get("aggiornato",""), c[0]["nome"]))

def data_breve(iso):
    """2026-07-22 -> 22.07.26"""
    if not iso: return ""
    a, m, g = iso.split("-")
    return f"{g}.{m}.{a[2:]}"

# ---------------------------------------------------------------- HTML
def build_html():
    tpl = (BASE/"scripts"/"template_index.html").read_text(encoding="utf-8")
    dati = {"meta": {"versione": VERSIONE, "generato": OGGI, "repo": REPO},
            "porti": PORTI, "rotte": ROTTE}
    html = tpl.replace("__DATA__", json.dumps(dati, ensure_ascii=False))
    (OUT/"index.html").write_text(html, encoding="utf-8")
    print("HTML  ->", OUT/"index.html")

# ---------------------------------------------------------------- cartine
ACQUA="#CFE2E8"; TERRA="#EBDFB6"; COSTA="#8A7F5C"; NAVY="#0E3A4C"; MAGENTA="#B0207A"; SEC="#5A6B78"

PROPORZIONI = {}

def chartlet(rotta, path, estensione, passo, etichette, titolo, figsize,
             marca_note=True, scava=None, fs=5.0, fs_tit=5.8, fs_tick=4.2):
    import numpy as np, matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    from global_land_mask import globe

    lat0,lat1,lon0,lon1 = estensione
    lats = np.arange(lat0, lat1, passo); lons = np.arange(lon0, lon1, passo)
    LON, LAT = np.meshgrid(lons, lats)
    land = globe.is_land(LAT, LON)

    # La maschera terra/acqua (~1 km) non risolve le canalette strette:
    # dove richiesto, scava un corridoio d'acqua lungo la rotta (schema indicativo).
    if scava:
        coslat = np.cos(np.radians((lat0+lat1)/2))
        pts = [(w["lon"]*coslat, w["lat"]) for w in rotta["waypoints"] if w["n"] >= scava["da_wp"]]
        X, Y = LON*coslat, LAT
        r2 = scava["raggio_deg"]**2
        for (x1,y1),(x2,y2) in zip(pts[:-1], pts[1:]):
            dx,dy = x2-x1, y2-y1
            t = np.clip(((X-x1)*dx+(Y-y1)*dy)/(dx*dx+dy*dy), 0, 1)
            d2 = (X-(x1+t*dx))**2 + (Y-(y1+t*dy))**2
            land &= d2 > r2

    fig, ax = plt.subplots(figsize=figsize, dpi=300)
    fig.patch.set_facecolor("#F6F0E0")
    ax.set_facecolor(ACQUA)
    ax.contourf(LON, LAT, land, levels=[0.5,1.5], colors=[TERRA], antialiased=True)
    ax.contour (LON, LAT, land, levels=[0.5], colors=[COSTA], linewidths=0.5)

    xs=[w["lon"] for w in rotta["waypoints"]]; ys=[w["lat"] for w in rotta["waypoints"]]
    ax.plot(xs, ys, color="white", lw=3.2, alpha=.75, solid_capstyle="round")
    ax.plot(xs, ys, color=NAVY, lw=1.5, solid_capstyle="round")
    for w in rotta["waypoints"]:
        if not (lon0<=w["lon"]<=lon1 and lat0<=w["lat"]<=lat1): continue
        operativo = marca_note and bool(w.get("nota"))
        ax.plot(w["lon"], w["lat"], "o", ms=4.5 if operativo else 3,
                mfc=MAGENTA if operativo else "#FDFAF1", mec=MAGENTA if operativo else NAVY, mew=1.1)
    for n, testo, dx, dy, ha in etichette:
        w = next(x for x in rotta["waypoints"] if x["n"]==n)
        ax.annotate(testo, (w["lon"], w["lat"]), xytext=(dx,dy), textcoords="offset points",
                    fontsize=fs, color="#1B2733", ha=ha, family="DejaVu Sans",
                    path_effects=[pe.withStroke(linewidth=1.8, foreground="#F6F0E0")])

    ax.set_xlim(lon0,lon1); ax.set_ylim(lat0,lat1)
    ax.set_aspect(1/np.cos(np.radians((lat0+lat1)/2)))
    ax.tick_params(labelsize=fs_tick, colors=SEC, length=2)
    ax.grid(color="#1B2733", alpha=.10, lw=.5)
    for s in ax.spines.values(): s.set_color(SEC); s.set_linewidth(.7)
    ax.set_title(titolo, fontsize=fs_tit, family="DejaVu Sans", color=NAVY, loc="left", pad=3)
    fig.text(.995,.004,"Schema indicativo — not for navigation", ha="right",
             fontsize=fs_tick, color=SEC, style="italic")
    fig.tight_layout(pad=.35)
    # ritaglio al contenuto: le rotte molto sviluppate in latitudine lascerebbero
    # altrimenti ampie fasce vuote ai lati dell'inquadratura.
    fig.savefig(path, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    # Le rotte molto sviluppate in latitudine lasciano ampie fasce vuote ai lati
    # dell'inquadratura: ritaglio ai contenuti effettivi (mappa, etichette, assi).
    from PIL import Image as _I, ImageChops as _IC
    import numpy as _np
    with _I.open(path) as _im:
        _rgb=_im.convert("RGB")
        _sfondo=_I.new("RGB", _rgb.size, tuple(_np.array(_rgb)[0,0]))
        _bbox=_IC.difference(_rgb, _sfondo).convert("L").point(lambda v: 255 if v>10 else 0).getbbox()
        if _bbox:
            m=8
            _bbox=(max(0,_bbox[0]-m), max(0,_bbox[1]-m),
                   min(_rgb.size[0], _bbox[2]+m), min(_rgb.size[1], _bbox[3]+m))
            _rgb=_rgb.crop(_bbox); _rgb.save(path)
        PROPORZIONI[pathlib.Path(path).stem] = _rgb.size[1]/_rgb.size[0]
    print("CARTA ->", path)

def build_cartine():
    """Una coppia di cartine per ogni rotta: quadro generale + approccio finale."""
    for porto, r in COPPIE:
        cfg = CARTINE[r["id"]]
        chartlet(r, OUT/f"_{r['id']}_overview.png", cfg["overview"]["estensione"],
                 cfg["overview"]["passo"], cfg["overview"]["etichette"],
                 cfg["overview"]["titolo"], (2.44, 3.14))
        chartlet(r, OUT/f"_{r['id']}_approccio.png", cfg["approccio"]["estensione"],
                 cfg["approccio"]["passo"], cfg["approccio"]["etichette"],
                 cfg["approccio"]["titolo"], (3.15, 2.20),
                 scava=cfg["approccio"].get("scava"))

# Inquadrature e etichette delle cartine, una voce per rotta.
CARTINE = {
  "bergen_haugesund": {
    "overview": {
      "estensione": (59.18, 60.88, 3.90, 5.58), "passo": 0.004,
      "titolo": "Rotta Bergen → Haugesund — 132.61 NM · 25 WP",
      "etichette": [(1,"BERGEN — PIER",6,4,"left"), (4,"Askøybrua (62 m)",6,-9,"left"),
                    (13,"POFF FEDJE",7,3,"left"), (14,"TSS OUT",-6,5,"right"),
                    (16,"12 NM OUT",-7,-3,"right"), (17,"12 NM IN",-8,0,"right"),
                    (19,"PORT LIMIT",-8,4,"right"), (25,"HAUGESUND",8,-2,"left")]},
    "approccio": {
      "estensione": (59.345, 59.555, 4.86, 5.34), "passo": 0.0008,
      "titolo": "Approccio finale — sequenza operativa",
      "scava": {"da_wp": 21, "raggio_deg": 0.0030},
      "etichette": [(19,"WP19 · PORT LIMIT",6,6,"left"), (20,"WP20 · GRUNNANE 11→7 kn",6,8,"left"),
                    (21,"WP21 · SBE / RED MANNING",-9,11,"right"), (22,"WP22 · Kråkeflua 8 kn",-9,-13,"right"),
                    (23,"WP23 · GALVEN",-11,-2,"right"), (24,"WP24 · GALTEN — acc. SX ROT>30°/min",9,-9,"left"),
                    (25,"GARPESKJÆRSKAIEN",9,6,"left")]}},
  "alesund_stavanger": {
    "overview": {
      "estensione": (58.75, 62.72, 2.20, 7.40), "passo": 0.008,
      "titolo": "Rotta Ålesund → Stavanger — 25 WP in mare aperto",
      "etichette": [(1,"ÅLESUND",7,3,"left"), (8,"PILOT OFF — Breisundet",-7,-9,"right"),
                    (12,"12 NM OUT",-7,4,"right"), (13,"TSS IN",-7,-9,"right"),
                    (14,"BEGLA",-8,-2,"right"), (15,"OUTSIDE TSS",-8,3,"right"),
                    (17,"UTSIRA",-8,-8,"right"), (19,"SKUDEFJORD PLT",8,2,"left"),
                    (28,"STAVANGER",8,-7,"left")]},
    "approccio": {
      "estensione": (58.955, 59.135, 5.36, 5.79), "passo": 0.0007,
      "titolo": "Approccio finale — sequenza operativa",
      "scava": {"da_wp": 23, "raggio_deg": 0.0026},
      "etichette": [(19,"WP19 · SKUDEFJORD — pilota",7,5,"left"), (21,"WP21 · TERNEBOANE",7,4,"left"),
                    (22,"WP22 · TUNGE",7,3,"left"),
                    (23,"WP23 · SBE / thrusters / 10 kn",-9,9,"right"),
                    (25,"WP25 · PORT LIMIT — solo MGO",-9,-11,"right"),
                    (27,"WP27 · turning basin",-10,5,"right"),
                    (28,"STRANDKAIEN",9,-7,"left")]}},
}

# ---------------------------------------------------------------- PDF
def build_pdf():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                    Spacer, Table, TableStyle, Image, PageBreak,
                                    NextPageTemplate, KeepTogether)
    from reportlab.platypus.tableofcontents import TableOfContents

    C_NAVY=colors.HexColor("#0E3A4C"); C_MAG=colors.HexColor("#B0207A")
    C_INK=colors.HexColor("#1B2733");  C_SEC=colors.HexColor("#5A6B78")
    C_BUFF=colors.HexColor("#F6F0E0"); C_TERRA=colors.HexColor("#EDE4C8")
    C_RIGA=colors.HexColor("#D8D2BE")

    pdf_path = OUT/f"Narrative_Porti_v{VERSIONE}.pdf"

    ELENCO_PORTI = "  ·  ".join(p_["nome"] for p_, _ in COPPIE)
    ELENCO_PORTI_LUNGO = " · ".join(f'{p_["nome"]} ({p_["paese"]})' for p_, _ in COPPIE)

    class Doc(BaseDocTemplate):
        def afterFlowable(self, fl):
            if isinstance(fl, Paragraph) and fl.style.name in ("H1","H2"):
                lvl = 0 if fl.style.name=="H1" else 1
                key = getattr(fl, "_bm", None)
                if key:
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(fl.getPlainText(), key, level=lvl, closed=False)
                    self.notify("TOCEntry", (lvl, fl.getPlainText(), self.page, key))

    # -------------------------------------------------- helper di canvas
    def testo_sp(canv, x, y, s, font, size, spacing, fill):
        # Nota: l'operatore Tc resta attivo nel content stream. Va riazzerato
        # sullo stesso text object, altrimenti i testi disegnati dopo risultano
        # più larghi del calcolato e si accavallano.
        t = canv.beginText(x, y); t.setFont(font, size); t.setCharSpace(spacing)
        t.setFillColor(fill); t.textOut(s); t.setCharSpace(0); canv.drawText(t)

    def spezza(canv, testo, font, size, maxw):
        righe, cur = [], ""
        for parola in testo.split():
            prova = (cur + " " + parola).strip()
            if canv.stringWidth(prova, font, size) <= maxw:
                cur = prova
            else:
                if cur: righe.append(cur)
                cur = parola
        if cur: righe.append(cur)
        return righe

    def riga_chip(canv, x, y, voci, size=7.8, gap=4*mm):
        """Disegna chip affiancati misurando ogni segmento: niente sovrapposizioni."""
        for etichetta, descrizione, col in voci:
            canv.setFont("Helvetica-Bold", size); canv.setFillColor(col)
            canv.drawString(x, y, etichetta)
            x += canv.stringWidth(etichetta, "Helvetica-Bold", size) + 1.4*mm
            canv.setFont("Helvetica", size); canv.setFillColor(C_SEC)
            canv.drawString(x, y, descrizione)
            x += canv.stringWidth(descrizione, "Helvetica", size) + gap

    # -------------------------------------------------- pagine
    def pagina_contenuto(canv, doc):
        canv.saveState()
        W,H = A4
        canv.setFillColor(C_NAVY); canv.rect(0, H-13*mm, W, 13*mm, stroke=0, fill=1)
        canv.setFillColor(C_MAG);  canv.rect(0, H-14*mm, W, 1*mm, stroke=0, fill=1)
        testo_sp(canv, 18*mm, H-8.5*mm, "NARRATIVE PORTI", "Helvetica-Bold", 8.5, 1.8, C_BUFF)
        canv.setFont("Helvetica", 8.5); canv.setFillColor(C_BUFF)
        canv.drawRightString(192*mm, H-8.5*mm, f"{ELENCO_PORTI}  ·  v{VERSIONE}")
        canv.setStrokeColor(C_RIGA); canv.setLineWidth(0.6)
        canv.line(18*mm, 12.5*mm, 192*mm, 12.5*mm)
        canv.setFont("Helvetica-Oblique", 7); canv.setFillColor(C_SEC)
        canv.drawString(18*mm, 9*mm, "Documento di supporto — non sostituisce carte e pubblicazioni ufficiali · Not for navigation")
        canv.setFont("Helvetica-Bold", 8.5); canv.setFillColor(C_NAVY)
        canv.drawRightString(192*mm, 8.8*mm, f"{doc.page}")
        canv.restoreState()

    def pagina_copertina(canv, doc):
        canv.saveState()
        W,H = A4
        canv.setFillColor(C_BUFF); canv.rect(0, 0, W, H, stroke=0, fill=1)
        canv.setFillColor(colors.Color(0.055,0.227,0.298, alpha=0.05))
        step=9*mm; y=step
        while y<H:
            x=step
            while x<W:
                canv.circle(x, y, 0.45, stroke=0, fill=1); x+=step
            y+=step
        # banda di testata
        canv.setFillColor(C_NAVY); canv.rect(0, H-70*mm, W, 70*mm, stroke=0, fill=1)
        canv.setFillColor(C_MAG);  canv.rect(0, H-71.6*mm, W, 1.6*mm, stroke=0, fill=1)
        testo_sp(canv, 20*mm, H-33*mm, "NARRATIVE PORTI", "Helvetica-Bold", 33, 4, C_BUFF)
        testo_sp(canv, 20.5*mm, H-42*mm, "DATABASE ARRIVI · NAVIGAZIONE", "Helvetica", 10.5, 2.2, C_BUFF)
        canv.setFillColor(C_BUFF); canv.setFont("Courier", 9)
        canv.drawString(20.5*mm, H-56*mm, f"VERSIONE {VERSIONE}   ·   GENERATO {OGGI}")
        canv.drawString(20.5*mm, H-62*mm, f"FONTE DATI: data/ — {REPO}")
        # elenco rotte
        y = H-104*mm
        for porto_, rotta_ in COPPIE:
            canv.setFillColor(C_INK); canv.setFont("Times-Italic", 24)
            canv.drawString(20*mm, y, rotta_["da"])
            x = 20*mm + canv.stringWidth(rotta_["da"], "Times-Italic", 24) + 4*mm
            canv.setFillColor(C_MAG); canv.setFont("Helvetica", 16)
            canv.drawString(x, y+0.6*mm, "\u2192")
            x += canv.stringWidth("\u2192", "Helvetica", 16) + 4*mm
            canv.setFillColor(C_INK); canv.setFont("Times-Italic", 24)
            canv.drawString(x, y, rotta_["a"])
            canv.setFont("Courier", 8.5); canv.setFillColor(C_SEC)
            d = f'{rotta_["distanza_nm"]:.2f} NM'
            if rotta_.get("distanza_calcolata"): d += " (calc.)"
            canv.drawString(20.5*mm, y-6.5*mm,
                            f'{d}  ·  {len(rotta_["waypoints"])} WAYPOINT  ·  ARRIVO {porto_["nome"].upper()}')
            y -= 17*mm

        # riquadro contenuti — altezza calcolata sul testo effettivo
        n_ = len(COPPIE)
        righe=[f'Schede porto: {ELENCO_PORTI_LUNGO}']
        righe += ["Sequenza di manovra per l'arrivo, con gli eventi operativi in evidenza",
                  f'Piano waypoint integrale di {n_} ' + ("rotta" if n_==1 else "rotte") + ', trascrizione di bordo',
                  "Cartine schematiche della rotta e dell'approccio finale per ogni scalo",
                  "Fonti ufficiali con data di verifica e provenienza di ogni dato"]
        x_box, w_box = 20*mm, 170*mm
        x_testo = 31.5*mm; w_testo = w_box - (x_testo - x_box) - 8*mm
        blocchi = [spezza(canv, r_, "Helvetica", 9, w_testo) for r_ in righe]
        n_righe = sum(len(b) for b in blocchi)
        h_box = 13*mm + n_righe*4.6*mm + (len(righe)-1)*2.4*mm + 15*mm
        y_top = H-132*mm
        canv.setStrokeColor(C_NAVY); canv.setLineWidth(0.8)
        canv.rect(x_box, y_top-h_box, w_box, h_box, stroke=1, fill=0)
        testo_sp(canv, 26*mm, y_top-8*mm, "CONTENUTO DI QUESTA VERSIONE", "Helvetica-Bold", 8.5, 2, C_NAVY)
        y = y_top-16*mm
        for blocco in blocchi:
            canv.setFillColor(C_MAG); canv.circle(27.5*mm, y+1.2*mm, 1.05*mm, stroke=0, fill=1)
            canv.setFillColor(C_INK); canv.setFont("Helvetica", 9)
            for i, riga in enumerate(blocco):
                canv.drawString(x_testo, y - i*4.6*mm, riga)
            y -= len(blocco)*4.6*mm + 2.4*mm
        # legenda provenienza — posizioni misurate
        y_leg = y_top - h_box + 9.5*mm
        canv.setFont("Helvetica", 7.8); canv.setFillColor(C_SEC)
        canv.drawString(26*mm, y_leg+5.5*mm, "Provenienza dei dati riportata accanto a ogni voce:")
        riga_chip(canv, 26*mm, y_leg, [
            ("[C]",   "comandante (fonte di verità)", C_NAVY),
            ("[W]",   "web verificato + data",        C_MAG),
            ("[C+W]", "confermato da entrambi",       colors.HexColor("#7A2E58")),
            ("[P]",   "in attesa di conferma",        C_SEC)])
        # disclaimer
        canv.setFillColor(C_INK); canv.setFont("Helvetica-Bold", 8)
        canv.drawString(20*mm, 30*mm, "Documento di supporto alla pianificazione.")
        canv.setFont("Helvetica", 8); canv.setFillColor(C_SEC)
        canv.drawString(20*mm, 25.5*mm, "Non sostituisce carte nautiche ufficiali, pubblicazioni e ordinanze. Not for navigation.")
        canv.restoreState()

    doc = Doc(str(pdf_path), pagesize=A4,
              leftMargin=18*mm, rightMargin=18*mm, topMargin=20*mm, bottomMargin=16*mm,
              title=f"Narrative Porti v{VERSIONE}", author="Narrative Porti",
              subject="Database arrivi — " + " | ".join(r_["titolo"] for _, r_ in COPPIE))
    frame = Frame(18*mm, 14*mm, 174*mm, 263*mm, id="f",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([
        PageTemplate(id="Copertina", frames=[frame], onPage=pagina_copertina),
        PageTemplate(id="Contenuto", frames=[frame], onPage=pagina_contenuto),
    ])

    # Scala tipografica: 6 corpi netti (15 / 11 / 10 / 9 / 8.5 / 7.5) — niente
    # differenze da mezzo punto, che rendono il testo incoerente senza motivo.
    S = {
      "H1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=15, leading=18.5,
                           textColor=C_NAVY, spaceBefore=1, spaceAfter=2),
      "H1sub": ParagraphStyle("H1sub", fontName="Times-Italic", fontSize=11, leading=13.5,
                           textColor=C_SEC, spaceAfter=5),
      "H2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=10, leading=12.5,
                           textColor=C_NAVY, spaceBefore=7, spaceAfter=3.5),
      "corpo": ParagraphStyle("corpo", fontName="Helvetica", fontSize=9, leading=11.8, textColor=C_INK),
      "cella": ParagraphStyle("cella", fontName="Helvetica", fontSize=8.5, leading=10.6, textColor=C_INK),
      "cellaEt": ParagraphStyle("cellaEt", fontName="Helvetica-Bold", fontSize=8.5, leading=10.6, textColor=C_NAVY),
      "seqNome": ParagraphStyle("seqNome", fontName="Helvetica-Bold", fontSize=8.5, leading=10.6, textColor=C_INK),
      "narr": ParagraphStyle("narr", fontName="Helvetica-Oblique", fontSize=8.5, leading=10.8, textColor=C_INK),
      "fonte": ParagraphStyle("fonte", fontName="Helvetica", fontSize=8.5, leading=10.6, textColor=C_INK),
      "legenda": ParagraphStyle("legenda", fontName="Helvetica", fontSize=7.5, leading=9.8, textColor=C_SEC),
      "toc0": ParagraphStyle("toc0", fontName="Helvetica-Bold", fontSize=9, leading=11.6,
                             textColor=C_NAVY, spaceBefore=1.5, spaceAfter=0),
      "toc1": ParagraphStyle("toc1", fontName="Helvetica", fontSize=8.5, leading=10.6,
                             leftIndent=11, textColor=C_INK, spaceBefore=0, spaceAfter=0),
    }
    COL_PROV = {"C":"#0E3A4C","W":"#B0207A","CW":"#7A2E58","P":"#5A6B78"}
    def prov(f_, ver=None):
        lab = {"C":"C","W":"W","CW":"C+W","P":"P"}[f_]
        if f_ in ("W","CW") and ver: lab += "\u00A0" + data_breve(ver)
        return f'&nbsp;<font size="7" color="{COL_PROV[f_]}"><b>[{lab}]</b></font>'
    def H(testo, key, stile="H1"):
        p=Paragraph(testo, S[stile]); p._bm=key; return p

    def tabella_voci(voci, w_et, w_val):
        rows=[]
        for v in voci:
            val = v["v"] + prov(v["fonte"], v.get("verificato"))
            if v.get("nota"): val += f'<br/><font size="7.5" color="#5A6B78">{v["nota"]}</font>'
            rows.append([Paragraph(v["t"], S["cellaEt"]), Paragraph(val, S["cella"])])
        t=Table(rows, colWidths=[w_et, w_val])
        t.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LINEBELOW",(0,0),(-1,-2),0.4,C_RIGA),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[None, colors.Color(0.055,0.227,0.298, alpha=0.035)]),
            ("TOPPADDING",(0,0),(-1,-1),1.9),("BOTTOMPADDING",(0,0),(-1,-1),1.9),
            ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
        ]))
        return t

    story=[NextPageTemplate("Contenuto"), PageBreak()]

    # ---- sommario compatto (in testa alla prima pagina di contenuto)
    story.append(Paragraph("Sommario", S["H2"]))
    toc=TableOfContents(); toc.levelStyles=[S["toc0"], S["toc1"]]
    story.append(toc)
    story.append(Spacer(1, 9))

    def blocco_scalo(porto, rotta, primo):
        """Scheda porto + rotta + waypoint per un singolo scalo."""
        b=[]
        sfx = "_" + porto["id"]
        if not primo:
            b.append(PageBreak())
        b.append(H(f'Scheda porto — {porto["nome"]}', "porto"+sfx))
        b.append(Paragraph(f'{porto["banchina_principale"]} — {porto["paese"]}, {porto["regione"]}', S["H1sub"]))
        b.append(Paragraph(
            f'<font name="Courier">{porto["posizione"]["testo"]}</font>'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;Scheda v{porto["versione_scheda"]} — aggiornata {porto["aggiornato"]}', S["corpo"]))
        if primo:
            b.append(Paragraph(
                'Provenienza: <font color="#0E3A4C"><b>[C]</b></font> comandante (fonte di verità) · '
                '<font color="#B0207A"><b>[W]</b></font> web verificato + data · '
                '<font color="#7A2E58"><b>[C+W]</b></font> confermato da entrambi · '
                '<font color="#5A6B78"><b>[P]</b></font> in attesa di conferma', S["legenda"]))
        b.append(Spacer(1, 3))

        # sequenza di manovra
        b.append(H("Sequenza di manovra — arrivo", "sequenza"+sfx, "H2"))
        seq_rows=[]
        for s_ in porto["avvicinamento"]["sequenza"]:
            wp = f'WP {s_["wp"]:02d}' if s_["wp"] else "\u2014"
            evid = s_["tipo"] in ("velocita","manning","vts","manovra","ormeggio")
            col = "#B0207A" if evid else "#1B2733"
            seq_rows.append([
                Paragraph(f'<font name="Courier" size="7.5" color="#5A6B78">{wp}</font>', S["cella"]),
                Paragraph(f'<font color="{col}"><b>{s_["nome"]}</b></font>', S["seqNome"]),
                Paragraph(s_["azione"], S["cella"])])
        t=Table(seq_rows, colWidths=[14*mm, 42*mm, 118*mm])
        t.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LINEBEFORE",(1,0),(1,-1),1.1,C_NAVY),
            ("LINEBELOW",(0,0),(-1,-2),0.4,C_RIGA),
            ("TOPPADDING",(0,0),(-1,-1),2.4),("BOTTOMPADDING",(0,0),(-1,-1),2.4),
            ("LEFTPADDING",(1,0),(1,-1),6),("LEFTPADDING",(2,0),(2,-1),2),
        ]))
        b.append(t)
        b.append(Spacer(1,3))
        b.append(Paragraph(f'<b>Vento in approccio:</b> {porto["avvicinamento"]["vento"]}'+prov("C"), S["corpo"]))

        for sez in porto["sezioni"]:
            chiave = "sez"+sfx+"_"+re.sub(r"\W+","_",sez["titolo"].lower())
            b.append(KeepTogether([H(sez["titolo"], chiave, "H2"),
                                   tabella_voci(sez["voci"], 34*mm, 140*mm)]))

        # note narrative su due colonne
        b.append(H("Note narrative del comandante", "narrative"+sfx, "H2"))
        note = ["\u201C"+n+"\u201D" for n in porto["note_narrative"]]
        meta = (len(note)+1)//2
        csx, cdx = note[:meta], note[meta:]
        cdx += [""]*(len(csx)-len(cdx))
        nrows=[[Paragraph(a, S["narr"]) if a else "", Paragraph(x, S["narr"]) if x else ""]
               for a,x in zip(csx, cdx)]
        tn=Table(nrows, colWidths=[85*mm, 85*mm], hAlign="LEFT")
        tn.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LINEBEFORE",(0,0),(0,-1),2.2,C_TERRA),
            ("LINEBEFORE",(1,0),(1,-1),2.2,C_TERRA),
            ("BACKGROUND",(0,0),(-1,-1),colors.Color(0.929,0.894,0.784, alpha=0.32)),
            ("TOPPADDING",(0,0),(-1,-1),2.5),("BOTTOMPADDING",(0,0),(-1,-1),2.5),
            ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),5),
        ]))
        b.append(tn)

        # rotta: cartine affiancate, titolo e figure sempre sulla stessa pagina
        blocco_rotta = [H(f'Rotta {rotta["titolo"]}', "rotta"+sfx)]
        dist = f'{rotta["distanza_nm"]:.2f} NM'
        if rotta.get("distanza_calcolata"): dist += " (calcolata)"
        tratte = f' · tratte {rotta["tipo_tratte"]}' if rotta.get("tipo_tratte") else ""
        blocco_rotta.append(Paragraph(f'{dist} · {len(rotta["waypoints"])} waypoint{tratte} '
                           f'— trascrizione integrale del piano di bordo', S["H1sub"]))
        note_rotta=[Paragraph("<b>Note di rotta</b>", S["corpo"])]
        for n in rotta["note"]:
            note_rotta.append(Paragraph("· "+n["testo"]+prov(n["fonte"], n.get("verificato")), S["fonte"]))
        def mappa_img(suffisso, larghezza):
            nome = f'_{rotta["id"]}_{suffisso}'
            return Image(str(OUT/f"{nome}.png"), width=larghezza,
                         height=larghezza*PROPORZIONI[nome])
        cella_dx=[mappa_img("approccio", 80*mm), Spacer(1,5)] + note_rotta
        t_mappe=Table([[mappa_img("overview", 62*mm), cella_dx]], colWidths=[66*mm, 108*mm])
        t_mappe.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                     ("LEFTPADDING",(0,0),(0,0),0),("RIGHTPADDING",(1,0),(1,0),0)]))
        blocco_rotta.append(t_mappe)
        b.append(KeepTogether(blocco_rotta))

        # piano waypoint
        b.append(PageBreak())
        b.append(H("Piano waypoint — trascrizione di bordo", "waypoint"+sfx))
        b.append(Paragraph("Coordinate e dati riportati esattamente come nel piano di bordo. "
                           "In rosa i waypoint con annotazione operativa.", S["H1sub"]))
        ETI={"n":"N.","nome":"NOME","raggio_nm":"R [NM]","lat_txt":"LAT","lon_txt":"LON",
             "bww":"BWW\u00B0","dist_enr":"D.ENR","dist":"DIST","sail":"SAIL","ap":"AP"}
        LARG={"n":8,"nome":56,"raggio_nm":13,"lat_txt":25,"lon_txt":26,
              "bww":13,"dist_enr":14,"dist":13,"sail":10,"ap":9}
        FMT={"raggio_nm":"{:.2f}","bww":"{:.1f}","dist_enr":"{:.2f}","dist":"{:.2f}"}
        cols=rotta["colonne"]
        larg=[LARG[c] for c in cols]
        scala=174.0/sum(larg)
        wrows=[[ETI[c] for c in cols]]
        for w in rotta["waypoints"]:
            riga=[]
            for c in cols:
                v=w.get(c)
                riga.append("\u2014" if v in (None,"") else (FMT[c].format(v) if c in FMT else str(v)))
            wrows.append(riga)
        tw=Table(wrows, colWidths=[x*scala*mm for x in larg], repeatRows=1)
        stile=[("FONTNAME",(0,0),(-1,-1),"Courier"),("FONTSIZE",(0,0),(-1,-1),7),
               ("FONTNAME",(0,0),(-1,0),"Courier-Bold"),("FONTSIZE",(0,0),(-1,0),7),
               ("BACKGROUND",(0,0),(-1,0),C_NAVY),("TEXTCOLOR",(0,0),(-1,0),C_BUFF),
               ("LINEBELOW",(0,1),(-1,-1),0.3,C_RIGA),
               ("TOPPADDING",(0,0),(-1,-1),0.9),("BOTTOMPADDING",(0,0),(-1,-1),0.9),
               ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
               ("VALIGN",(0,0),(-1,-1),"MIDDLE")]
        for i,w in enumerate(rotta["waypoints"], start=1):
            if w.get("nota"):
                stile.append(("BACKGROUND",(0,i),(-1,i), colors.Color(0.69,0.125,0.478, alpha=0.08)))
        tw.setStyle(TableStyle(stile))
        b.append(tw)

        b.append(H("Annotazioni sui waypoint evidenziati", "annotazioni"+sfx, "H2"))
        ann=[f'<font name="Courier" size="7.5" color="#B0207A">WP {w["n"]:02d}</font>&nbsp; {w["nota"]}'
             for w in rotta["waypoints"] if w.get("nota")]
        meta=(len(ann)+1)//2
        sx, dx = ann[:meta], ann[meta:]
        dx += [""]*(len(sx)-len(dx))
        ta=Table([[Paragraph(a, S["cella"]) if a else "", Paragraph(x, S["cella"]) if x else ""]
                  for a,x in zip(sx,dx)], colWidths=[85*mm,85*mm], hAlign="LEFT")
        ta.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                ("TOPPADDING",(0,0),(-1,-1),1.6),("BOTTOMPADDING",(0,0),(-1,-1),1.6),
                                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),6)]))
        b.append(ta)

        # fonti dello scalo
        titolo_fonti = H(f'Fonti e verifiche — {porto["nome"]}', "fonti"+sfx, "H2")
        f_par=[Paragraph(f'· <link href="{f_["url"]}" color="#0E3A4C"><u>{f_["label"]}</u></link> '
                         f'<font name="Courier" size="7" color="#5A6B78">{data_breve(f_["verificato"])}</font>',
                         S["fonte"]) for f_ in porto["fonti"]]
        meta=(len(f_par)+1)//2
        fsx, fdx = f_par[:meta], f_par[meta:]
        fdx += [""]*(len(fsx)-len(fdx))
        tf=Table([[a,x] for a,x in zip(fsx,fdx)], colWidths=[85*mm,85*mm], hAlign="LEFT")
        tf.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                ("TOPPADDING",(0,0),(-1,-1),1.8),("BOTTOMPADDING",(0,0),(-1,-1),1.8),
                                ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),6)]))
        b.append(KeepTogether([titolo_fonti, tf]))
        return b

    for i,(porto, rotta) in enumerate(COPPIE):
        story += blocco_scalo(porto, rotta, primo=(i==0))

    # ---- registro versioni
    story.append(PageBreak())
    story.append(H("Registro versioni", "changelog"))
    story.append(Paragraph("Ogni modifica ai dati incrementa la versione e viene registrata qui.", S["H1sub"]))
    voci_log=[]
    for riga in (BASE/"CHANGELOG.md").read_text(encoding="utf-8").splitlines():
        riga=riga.strip()
        if riga.startswith("## "):
            voci_log.append(Paragraph(f'<font color="#0E3A4C"><b>{riga[3:]}</b></font>', S["corpo"]))
        elif riga.startswith("- "):
            voci_log.append(Paragraph("· "+riga[2:], S["fonte"]))
    meta=(len(voci_log)+1)//2
    lsx, ldx = voci_log[:meta], voci_log[meta:]
    ldx += [""]*(len(lsx)-len(ldx))
    tl=Table([[a,x] for a,x in zip(lsx,ldx)], colWidths=[85*mm,85*mm], hAlign="LEFT")
    tl.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                            ("TOPPADDING",(0,0),(-1,-1),1.4),("BOTTOMPADDING",(0,0),(-1,-1),1.4),
                            ("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),6)]))
    story.append(tl)


    doc.multiBuild(story)
    print("PDF   ->", pdf_path)

if __name__ == "__main__":
    build_html()
    build_cartine()
    build_pdf()
    print("Build completato — versione", VERSIONE)
