# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate qui.
Formato versione: `vMAJOR.MINOR` — MINOR per aggiunte/modifiche ai dati, MAJOR per cambi di struttura.

## v1.1 — 2026-07-26

- PDF: testata di pagina su banda piena (contrasto corretto, prima si confondeva con lo sfondo).
- PDF: risolta la sovrapposizione dei testi nella legenda di copertina; il riquadro contenuti ora manda a capo il testo e adatta l'altezza.
- PDF: chip di provenienza compattati ([C] / [W 22.07.26] / [C+W] / [P]) con legenda estesa in copertina e in testa alla scheda.
- PDF: layout ridistribuito da 8 a 5 pagine — sommario in testa alla scheda, cartine rotta e approccio affiancate, note narrative, annotazioni waypoint e fonti su due colonne. Nessun contenuto rimosso.
- Cartina di approccio: etichette distanziate per evitare accavallamenti.

## v1.0 — 2026-07-22

- Primo porto: Haugesund (Norvegia) — scheda completa con provenienza C/W per ogni dato.
- Rotta Bergen → Haugesund: 25 waypoint (trascrizione integrale), 132.61 NM, note operative.
- Verifiche web del 22.07.2026: Kvitsøy VTS ch 19 (Nord), Havnevakt VHF 12/16, banchina 297 m, shore power 16 MVA, Askøybrua 62 m.
- Primo build dei prodotti: `output/index.html` (database interattivo con mappa) e `output/Narrative_Porti_v1.0.pdf`.
- Voce in attesa: fondale ufficiale in banchina (riferimento: carta Karmsund Havn nov 2024).

## v0.1 — 2026-07-22

- Inizializzazione della repository: struttura cartelle, README, versionamento.
