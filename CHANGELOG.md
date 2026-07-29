# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate qui.
Formato versione: `vMAJOR.MINOR` — MINOR per aggiunte/modifiche ai dati, MAJOR per cambi di struttura.

## v1.2 — 2026-07-29

- Secondo scalo: Stavanger (Norvegia) — Strandkaien 16W, Cruise & Waiting Terminal.
- Rotta Ålesund → Stavanger: 28 waypoint (trascrizione integrale), imbarco pilota a Skudefjord, passaggio stretto Kalhammarodden–Tjuvholmen.
- Verifiche del 29.07.2026: Kvitsøy VTS settore Sud ch 18, Port of Stavanger ch 12, banchina 309 m orientata 340°, UKC 1,5% della larghezza, shore power 16 MW, limite 8 kn in baia interna, regime di restrizioni acustiche.
- Ålesund: Storneskaia 354 m, ISPS, energia da terra 400/440/690 V; contatti Havnevakta.
- Build multi-scalo: struttura dati e generatore ora gestiscono più porti e rotte; copertina, sommario e testata si adattano al numero di scali.
- Tabella waypoint a colonne variabili: ogni rotta dichiara le proprie colonne, così i piani di bordo con campi diversi restano fedeli all'originale.
- Distanza di rotta calcolata dalle coordinate quando non riportata nella tabella di bordo, ed etichettata come tale.
- Segnalata la differenza fra il divieto EGCS registrato a bordo e la formulazione meno restrittiva del Cruise Terminal Handbook 2023.

## v1.1 — 2026-07-26

- PDF: testata di pagina su banda piena (contrasto corretto, prima si confondeva con lo sfondo).
- PDF: risolta la sovrapposizione dei testi nella legenda di copertina; il riquadro contenuti ora manda a capo il testo e adatta l'altezza.
- PDF: chip di provenienza compattati ([C] / [W 22.07.26] / [C+W] / [P]) con legenda estesa in copertina e in testa alla scheda.
- PDF: layout ridistribuito da 8 a 5 pagine — sommario in testa alla scheda, cartine rotta e approccio affiancate, note narrative, annotazioni waypoint e fonti su due colonne. Nessun contenuto rimosso.
- Cartina di approccio: etichette distanziate per evitare accavallamenti.
- PDF: corretto il riempimento delle bande colorate (testata pagine e copertina). Erano disegnate solo come contorno, quindi il testo chiaro finiva su fondo bianco e risultava illeggibile.
- PDF: scala tipografica razionalizzata da 12 corpi ravvicinati a 7 misure nette (15 / 11 / 10 / 9 / 8.5 / 7.5 / 7 pt); ingranditi tabella waypoint, chip di provenienza e piè di pagina.
- QA automatica: verifica del contrasto sui pixel renderizzati, oltre al controllo di sovrapposizioni e margini.

## v1.0 — 2026-07-22

- Primo porto: Haugesund (Norvegia) — scheda completa con provenienza C/W per ogni dato.
- Rotta Bergen → Haugesund: 25 waypoint (trascrizione integrale), 132.61 NM, note operative.
- Verifiche web del 22.07.2026: Kvitsøy VTS ch 19 (Nord), Havnevakt VHF 12/16, banchina 297 m, shore power 16 MVA, Askøybrua 62 m.
- Primo build dei prodotti: `output/index.html` (database interattivo con mappa) e `output/Narrative_Porti_v1.0.pdf`.
- Voce in attesa: fondale ufficiale in banchina (riferimento: carta Karmsund Havn nov 2024).

## v0.1 — 2026-07-22

- Inizializzazione della repository: struttura cartelle, README, versionamento.
