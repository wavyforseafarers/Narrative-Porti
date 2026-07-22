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

for r in ROTTE:
    for w in r["waypoints"]:
        w["lat"] = ddm_to_dec(w["lat_txt"]); w["lon"] = ddm_to_dec(w["lon_txt"])

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
def chartlet(rotta, path, estensione, passo, etichette, titolo, figsize, marca_note=True, scava=None):
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

    fig, ax = plt.subplots(figsize=figsize, dpi=200)
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
                    fontsize=6.2, color="#1B2733", ha=ha, family="DejaVu Sans",
                    path_effects=[pe.withStroke(linewidth=2.2, foreground="#F6F0E0")])

    ax.set_xlim(lon0,lon1); ax.set_ylim(lat0,lat1)
    ax.set_aspect(1/np.cos(np.radians((lat0+lat1)/2)))
    ax.tick_params(labelsize=5.6, colors=SEC, length=2.5)
    ax.grid(color="#1B2733", alpha=.10, lw=.5)
    for s in ax.spines.values(): s.set_color(SEC); s.set_linewidth(.7)
    ax.set_title(titolo, fontsize=8, family="DejaVu Sans", color=NAVY, loc="left", pad=5)
    fig.text(.995,.006,"Schema indicativo — not for navigation", ha="right",
             fontsize=5.4, color=SEC, style="italic")
    fig.tight_layout(pad=.7)
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("CARTA ->", path)

def build_cartine():
    r = ROTTE[0]
    chartlet(r, OUT/"_rotta_overview.png",
        (59.18, 60.88, 3.90, 5.58), 0.004,
        [(1,"BERGEN — PIER",6,4,"left"), (4,"Askøybrua (62 m)",6,-9,"left"),
         (13,"POFF FEDJE",7,3,"left"), (14,"TSS OUT",-6,5,"right"),
         (16,"12 NM OUT",-7,-3,"right"), (17,"12 NM IN",-8,0,"right"),
         (19,"PORT LIMIT",-8,4,"right"), (25,"HAUGESUND",8,-2,"left")],
        "Rotta Bergen → Haugesund — 132.61 NM · 25 WP · tratte RL", (6.0,7.4))
    chartlet(r, OUT/"_rotta_approccio.png",
        (59.345, 59.555, 4.86, 5.34), 0.0008,
        [(19,"WP19 · PORT LIMIT",6,6,"left"), (20,"WP20 · GRUNNANE 11→7 kn",6,8,"left"),
         (21,"WP21 · SBE / RED MANNING",-9,10,"right"), (22,"WP22 · Kråkeflua — 8 kn",-9,-12,"right"),
         (23,"WP23 · GALVEN",-10,0,"right"), (24,"WP24 · GALTEN — acc. SX ROT>30°/min",9,-8,"left"),
         (25,"GARPESKJÆRSKAIEN",9,5,"left")],
        "Approccio finale Haugesund — sequenza operativa", (7.6,4.6),
        scava={"da_wp": 21, "raggio_deg": 0.0030})

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

    porto=PORTI[0]; rotta=ROTTE[0]
    pdf_path = OUT/f"Narrative_Porti_v{VERSIONE}.pdf"

    class Doc(BaseDocTemplate):
        def afterFlowable(self, fl):
            if isinstance(fl, Paragraph) and fl.style.name in ("H1","H2"):
                lvl = 0 if fl.style.name=="H1" else 1
                key = getattr(fl, "_bm", None)
                if key:
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(fl.getPlainText(), key, level=lvl, closed=False)
                    self.notify("TOCEntry", (lvl, fl.getPlainText(), self.page, key))

    def pagina_contenuto(canv, doc):
        canv.saveState()
        canv.setStrokeColor(C_MAG); canv.setLineWidth(1.4)
        canv.line(18*mm, 285*mm, 192*mm, 285*mm)
        canv.setFont("Helvetica-Bold", 7); canv.setFillColor(C_NAVY)
        canv.drawString(18*mm, 287*mm, "NARRATIVE PORTI")
        canv.setFont("Helvetica", 7); canv.setFillColor(C_SEC)
        canv.drawRightString(192*mm, 287*mm, f"v{VERSIONE} · {OGGI}")
        canv.setFont("Helvetica-Oblique", 6.5)
        canv.drawString(18*mm, 10*mm, "Documento di supporto — non sostituisce carte e pubblicazioni ufficiali · Not for navigation")
        canv.setFont("Helvetica", 7); canv.setFillColor(C_NAVY)
        canv.drawRightString(192*mm, 10*mm, f"Pag. {doc.page}")
        canv.restoreState()

    def testo_sp(canv, x, y, s, font, size, spacing, fill):
        t = canv.beginText(x, y); t.setFont(font, size); t.setCharSpace(spacing)
        t.setFillColor(fill); t.textOut(s); canv.drawText(t)

    def pagina_copertina(canv, doc):
        canv.saveState()
        W,H = A4
        canv.setFillColor(C_BUFF); canv.rect(0,0,W,H,1,0)
        # reticolo puntinato da carta
        canv.setFillColor(colors.Color(0.055,0.227,0.298, alpha=0.05))
        step=9*mm
        y=step
        while y<H:
            x=step
            while x<W:
                canv.circle(x,y,0.45,0,1); x+=step
            y+=step
        # banda navy
        canv.setFillColor(C_NAVY); canv.rect(0, H-72*mm, W, 72*mm, 1, 0)
        canv.setFillColor(C_MAG);  canv.rect(0, H-72*mm-1.6*mm, W, 1.6*mm, 1, 0)
        buff = colors.HexColor("#F6F0E0")
        testo_sp(canv, 20*mm, H-34*mm, "NARRATIVE PORTI", "Helvetica-Bold", 33, 4, buff)
        testo_sp(canv, 20.5*mm, H-43*mm, "DATABASE ARRIVI · NAVIGAZIONE", "Helvetica", 10.5, 2.2, buff)
        canv.setFillColor(buff)
        canv.setFont("Courier", 9)
        canv.drawString(20.5*mm, H-58*mm, f"VERSIONE {VERSIONE}   ·   GENERATO {OGGI}")
        canv.drawString(20.5*mm, H-64*mm, f"FONTE DATI: data/ — {REPO}")
        # rotta al centro
        canv.setFillColor(C_INK); canv.setFont("Times-Italic", 31)
        canv.drawString(20*mm, H-118*mm, "Bergen")
        canv.setFillColor(C_MAG); canv.setFont("Helvetica", 22)
        canv.drawString(58*mm, H-117.4*mm, "\u2192")
        canv.setFillColor(C_INK); canv.setFont("Times-Italic", 31)
        canv.drawString(70*mm, H-118*mm, "Haugesund")
        canv.setFont("Courier", 9.5); canv.setFillColor(C_SEC)
        canv.drawString(20.5*mm, H-127*mm, "132.61 NM  ·  25 WAYPOINT  ·  TRATTE LOSSODROMICHE")
        # riquadro contenuti
        canv.setStrokeColor(C_NAVY); canv.setLineWidth(0.8)
        canv.rect(20*mm, 52*mm, 170*mm, 92*mm, 1, 0)
        testo_sp(canv, 26*mm, 136*mm, "CONTENUTO DI QUESTA VERSIONE", "Helvetica-Bold", 8.5, 2, C_NAVY)
        canv.setFont("Helvetica", 9.5); canv.setFillColor(C_INK)
        righe=["Scheda porto — Haugesund (Norvegia) · Garpeskjærskaien, Haugesund Cruise Port",
               "Sequenza di manovra per l'arrivo da nord, con eventi operativi",
               "Piano waypoint integrale Bergen \u2192 Haugesund (25 WP, trascrizione di bordo)",
               "Cartine schematiche della rotta e dell'approccio finale",
               "Fonti ufficiali con data di verifica (22.07.2026) e provenienza di ogni dato"]
        y=127*mm
        for r_ in righe:
            canv.setFillColor(C_MAG); canv.circle(27.5*mm, y+1.2*mm, 1.05*mm, 0, 1)
            canv.setFillColor(C_INK); canv.drawString(31.5*mm, y, r_); y-=8.2*mm
        canv.setFont("Helvetica", 8); canv.setFillColor(C_SEC)
        canv.drawString(26*mm, 60*mm, "Provenienza dei dati:")
        canv.setFillColor(C_NAVY); canv.setFont("Helvetica-Bold", 8)
        canv.drawString(26*mm, 55*mm, "C = comandante (fonte di verità)")
        canv.setFillColor(C_MAG)
        canv.drawString(75*mm, 55*mm, "W = web verificato")
        canv.setFillColor(C_SEC); canv.setFont("Helvetica", 8)
        canv.drawString(107*mm, 55*mm, "C+W = confermato da entrambi · P = in attesa")
        # disclaimer
        canv.setFillColor(C_INK); canv.setFont("Helvetica-Bold", 8)
        canv.drawString(20*mm, 40*mm, "Documento di supporto alla pianificazione.")
        canv.setFont("Helvetica", 8)
        canv.drawString(20*mm, 35.5*mm, "Non sostituisce carte nautiche ufficiali, pubblicazioni e ordinanze. Not for navigation.")
        canv.restoreState()

    doc = Doc(str(pdf_path), pagesize=A4,
              leftMargin=18*mm, rightMargin=18*mm, topMargin=20*mm, bottomMargin=16*mm,
              title=f"Narrative Porti v{VERSIONE}", author="Narrative Porti",
              subject="Database arrivi — Bergen \u2192 Haugesund")
    frame = Frame(18*mm, 14*mm, 174*mm, 268*mm, id="f")
    doc.addPageTemplates([
        PageTemplate(id="Copertina", frames=[frame], onPage=pagina_copertina),
        PageTemplate(id="Contenuto", frames=[frame], onPage=pagina_contenuto),
    ])

    S = {
      "H1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=17, leading=21,
                           textColor=C_NAVY, spaceBefore=2, spaceAfter=3),
      "H1sub": ParagraphStyle("H1sub", fontName="Times-Italic", fontSize=12.5, leading=15,
                           textColor=C_SEC, spaceAfter=10),
      "H2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=11, leading=14,
                           textColor=C_NAVY, spaceBefore=12, spaceAfter=5),
      "corpo": ParagraphStyle("corpo", fontName="Helvetica", fontSize=9, leading=12.6, textColor=C_INK),
      "cella": ParagraphStyle("cella", fontName="Helvetica", fontSize=8.6, leading=11.4, textColor=C_INK),
      "cellaEt": ParagraphStyle("cellaEt", fontName="Helvetica-Bold", fontSize=8.2, leading=11, textColor=C_SEC),
      "mono": ParagraphStyle("mono", fontName="Courier", fontSize=8.4, leading=11, textColor=C_INK),
      "narr": ParagraphStyle("narr", fontName="Helvetica-Oblique", fontSize=8.8, leading=12.2, textColor=C_INK),
      "fonte": ParagraphStyle("fonte", fontName="Helvetica", fontSize=8.2, leading=11.4, textColor=C_INK),
      "toc0": ParagraphStyle("toc0", fontName="Helvetica-Bold", fontSize=10.5, leading=17, textColor=C_NAVY),
      "toc1": ParagraphStyle("toc1", fontName="Helvetica", fontSize=9.2, leading=14.5,
                             leftIndent=12, textColor=C_INK),
    }
    def prov(f_, ver=None):
        lab={"C":"C · COMANDANTE","W":"W · VERIFICATO","CW":"C+W · CONFERMATO","P":"IN ATTESA"}[f_]
        if f_ in ("W","CW") and ver: lab += " " + ver
        col = {"C":"#0E3A4C","W":"#B0207A","CW":"#7A2E58","P":"#5A6B78"}[f_]
        return f'&nbsp;<font size="6.2" color="{col}"><b>[{lab}]</b></font>'
    def H(testo, key, stile="H1"):
        p=Paragraph(testo, S[stile]); p._bm=key; return p

    story=[NextPageTemplate("Contenuto"), PageBreak()]

    # ---- sommario
    story.append(Paragraph("Sommario", S["H1"]))
    toc=TableOfContents(); toc.levelStyles=[S["toc0"], S["toc1"]]
    story.append(toc); story.append(PageBreak())

    # ---- scheda porto
    story.append(H("Scheda porto — Haugesund", "porto_haugesund"))
    story.append(Paragraph(f'{porto["banchina_principale"]} — {porto["paese"]}, {porto["regione"]}', S["H1sub"]))
    story.append(Paragraph(f'<font name="Courier">{porto["posizione"]["testo"]}</font>'
                           f'&nbsp;&nbsp;·&nbsp;&nbsp;Scheda v{porto["versione_scheda"]} — aggiornata {porto["aggiornato"]}', S["corpo"]))
    story.append(Spacer(1, 6))

    story.append(H("Sequenza di manovra — arrivo da nord", "sequenza", "H2"))
    seq_rows=[]
    for s_ in porto["avvicinamento"]["sequenza"]:
        wp = f'WP {s_["wp"]:02d}' if s_["wp"] else "—"
        evid = s_["tipo"] in ("velocita","manning","vts","manovra","ormeggio")
        nome = f'<font color="{"#B0207A" if evid else "#1B2733"}"><b>{s_["nome"]}</b></font>'
        seq_rows.append([Paragraph(f'<font name="Courier" size="7.6">{wp}</font>', S["cella"]),
                         Paragraph(f'{nome}<br/><font size="8">{s_["azione"]}</font>', S["cella"])])
    t=Table(seq_rows, colWidths=[17*mm, 157*mm])
    t.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBEFORE",(1,0),(1,-1),1.1,C_NAVY),
        ("LINEBELOW",(0,0),(-1,-2),0.4,C_RIGA),
        ("TOPPADDING",(0,0),(-1,-1),3.5),("BOTTOMPADDING",(0,0),(-1,-1),3.5),
        ("LEFTPADDING",(1,0),(1,-1),7),
    ]))
    story.append(t)
    story.append(Spacer(1,4))
    story.append(Paragraph(f'<b>Vento in approccio:</b> {porto["avvicinamento"]["vento"]}'+prov("C"), S["corpo"]))

    for sez in porto["sezioni"]:
        blocco=[H(sez["titolo"], "sez_"+re.sub(r"\W+","_",sez["titolo"].lower()), "H2")]
        rows=[]
        for v in sez["voci"]:
            val = v["v"] + prov(v["fonte"], v.get("verificato"))
            if v.get("nota"): val += f'<br/><font size="7.6" color="#5A6B78">{v["nota"]}</font>'
            rows.append([Paragraph(v["t"], S["cellaEt"]), Paragraph(val, S["cella"])])
        tb=Table(rows, colWidths=[38*mm, 136*mm])
        tb.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("LINEBELOW",(0,0),(-1,-2),0.4,C_RIGA),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[None, colors.Color(0.055,0.227,0.298, alpha=0.035)]),
            ("TOPPADDING",(0,0),(-1,-1),3.2),("BOTTOMPADDING",(0,0),(-1,-1),3.2),
        ]))
        blocco.append(tb)
        story.append(KeepTogether(blocco))

    story.append(H("Note narrative del comandante", "narrative", "H2"))
    nrows=[[Paragraph("\u201C"+n+"\u201D", S["narr"])] for n in porto["note_narrative"]]
    tn=Table(nrows, colWidths=[174*mm])
    tn.setStyle(TableStyle([
        ("LINEBEFORE",(0,0),(0,-1),2.2,C_TERRA),
        ("BACKGROUND",(0,0),(-1,-1),colors.Color(0.929,0.894,0.784, alpha=0.35)),
        ("TOPPADDING",(0,0),(-1,-1),3.4),("BOTTOMPADDING",(0,0),(-1,-1),3.4),
        ("LEFTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(tn)
    story.append(PageBreak())

    # ---- rotta
    story.append(H("Rotta Bergen \u2192 Haugesund", "rotta"))
    story.append(Paragraph(f'{rotta["distanza_nm"]:.2f} NM · {len(rotta["waypoints"])} waypoint · tratte {rotta["tipo_tratte"]} — trascrizione integrale del piano di bordo', S["H1sub"]))
    story.append(Image(str(OUT/"_rotta_overview.png"), width=128*mm, height=128*mm*(7.4/6.0)))
    story.append(PageBreak())

    story.append(H("Approccio finale", "approccio", "H2"))
    story.append(Image(str(OUT/"_rotta_approccio.png"), width=174*mm, height=174*mm*(4.6/7.6)))
    story.append(Spacer(1,6))
    for n in rotta["note"]:
        story.append(Paragraph("· "+n["testo"]+prov(n["fonte"], n.get("verificato")), S["corpo"]))
    story.append(PageBreak())

    story.append(H("Piano waypoint — trascrizione di bordo", "waypoint", "H2"))
    intest=["N.","NOME","R [NM]","LAT","LON","BWW\u00B0","D.ENR","DIST","SAIL"]
    wrows=[intest]
    for w in rotta["waypoints"]:
        wrows.append([str(w["n"]), w["nome"],
                      f'{w["raggio_nm"]:.2f}' if w["raggio_nm"] is not None else "—",
                      w["lat_txt"], w["lon_txt"],
                      f'{w["bww"]:.1f}' if w["bww"] is not None else "—",
                      f'{w["dist_enr"]:.2f}' if w["dist_enr"] is not None else "—",
                      f'{w["dist"]:.2f}' if w["dist"] is not None else "—",
                      w["sail"] or "—"])
    tw=Table(wrows, colWidths=[8*mm,52*mm,13*mm,25*mm,26*mm,13*mm,14*mm,13*mm,10*mm], repeatRows=1)
    stile=[("FONTNAME",(0,0),(-1,-1),"Courier"),("FONTSIZE",(0,0),(-1,-1),6.6),
           ("FONTNAME",(0,0),(-1,0),"Courier-Bold"),("FONTSIZE",(0,0),(-1,0),6.4),
           ("BACKGROUND",(0,0),(-1,0),C_NAVY),("TEXTCOLOR",(0,0),(-1,0),C_BUFF),
           ("LINEBELOW",(0,1),(-1,-1),0.3,C_RIGA),
           ("TOPPADDING",(0,0),(-1,-1),2.2),("BOTTOMPADDING",(0,0),(-1,-1),2.2),
           ("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3),
           ("VALIGN",(0,0),(-1,-1),"MIDDLE")]
    for i,w in enumerate(rotta["waypoints"], start=1):
        if w.get("nota"):
            stile.append(("BACKGROUND",(0,i),(-1,i), colors.Color(0.69,0.125,0.478, alpha=0.08)))
    tw.setStyle(TableStyle(stile))
    story.append(tw)
    story.append(Spacer(1,7))
    story.append(Paragraph("<b>Annotazioni sui waypoint evidenziati</b>", S["corpo"]))
    for w in rotta["waypoints"]:
        if w.get("nota"):
            story.append(Paragraph(f'<font name="Courier" size="7.6">WP {w["n"]:02d}</font>&nbsp; {w["nota"]}', S["cella"]))
    story.append(PageBreak())

    # ---- fonti e changelog
    story.append(H("Fonti e verifiche", "fonti"))
    story.append(Paragraph("Tutte le integrazioni web sono esclusivamente nautiche e verificate alla data indicata. In caso di discrepanza prevale il dato del comandante.", S["H1sub"]))
    for f_ in porto["fonti"]:
        story.append(Paragraph(f'· <link href="{f_["url"]}" color="#0E3A4C"><u>{f_["label"]}</u></link> '
                               f'&nbsp;<font name="Courier" size="6.8" color="#5A6B78">verif. {f_["verificato"]}</font>', S["fonte"]))
    story.append(Spacer(1,10))
    story.append(H("Registro versioni", "changelog", "H2"))
    for riga in (BASE/"CHANGELOG.md").read_text(encoding="utf-8").splitlines():
        riga=riga.strip()
        if riga.startswith("## "):
            story.append(Paragraph(f'<b>{riga[3:]}</b>', S["corpo"]))
        elif riga.startswith("- "):
            story.append(Paragraph("· "+riga[2:], S["fonte"]))

    doc.multiBuild(story)
    print("PDF   ->", pdf_path)

if __name__ == "__main__":
    build_html()
    build_cartine()
    build_pdf()
    print("Build completato — versione", VERSIONE)
