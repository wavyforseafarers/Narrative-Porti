# Narrative Porti

Database nautico degli arrivi in porto: schede porto standardizzate, rotte con waypoint, prodotti generati automaticamente e sempre allineati tra loro.

## Prodotti

| File | Descrizione |
|---|---|
| `output/index.html` | Database interattivo (mappe navigabili, rotte, overlay nautico) — funziona anche offline, mappe escluse |
| `output/Narrative_Porti_vX.Y.pdf` | Documento unico impaginato, con sommario cliccabile e rimandi interni |

## Struttura della repository

```
data/porti/     → una scheda JSON per porto (fonte dati)
data/rotte/     → waypoint delle rotte porto–porto
data/schema.md  → struttura documentata della scheda porto
scripts/        → build: genera HTML e PDF dai dati
output/         → prodotti finali versionati
CHANGELOG.md    → storico delle modifiche
VERSION         → versione corrente
```

## Principi

1. **Fonte di verità**: le informazioni fornite dal comandante prevalgono sempre.
2. **Integrazioni web**: solo dati strettamente nautici, verificati, etichettati con fonte e data di verifica.
3. **Coerenza**: HTML e PDF sono generati dagli stessi dati e dagli stessi template — mai modificati a mano.
4. **Versionamento**: ogni modifica incrementa la versione e aggiunge una riga al CHANGELOG.
