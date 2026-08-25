# <img src="https://flagcdn.com/24x18/cn.png" alt="🇨🇳" width="24"> cli-jinping — FantaAsta CLI

CLI interattiva per gestire l'asta del fantacalcio, con dashboard live in tempo reale.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![SQLite](https://img.shields.io/badge/database-SQLite-green)
![Streamlit](https://img.shields.io/badge/dashboard-Streamlit-red)

## Cos'è

Un tool da terminale per condurre l'asta del fantacalcio in modo rapido e ordinato. Gestisce budget, limiti di ruolo, acquisti e annullamenti, con autocompletamento intelligente sui nomi dei calciatori.

In parallelo, una dashboard Streamlit mostra lo stato dell'asta in tempo reale su un secondo schermo — perfetta per proiettarla durante l'asta dal vivo.

## Funzionalità

- **Autocompletamento** su nomi giocatori e squadre (TAB)
- **Controlli automatici**: budget, limiti di ruolo (3P/8D/8C/6A), acquisti duplicati
- **Dashboard live** con refresh ogni 2 secondi, griglia 12 squadre, ticker ultimo acquisto
- **Undo/Remove/Move**: correggi errori al volo
- **Export** in formato CSV compatibile con app desktop fantacalcio
- **Backup/Restore/Reset**: gestione completa del ciclo di vita dell'asta
- **Import listone** da file Excel (.xlsx) con conversione automatica

## Requisiti

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (consigliato per gestire il venv)

## Installazione

```bash
# Clona il repository
git clone <url-repo>
cd cli-jinping-main

# Crea il virtual environment e installa le dipendenze
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# oppure: source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

## Preparazione del listone

Converti il file Excel con l'elenco dei calciatori in CSV:

```bash
python convert.py "nome_file_calciatori.xlsx"
```

Questo produce `listone.csv` con header che verrà importato automaticamente al primo `setup`.

## Avvio

### Solo CLI

```bash
python fantaasta_cli.py
```

### CLI + Dashboard (Windows)

```batch
start_all.bat
```

### Solo Dashboard

```bash
streamlit run dashboard.py
```

## Comandi

| Comando | Descrizione |
|---------|-------------|
| `setup` | Configura budget e squadre (reimporta il listone) |
| `buy "Giocatore" "Squadra" Prezzo` | Acquista un giocatore |
| `price "Giocatore" Prezzo ["Squadra"]` | Modifica il prezzo di un acquisto |
| `move "Giocatore" "NuovaSquadra"` | Sposta un giocatore a un'altra squadra |
| `remove "Giocatore" ["Squadra"]` | Rimuove un acquisto |
| `status` | Budget e giocatori per squadra |
| `recap_roles` | Giocatori acquistati divisi per ruolo |
| `recap_budget` | Spesa per reparto (valore e %) |
| `roster "Squadra"` | Rosa completa di una squadra |
| `undo` | Annulla l'ultimo acquisto |
| `export [file.csv]` | Esporta per app desktop |
| `backup [file.db]` | Salvataggio manuale del database |
| `reset` | Azzera l'asta (con backup automatico) |
| `restore file.db` | Ripristina da un backup |
| `exit` | Chiude l'applicazione |

## Architettura

```
fantaasta_cli.py   → Interfaccia utente (prompt_toolkit + rich)
database.py        → Persistenza SQLite (WAL mode, transazioni atomiche)
completer.py       → Autocompletamento contestuale
dashboard.py       → Dashboard Streamlit real-time
convert.py         → Conversione xlsx → csv del listone
```

Il database SQLite usa WAL mode per permettere letture concorrenti dalla dashboard mentre la CLI scrive. Le query della dashboard sono ottimizzate con aggregazioni batch (3 query totali per refresh, ~0.25ms).

## Struttura del listone CSV

Il file `listone.csv` deve avere un header con almeno queste colonne (i nomi sono flessibili):

| Campo | Nomi accettati |
|-------|---------------|
| ID | `#`, `id`, `cod`, `codice` |
| Nome | `nome`, `name`, `giocatore` |
| Squadra | `sq.`, `sq`, `squadra`, `team` |
| Ruolo | `r.`, `r`, `ruolo`, `role` |

## License

MIT
