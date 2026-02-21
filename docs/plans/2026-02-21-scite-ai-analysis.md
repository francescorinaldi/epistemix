# Analisi Approfondita di scite.ai — Ispirazione per Epistemix

**Data:** 21 febbraio 2026
**Obiettivo:** Studio dell'interfaccia scite.ai e raccomandazioni per il design futuro di Epistemix

---

## 1. Cos'è scite.ai

scite.ai è una piattaforma di analisi citazionale fondata nel 2019 da Josh Nicholson e Yuri Lazebnik. La sua innovazione centrale è il concetto di **Smart Citations**: invece di contare semplicemente le citazioni, scite classifica *come* ogni articolo viene citato — supportando, contestando o semplicemente menzionando un'affermazione.

**Numeri chiave:**
- Oltre 1.2 miliardi di coppie citazionali analizzate
- Oltre 187 milioni di articoli indicizzati
- Utilizzato da oltre 600 università e istituzioni di ricerca
- Integrato con Zotero, browser extension, API

**Modello di business:**
| Piano | Prezzo | Funzionalità |
|-------|--------|--------------|
| Free | $0 | Ricerca base, citation badge limitati |
| Individual | ~$12/mese | Smart Citations complete, AI assistant, export |
| Institutional | Custom | Accesso campus-wide, analytics, API |

---

## 2. Anatomia dell'Interfaccia

### 2.1 Struttura Generale

L'interfaccia di scite.ai è **estremamente minimale e istituzionale**. Segue un paradigma "search-first": l'esperienza utente ruota interamente attorno a una barra di ricerca centrale, simile a Google Scholar ma con una proposta di valore radicalmente diversa.

```
┌─────────────────────────────────────────────────────────────┐
│  Logo    Search Bar                      Sign In  │ Upgrade │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              [Search or ask a question...]                  │
│                                                             │
│     Tabs: Search | Assistant | Dashboards | Reference Check │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Risultati / Pannello Contenuto                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Le Quattro Modalità Principali

#### A. Search (Ricerca)
- Barra di ricerca unificata per DOI, titolo, argomento, autore
- Filtri laterali: anno, giornale, tipo di pubblicazione, campo disciplinare
- Risultati in lista verticale con **Smart Citation badges** integrati

#### B. Assistant (AI Research Assistant)
- Chat-like interface per domande in linguaggio naturale
- Risposte con citazioni inline cliccabili
- Ogni affermazione è tracciabile al paper sorgente
- Interfaccia pulita, sans-serif, sfondo bianco

#### C. Dashboards (Citation Dashboards)
- Vista paper-centrica: per ogni articolo mostra tutti i contesti citazionali
- Sezioni: Supporting · Contrasting · Mentioning
- Ogni contesto mostra l'estratto esatto con la citazione evidenziata
- Statistiche aggregate: totale citazioni, distribuzione per tipo

#### D. Reference Check
- Incolla un manoscritto → scite analizza tutte le referenze
- Per ogni referenza: mostra se è stata ritirata, corretta, o contestata
- Rapporto di "salute" delle referenze utilizzate

### 2.3 Smart Citation Badges

Il componente UI più iconico e riconoscibile di scite:

```
┌──────────────────────────────────┐
│  📊 Smart Citations             │
│                                  │
│  🟢 42 Supporting               │
│  🔴  3 Contrasting              │
│  ⚪ 128 Mentioning              │
│                                  │
│  Total: 173 citations            │
└──────────────────────────────────┘
```

**Principi di design dei badge:**
- **Tre colori semantici:** verde (supporting), rosso (contrasting), grigio/neutro (mentioning)
- **Numeri prominenti:** il dato numerico è l'elemento dominante
- **Compatti e inline:** appaiono direttamente nella lista risultati
- **Embeddabili:** widget che può essere inserito in siti terzi

### 2.4 Paper Detail View

Quando si apre un articolo specifico, la vista si espande in:

```
┌──────────────────────────────────────────────────────────────┐
│  TITOLO DELL'ARTICOLO                                        │
│  Autori · Giornale · Anno · DOI                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Smart Citations Summary ────┐  ┌─ Tally ─────────────┐  │
│  │  42 Supporting               │  │  ████████████░░  76% │  │
│  │   3 Contrasting              │  │  ██░░░░░░░░░░░░   2% │  │
│  │ 128 Mentioning               │  │  ████░░░░░░░░░░  22% │  │
│  └──────────────────────────────┘  └─────────────────────┘  │
│                                                              │
│  Tabs: [Supporting] [Contrasting] [Mentioning] [Self-Cites]  │
│                                                              │
│  ┌─ Citation Context ──────────────────────────────────────┐ │
│  │  "Smith et al. (2020) demonstrated that X, which        │ │
│  │   ███████████ supports ███████████ the hypothesis       │ │
│  │   proposed by [Target Paper]..."                        │ │
│  │                                                         │ │
│  │  — Source: Johnson 2021, Nature, DOI: 10.xxx            │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Citation Context ──────────────────────────────────────┐ │
│  │  "Unlike the results reported in [Target Paper],        │ │
│  │   our findings ███ contrast ███ with the claim..."      │ │
│  │                                                         │ │
│  │  — Source: Williams 2022, PNAS, DOI: 10.xxx             │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 2.5 Assistant Interface

L'Assistant è un'interfaccia conversazionale che risponde con **citazioni verificabili**:

```
┌──────────────────────────────────────────────────────────────┐
│  💬 scite Assistant                                          │
│                                                              │
│  User: "What is the evidence for neuroplasticity             │
│         in adult brains?"                                    │
│                                                              │
│  ┌─ Assistant Response ────────────────────────────────────┐ │
│  │  Research has shown significant evidence for adult       │ │
│  │  neuroplasticity. Maguire et al. (2000) [1] found that  │ │
│  │  London taxi drivers had enlarged hippocampi compared    │ │
│  │  to controls, suggesting structural changes from        │ │
│  │  spatial navigation experience. This finding has been    │ │
│  │  supported by 42 subsequent studies [1] and contrasted   │ │
│  │  by 3 studies [1]...                                    │ │
│  │                                                         │ │
│  │  [1] Maguire et al., PNAS, 2000                        │ │
│  │      🟢 42 supporting  🔴 3 contrasting                │ │
│  │  [2] Draganski et al., Nature, 2004                    │ │
│  │      🟢 89 supporting  🔴 1 contrasting                │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  [Ask a follow-up question...]                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Principi di Design di scite.ai

### 3.1 Semplicità Istituzionale

| Principio | Implementazione |
|-----------|----------------|
| **Sfondo bianco** | Nessun gradiente, nessuna texture — puro bianco con testo nero/grigio |
| **Tipografia sobria** | Sans-serif (Inter / system font), pesi leggeri per il corpo, bold solo per titoli |
| **Gerarchia cromatica ridotta** | Solo 3 colori semantici (verde, rosso, grigio) + blu per link |
| **Nessuna decorazione** | Zero illustrazioni, zero icone decorative, zero animazioni |
| **Densità informativa alta** | Molte informazioni per schermo, poco spazio vuoto decorativo |
| **UI "invisibile"** | L'interfaccia scompare — il contenuto (dati citazionali) è il protagonista |

### 3.2 Pattern di Interazione

| Pattern | Dettaglio |
|---------|-----------|
| **Search-first** | L'intera app ruota attorno alla ricerca; non c'è "dashboard" vuota |
| **Progressive disclosure** | Lista compatta → click → dettaglio espanso con contesto citazionale |
| **Inline evidence** | Le citazioni appaiono *nel contesto* del testo, non in una lista separata |
| **Zero friction** | Nessun onboarding wizard, nessun tutorial — cerchi e trovi |
| **Embeddability** | I badge sono widget standalone, utilizzabili ovunque |
| **Verifiability** | Ogni dato è cliccabile e porta alla fonte originale |

### 3.3 Palette Cromatica

```
Primario:     #FFFFFF (sfondo bianco)
Testo:        #1a1a1a (quasi-nero)
Secondario:   #666666 (grigio per metadati)
Link/Azione:  #1a73e8 (blu Google-like)
Supporting:   #34a853 (verde)
Contrasting:  #ea4335 (rosso)
Mentioning:   #9aa0a6 (grigio)
Badge BG:     #f8f9fa (grigio chiarissimo)
```

### 3.4 Tipografia

- **Titoli:** Sans-serif (Inter/system), 18-24px, weight 600
- **Corpo:** Sans-serif, 14-16px, weight 400, line-height 1.5
- **Metadati:** Sans-serif, 12-13px, weight 400, colore secondario
- **Badge numeri:** Sans-serif, 14-16px, weight 700
- **Nessun serif** — differenza netta con Epistemix

---

## 4. Confronto: scite.ai vs Epistemix

### 4.1 Filosofia di Design

| Dimensione | scite.ai | Epistemix |
|------------|----------|-----------|
| **Tema** | Light mode, bianco istituzionale | Dark mode, accademico-elegante |
| **Font** | Sans-serif puro (Inter) | Serif display + sans-serif + monospace |
| **Colori** | 3 semantici + 1 azione | Palette ricca con gold accent |
| **Complessità** | Minimale, quasi spartana | Sofisticata, con data viz elaborate |
| **Entry point** | Barra di ricerca | Dashboard con lista audit |
| **Densità** | Alta (molta info, poco decoro) | Media (bilancia info e estetica) |
| **Animazioni** | Quasi zero | Pulse, fade-in, transizioni |
| **Target** | Ricercatore individuale | Revisore epistemico / team |

### 4.2 Componenti a Confronto

| Componente | scite.ai | Epistemix |
|------------|----------|-----------|
| **Indicatore chiave** | Citation Badge (S/C/M) | Coverage % + Anomaly count |
| **Visualizzazione** | Barre percentuali semplici | Recharts line chart + D3 force graph |
| **Lista risultati** | Card compatte con badge inline | Card con status badge e stats row |
| **Dettaglio** | Contesto citazionale con highlight | Cycle timeline + chart panel |
| **AI Integration** | Chat assistant con inline citations | Dual-agent audit con blindness gauge |
| **Navigation** | Tabs orizzontali, flat | Pagine separate con back-link |

### 4.3 Punti di Forza di scite.ai da Emulare

1. **Immediatezza**: l'utente trova valore in <3 secondi (cerca → vede badge)
2. **Credential-free start**: puoi cercare senza login
3. **Embeddable widgets**: i badge vivono fuori dalla piattaforma
4. **Citazione come unità atomica**: ogni dato è verificabile fino alla frase sorgente
5. **Densità senza caos**: molto contenuto, zero rumore visivo

### 4.4 Punti di Forza di Epistemix da Preservare

1. **Estetica distintiva**: il dark theme con Cormorant Garamond è memorabile
2. **Narrazione visiva**: il CycleTimeline racconta una storia, non solo dati
3. **Multi-agent transparency**: il BlindnessGauge è unico nel panorama
4. **Data visualization ricca**: il CitationGraph in D3 è potente
5. **Real-time updates**: l'esperienza "live audit" è coinvolgente

---

## 5. Raccomandazioni per Epistemix

### 5.1 Adozioni Immediate (Quick Wins)

#### R1: Introdurre un "Epistemic Badge" Embeddabile

Ispirato ai Smart Citation Badges di scite, creare un badge Epistemix che sintetizzi il risultato di un audit:

```
┌──────────────────────────────────────────┐
│  ε Epistemic Audit                       │
│                                          │
│  Coverage:  72%  accessible              │
│  Gaps:       4   anomalies detected      │
│  Languages:  3/7 expected                │
│  Agents:    α 72% · β 58% (Δ14%)        │
│                                          │
│  Topic: Amphipolis tomb excavation       │
│  Last updated: Feb 2026                  │
└──────────────────────────────────────────┘
```

**Perché:** Un badge embeddabile è un moltiplicatore virale. Un ricercatore potrebbe inserirlo nel proprio sito, in un paper supplementare, o in una proposta di finanziamento. È la versione "scite badge" per l'audit epistemico.

**Implementazione:** Componente React standalone + endpoint API che restituisce HTML/SVG per embedding.

#### R2: Aggiungere una Search/Query Page Pubblica

Come scite.ai permette di cercare senza login, Epistemix dovrebbe avere una pagina pubblica dove:
- L'utente inserisce un topic + country + discipline
- Vede un'anteprima di quali meta-assiomi si applicherebbero
- Vede una stima di quanti cicli servirebbero
- **Call to action:** "Run full audit" → porta al login

```
┌──────────────────────────────────────────────────────────────┐
│  ε                                                           │
│                                                              │
│  What should we know about...                                │
│                                                              │
│  [Topic: e.g., Amphipolis tomb excavation              ]     │
│  [Country: e.g., Greece                                ]     │
│  [Discipline: e.g., archaeology                        ]     │
│                                                              │
│  [Preview Audit →]                                           │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Preview:                                                    │
│  ✓ MA-01 Linguistic Diversity — expected: el, en, de, fr, it │
│  ✓ MA-02 Institutional Multiplicity — likely 5+ institutions │
│  ✓ MA-05 Disciplinary Breadth — archaeology, art history,    │
│           conservation, epigraphy                            │
│  ✓ MA-08 Access Barriers — JSTOR, Academia.edu               │
│                                                              │
│  Estimated: 4 cycles · ~15 minutes · $2.40 API cost         │
│                                                              │
│  [Run Full Audit — Sign In Required]                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Perché:** Riduce la friction all'ingresso. L'utente capisce il valore *prima* di creare un account. Questo è il pattern che ha reso Google Scholar e scite.ai virali nel mondo accademico.

#### R3: Citation Context Inline nel Pannello Anomalie

Come scite mostra il *contesto esatto* di ogni citazione, Epistemix dovrebbe mostrare l'*evidenza esatta* di ogni anomalia:

Attualmente l'AnomalyPanel mostra:
```
⚠ Missing linguistic coverage
  Expected: French, Italian, Arabic
  Suggested queries: [fr] "fouilles Amphipolis"
```

Con il pattern scite, diventerebbe:
```
⚠ Missing linguistic coverage
  Expected: French, Italian, Arabic
  
  Evidence:
  "Kasta tomb excavation directed by Peristeri (2012-2014) 
   was extensively covered in Greek media but NO French or 
   Italian scholarly publication was found in Cycle 1-2."
   — Cycle 2, MA-01 analysis
   
  Suggested queries: [fr] "fouilles Amphipolis Kasta"
```

**Perché:** La verificabilità è il valore #1 sia per scite che per Epistemix. Mostrare *perché* un'anomalia è stata rilevata, con la citazione esatta dal processo di audit, aumenta enormemente la credibilità.

### 5.2 Adozioni a Medio Termine

#### R4: Light Mode Istituzionale (Opzionale)

scite.ai dimostra che il mondo accademico preferisce interfacce chiare e sobrie. Aggiungere un **light mode opzionale** renderebbe Epistemix più accessibile in contesti istituzionali:

```css
/* Light mode variant */
:root[data-theme="light"] {
  --bg-page: #ffffff;
  --bg-card: #f8f9fa;
  --bg-elevated: #ffffff;
  --text-heading: #1a1a1a;
  --text-primary: #333333;
  --text-secondary: #666666;
  --accent: #2c5282;           /* Blu accademico al posto dell'oro */
  --border-default: #e2e8f0;
}
```

**Perché:** Molte università hanno requisiti di accessibilità (WCAG AA) che il dark mode rende più difficili da soddisfare. Un light mode non toglie nulla all'identità di Epistemix, ma apre il mercato istituzionale. Il toggle potrebbe essere un semplice switch nell'header.

#### R5: Navigazione a Tabs (come scite)

scite usa tabs orizzontali per passare tra Search, Assistant, Dashboards, Reference Check. Epistemix potrebbe adottare un pattern simile nella pagina audit:

```
[Overview] [Findings] [Anomalies] [Citation Graph] [Agent Analysis]
```

Al posto dell'attuale layout a due colonne che mostra tutto simultaneamente.

**Perché:** Su schermi piccoli e tablet (comuni in biblioteche universitarie), il layout attuale è compresso. I tabs permettono di dare a ogni sezione lo spazio necessario senza scrolling infinito.

#### R6: Tabella Findings Strutturata

Come scite presenta i risultati in una lista densa ma leggibile, creare un componente `FindingsTable` che mostri i findings in formato tabulare:

```
┌─────────────────────────────────────────────────────────────┐
│  Source              │ Author    │ Lang │ School │ Status   │
├─────────────────────────────────────────────────────────────┤
│  Annual Review of    │ Peristeri │ en   │ α      │ verified │
│  Archaeology         │           │      │        │          │
├─────────────────────────────────────────────────────────────┤
│  Archéologie du      │ Lequèvre  │ fr   │ β      │ new      │
│  Monde Grec          │           │      │        │          │
├─────────────────────────────────────────────────────────────┤
│  考古学研究           │ 田中       │ ja   │ —      │ barrier  │
│                      │           │      │        │          │
└─────────────────────────────────────────────────────────────┘

  Showing 12 of 47 findings · Filter: [All ▾] [Language ▾] [School ▾]
```

**Perché:** L'attuale AnomalyPanel è ottimo per le anomalie, ma i findings individuali non hanno una vista dedicata e navigabile. Una tabella con sorting e filtering è il formato più familiare per i ricercatori (è come leggere un database bibliografico).

### 5.3 Adozioni Strategiche (Lungo Termine)

#### R7: API Pubblica con Documentazione Interattiva

scite.ai offre un'API REST pubblica per integrazioni. Epistemix dovrebbe esporre un'API documentata con Swagger/OpenAPI:

```
GET  /api/v1/audits/:id/badge      → SVG badge embeddabile
GET  /api/v1/audits/:id/summary    → JSON summary (coverage, anomalies)
GET  /api/v1/audits/:id/findings   → Lista findings paginata
GET  /api/v1/audits/:id/graph      → Grafo citazionale in formato JSON
POST /api/v1/audits                → Avvia nuovo audit
```

**Perché:** L'API è il meccanismo che ha permesso a scite.ai di integrarsi con Zotero, Mendeley, e browser extensions. Per Epistemix, l'API aprirebbe integrazioni con:
- **Zotero plugin**: audit epistemico di una collezione bibliografica
- **Browser extension**: badge Epistemix accanto a ogni paper su Google Scholar
- **LMS integration**: inserire audit in piattaforme didattiche universitarie

#### R8: Browser Extension (come scite)

scite ha un'estensione browser che aggiunge badge citazionali ovunque appaia un DOI. Epistemix potrebbe creare un'estensione che:
- Detecta topic/discipline nella pagina corrente
- Mostra se esiste un audit Epistemix per quel topic
- Offre un quick-start per avviare un audit

#### R9: Reference Audit (ispirato a Reference Check)

Come scite analizza le referenze di un manoscritto, Epistemix potrebbe offrire un "Reference Audit":
- L'utente carica un PDF o incolla una lista di referenze
- Epistemix verifica la copertura linguistica e disciplinare delle fonti
- Genera un report: "Le tue 45 referenze sono tutte in inglese. Per questo topic, ci si aspetterebbero fonti in francese (scavi) e greco (archivi locali)"

**Perché:** Questo è il use case più diretto per il mondo accademico — un ricercatore che sta scrivendo un paper e vuole verificare di non avere blind spots nella propria bibliografia.

---

## 6. Principi di Design da Adottare

### 6.1 Il Framework "CIVIC" (ispirato a scite.ai)

| Principio | Significato | Applicazione in Epistemix |
|-----------|-------------|---------------------------|
| **C**lear | Nessuna ambiguità visiva | Un colore = un significato, sempre |
| **I**mmediate | Valore in <3 secondi | Badge/summary prima di tutto |
| **V**erifiable | Ogni dato è cliccabile | Link finding → fonte → contesto |
| **I**nstitutional | Appare affidabile per un rettore | Light mode, tipografia sobria |
| **C**ompact | Massima info, minimo spazio | Tabelle dense, badge inline |

### 6.2 Regole Specifiche

1. **Ogni numero deve avere un'etichetta** — mai un numero isolato senza contesto
2. **Ogni anomalia deve avere evidenza** — non solo "missing X", ma "missing X because Y"
3. **Ogni azione deve avere una preview** — prima di avviare un audit, mostra cosa aspettarsi
4. **Il badge è il prodotto** — se il badge è buono, il prodotto si vende da solo
5. **Light mode per i PDF** — quando un audit viene esportato in PDF, il light mode è obbligatorio

---

## 7. Mockup Proposti

### 7.1 Nuova Homepage (ispirata a scite search-first)

```
┌──────────────────────────────────────────────────────────────┐
│  ε Epistemix                         [Sign In] [Learn More]  │
│                                                              │
│                                                              │
│          Discover what your research is missing              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  🔍 Enter a research topic...                          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Examples:                                                   │
│  • Amphipolis tomb excavation, Greece, archaeology           │
│  • CRISPR gene therapy, USA, molecular biology               │
│  • Antikythera mechanism, Greece, history of science         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  How it works:                                               │
│                                                              │
│  1. Predict          2. Search           3. Detect           │
│  What knowledge      Multilingual,       Unknown unknowns,   │
│  should exist        multi-source        blind spots          │
│                                                              │
│  ┌── Live Example ─────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  ε Antikythera Mechanism — Epistemic Audit              │ │
│  │                                                         │ │
│  │  Coverage:  78%  │  Gaps: 6   │  Languages: 5/7        │ │
│  │  Agents: α 82% · β 71%  │  Δ: 11%                     │ │
│  │                                                         │ │
│  │  ⚠ Missing: French excavation reports                  │ │
│  │  ⚠ Missing: Arabic astronomical traditions             │ │
│  │  ⚠ Missing: Italian conservation school                │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 Audit Badge Embeddabile

```html
<!-- Embed code (come scite badge) -->
<div class="epistemix-badge" data-audit-id="abc123"></div>
<script src="https://epistemix.app/badge.js"></script>
```

Badge rendering:
```
┌────────────────────────────────┐
│  ε Epistemic Audit             │
│                                │
│   72%    4 gaps   3/7 langs    │
│  coverage  found   covered     │
│                                │
│  Amphipolis · Feb 2026         │
│  [View Full Report →]          │
└────────────────────────────────┘
```

### 7.3 Findings Table (ispirata a scite results list)

```
┌──────────────────────────────────────────────────────────────┐
│  📋 Findings (47)                    Filter ▾  Sort ▾  Export│
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Finding ─────────────────────────────────────────────┐   │
│  │  📄 "Amphipolis Excavation: Architecture of Power"    │   │
│  │  Peristeri, K. · Annual Review of Archaeology · 2014  │   │
│  │  🏛 en · Aristotle University · School α              │   │
│  │                                                       │   │
│  │  Context: "The Kasta tomb represents the largest      │   │
│  │  burial monument discovered in Greece, dated to       │   │
│  │  the 4th century BCE..."                              │   │
│  │                                                       │   │
│  │  Relations: supports 3 · contested by 1               │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ Finding ─────────────────────────────────────────────┐   │
│  │  📄 "Fouilles d'Amphipolis: Nouvelles perspectives"   │   │
│  │  Lequèvre, M. · Archéologie du Monde Grec · 2019     │   │
│  │  🇫🇷 fr · Sorbonne · School β                        │   │
│  │                                                       │   │
│  │  Context: "Contrairement à l'hypothèse de Peristeri, │   │
│  │  les dimensions du tombeau ne justifient pas..."      │   │
│  │                                                       │   │
│  │  Relations: contests 1 · supports 1                   │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 8. Prioritizzazione

### Matrice Impatto / Effort

| Raccomandazione | Impatto | Effort | Priorità |
|----------------|---------|--------|----------|
| R1: Epistemic Badge | 🟢 Alto | 🟢 Basso | **P1** |
| R2: Search Page Pubblica | 🟢 Alto | 🟡 Medio | **P1** |
| R3: Evidence Inline | 🟡 Medio | 🟢 Basso | **P2** |
| R4: Light Mode | 🟡 Medio | 🟡 Medio | **P2** |
| R5: Tab Navigation | 🟡 Medio | 🟢 Basso | **P2** |
| R6: Findings Table | 🟡 Medio | 🟡 Medio | **P3** |
| R7: API Pubblica | 🟢 Alto | 🔴 Alto | **P3** |
| R8: Browser Extension | 🟢 Alto | 🔴 Alto | **P4** |
| R9: Reference Audit | 🟢 Alto | 🔴 Alto | **P4** |

### Roadmap Suggerita

**Sprint 1 (2 settimane):**
- R1: Epistemic Badge component + API endpoint
- R5: Tab navigation nella pagina audit

**Sprint 2 (2 settimane):**
- R2: Search page pubblica (anteprima senza login)
- R3: Evidence inline nell'AnomalyPanel

**Sprint 3 (3 settimane):**
- R4: Light mode con CSS variables toggle
- R6: FindingsTable component con sorting/filtering

**Sprint 4+ (ongoing):**
- R7: API pubblica con OpenAPI docs
- R8-R9: Estensioni e features avanzate

---

## 9. Conclusioni

### Cosa Imparare da scite.ai

1. **La semplicità è un vantaggio competitivo.** scite ha vinto nel mercato accademico non perché fa tutto, ma perché fa *una cosa* (Smart Citations) in modo immediatamente comprensibile.

2. **Il badge è il prodotto.** La visualizzazione compatta e embeddabile è ciò che rende scite virale. Epistemix ha bisogno del suo equivalente.

3. **Search-first, not dashboard-first.** Gli accademici non vogliono una dashboard da popolare — vogliono una risposta immediata a una domanda.

4. **La verificabilità è non-negoziabile.** Ogni claim deve essere tracciabile alla fonte. Questo è il DNA condiviso di scite e Epistemix.

5. **Light mode per il mondo istituzionale.** Le università, i dipartimenti, i comitati di finanziamento — tutti operano su schermi luminosi con documenti bianchi. Il dark mode è bello, ma il light mode è necessario.

### Cosa NON Copiare da scite.ai

1. **Non abbandonare il dark mode.** È l'identità di Epistemix. Aggiungere light mode, non sostituire.
2. **Non semplificare troppo.** Epistemix è più complesso di scite — multi-agent, multi-lingua, anomaly detection — e questa complessità è il suo valore. Il trucco è nasconderla progressivamente (progressive disclosure).
3. **Non rinunciare alla narrazione.** Il CycleTimeline è storytelling, non solo data display. scite è un database, Epistemix è un detective.

### L'Insight Strategico

scite.ai e Epistemix sono **complementari, non competitivi**:
- scite dice "come è stato citato questo paper?"
- Epistemix dice "cosa non stiamo cercando affatto?"

scite opera **dentro** la letteratura esistente. Epistemix opera **sui bordi** — dove la letteratura finisce e l'ignoto inizia. Questa è la differenza fondamentale, e l'interfaccia deve rifletterla.

La proposta di valore di Epistemix non è "sapere di più" ma "sapere cosa non sai". E l'interfaccia dovrebbe rendere questo concetto — l'assenza come informazione — il suo elemento visivo più potente.

---

*Documento preparato come parte dell'analisi competitiva per il design v0.3.0 di Epistemix.*
