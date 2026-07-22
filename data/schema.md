# Schema dati — Narrative Porti

Ogni porto è un file JSON in `data/porti/`, ogni rotta un file JSON in `data/rotte/`.
I prodotti (`output/index.html` e il PDF) sono generati esclusivamente da questi file
tramite `scripts/build.py`. Non modificare mai i prodotti a mano.

## Provenienza dei dati (`fonte`)

| Codice | Significato |
|---|---|
| `C`  | Comandante — fonte di verità, prevale sempre |
| `W`  | Web — solo dati nautici, verificati; ogni voce indica la data di verifica |
| `CW` | Fornito dal comandante e confermato da fonte ufficiale |
| `P`  | In attesa di conferma ufficiale |

## Porto (`data/porti/<id>.json`)

- `id`, `nome`, `paese`, `regione`
- `banchina_principale` — nome della banchina di riferimento
- `posizione` — `{ testo (formato bordo), lat, lon }` (lat/lon decimali calcolati dal testo)
- `sezioni[]` — sezioni della scheda, ognuna `{ titolo, voci[] }`
  - voce: `{ t (etichetta), v (valore), fonte, nota?, verificato? (data per W) }`
- `avvicinamento` — `{ vento, sequenza[] }`
  - passo: `{ wp (n° waypoint o null), nome, azione, tipo }`
  - `tipo` ∈ `vts | limite | velocita | manning | manovra | ormeggio | punto`
- `note_narrative[]` — testo libero del comandante, riportato integralmente
- `fonti[]` — `{ label, url, verificato }`
- `versione_scheda`, `aggiornato`

## Rotta (`data/rotte/<da>_<a>.json`)

- `id`, `da`, `a`, `titolo`, `distanza_nm`, `tipo_tratte` (RL = lossodromia)
- `waypoints[]` — trascrizione integrale della tabella di bordo:
  `{ n, nome, raggio_nm, lat_txt, lon_txt, bww, dist_enr, dist, sail, nota? }`
  Le coordinate testuali (formato `62°06.841' N`) sono la fonte; i decimali
  vengono calcolati in build.
- `note[]` — annotazioni di rotta `{ testo, fonte, verificato? }`

## Convenzioni

- Coordinate: gradi e primi decimali, come a bordo (`59°24.691' N | 005°15.309' E`).
- Toponimi: grafia norvegese normalizzata (es. Kråkeflua); i nomi originali della
  tabella di bordo restano verbatim nella tabella waypoint.
- Ogni modifica ai dati incrementa `VERSION` e aggiunge una riga a `CHANGELOG.md`.
