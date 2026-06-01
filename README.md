# Prize Distribution — PySide6

Not so basic manger to add your distribution prizes, players damage and check your previus records!

---

## Struttura del progetto

```
prize_app/
├── main.py                       ← punto di avvio
├── preferences.json              ← generato al primo avvio
│
├── locales/                      ← un file JSON per lingua (auto-detect)
│   ├── it.json  (316 chiavi)     ← Italiano
│   ├── en.json  (316 chiavi)     ← English
│   ├── fr.json  (316 chiavi)     ← Français
│   └── ru.json  (316 chiavi)     ← Русский
│
├── models/                       ← dataclass puri, nessuna dipendenza UI
│   ├── date_range.py
│   ├── participant.py
│   ├── prize.py
│   └── saved_state.py
│
├── core/                         ← logica di business
│   ├── translations.py           ← TranslationManager con autodetect locale
│   ├── distribution.py           ← DistributionEngine (fix bug + min 1)
│   ├── state_manager.py          ← save/load/backup/export/import
│   └── preferences.py
│
└── ui/
    ├── theme.py                  ← palette dark/light + QSS completo
    ├── widgets.py                ← SortableTable + helper condivisi
    ├── main_window.py            ← QMainWindow con tutte le funzioni
    ├── tabs/
    │   ├── prizes_tab.py
    │   ├── participants_tab.py
    │   ├── distribution_tab.py
    │   └── history_tab.py
    └── dialogs/
        ├── credits_dialog.py
        └── settings_dialog.py
```

---

## Installazione e avvio

```bash
pip install PySide6
cd prize_distribution
python main.py
```

Python ≥ 3.10 richiesto.

---

## Funzionalità

| Feature | Note |
|---|---|
| Premi (normale + speciale) | Aggiunta singola e batch (`nome:qty[:s:vincitori]`) |
| Partecipanti | Form con checkbox "Abilitato" + batch + toggle riga |
| Distribuzione | Ricalcolo auto al cambio tab, "Ricevuto" per riga |
| Storico | Albero anno/mese, filtri, dettaglio, carica template |
| **Carica Template** | Carica solo premi o solo partecipanti da uno stato storico |
| **Ordinamento colonne** | Click su intestazione su tutte le tabelle (esclude colonne azione) |
| **Selezione giorno** | Combo start_day / end_day con popolo dinamico per anno+mese |
| **Font size con preview** | Slider 8–16pt nelle impostazioni con anteprima live |
| **Import impostazioni** | Carica preferences.json da file, con rollback su errore |
| **Anteprima backup** | Selezionando un backup mostra conteggio e primi 3 elementi |
| **Auto-refresh distribuzione** | Aggiornamento automatico al cambio verso il tab Distribuzione |
| **Crediti** | Bottone in header → popup con sviluppatore, GitHub, BTC/LTC |
| Tema chiaro/scuro | Toggle in header + dialog impostazioni |
| 4 lingue | IT/EN/FR/RU; aggiungere `locales/de.json` per il tedesco |
| Log con `[lingua]` | Formato: `datetime - [it] - INFO - messaggio` |
| Auto-backup | Timer configurabile in minuti con retention |
| Export/Import JSON | Da dialog impostazioni |

---

## Algoritmo distribuzione (bug fix originale)

**Problema originale:** `round()` causava 0 unità ai partecipanti con < 0.5 di quota
esatta (es. 0.1% di 100 item → 0.1 → arrotondato a 0).

**Intent del progetto:** ogni partecipante non escluso deve ricevere **almeno 1** unità.

**Soluzione (Case A — item ≥ partecipanti):**
1. Riserva 1 unità garantita per ogni partecipante.
2. Distribuisce le unità rimanenti con il **Largest Remainder Method** (Hamilton):
   floor delle quote proporzionali, poi +1 ai resti frazionari più grandi.
3. Somma finale == totale esatto, ogni partecipante riceve ≥ 1.

**Case B (item < partecipanti):** non ci sono abbastanza unità per tutti —
algoritmo Hamilton puro, alcuni ricevono 0 (inevitabile e matematicamente equo).

---

## Aggiungere una nuova lingua

1. Copia `locales/en.json` → `locales/de.json`
2. Traduci tutti i valori
3. Riavvia: la lingua compare automaticamente nel selettore

Nessuna modifica al codice.
