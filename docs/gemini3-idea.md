# Gemini 3.0 Idea: MCP-First Agentic Transpiler (n8n -> Python)

## Koncept
Vytvoříme agenta, který využívá **Model Context Protocol (MCP)** k překladu n8n workflows do standalone Python agentů. Místo statického parsování JSONu a generování `requests` kódu využijeme specializované MCP servery pro pochopení zdroje (n8n) a generování cíle (PicaOS).

## Architektura: "The MCP Bridge"

### 1. Zdroj: n8n-mcp (Understanding)
*   **Nástroj:** [n8n-mcp](https://github.com/czlonkowski/n8n-mcp)
*   **Role:** Místo abychom hádali logiku z JSON exportu, agent se připojí k běžící n8n instanci přes MCP.
*   **Výhoda:** Může si "osahat" konfiguraci nodů, získat schémata a pochopit tok dat v kontextu živé instance.

### 2. Cíl: PicaOS / Pica MCP (Implementation)
*   **Nástroj:** [PicaOS](https://docs.picaos.com/get-started) & [Pica MCP](https://hub.docker.com/mcp/server/pica/overview)
*   **Role:** PicaOS řeší nejtěžší část psaní agentů - **autentizaci a integrace**.
*   **Strategie:** Agent nebude generovat složitý OAuth kód pro Google/Slack/atd. Místo toho vygeneruje kód, který využívá PicaOS SDK (nebo volá Pica MCP tools).

### 3. Exekuce: E2B (The Crucible)
*   **Role:** Bezpečné prostředí pro běh a testování vygenerovaného agenta.
*   **Iterace:** Agent v E2B zkouší kód spustit. Díky PicaOS odpadá většina chyb spojených s autentizací.

---

## Obecná Konverzní Pipeline

Proces transformace n8n workflow na Python agenta má 4 hlavní fáze:

1.  **Analýza (Understanding Phase)**
    *   **Input:** n8n Workflow ID / JSON.
    *   **Action:** Agent se přes `n8n-mcp` dotazuje na strukturu workflow. Identifikuje spouštěče (Triggers), akce (Nodes) a tok dat (Connections).
    *   **Output:** "Intent Graph" - abstraktní popis toho, co workflow *dělá* (např. "Když přijde email, ulož přílohu na Drive").

2.  **Strategie (Mapping Phase)**
    *   **Action:** Rozhodnutí, jaké knihovny použít.
    *   *S PicaOS:* Mapování n8n nodů na PicaOS Tools (`n8n:Gmail` -> `pica:google.gmail`).
    *   *Bez PicaOS:* Výběr Python knihoven (`google-api-python-client`, `slack-sdk`).

3.  **Generace (Coding Phase)**
    *   **Action:** LLM píše Python kód.
    *   Vytváří se struktura: `setup()` (auth), `main()` (logika), `handlers()` (akce).

4.  **Verifikace (The Crucible Phase)**
    *   **Action:** Spuštění v E2B Sandboxu.
    *   **Loop:** Pokud nastane chyba (Runtime Error, API Error), agent analyzuje stderr, upraví kód a zkusí to znovu.

---

## Alternativa: "Hard Mode" (Bez PicaOS)

Pokud bychom nepoužili PicaOS, agent by musel řešit **Integration Hell**:

*   **Autentizace:** Musel by generovat kód pro OAuth2 flow (Flask server pro callback, ukládání tokenů, refresh tokenů). To je extrémně náchylné k chybám.
*   **API Klienti:** Musel by znát a správně implementovat stovky různých API (Slack API vs Discord API vs Google API).
*   **Údržba:** Když Google změní API, vygenerovaný kód přestane fungovat. PicaOS/MCP toto abstrahuje.

**Závěr:** Bez PicaOS je šance na vygenerování funkčního, robustního agenta řádově nižší.

---

## Proč Python v E2B místo n8n?

Proč vůbec převádět funkční n8n workflow do Pythonu?

1.  **Cena a Efektivita:**
    *   n8n (zejména cloud) může být drahé pro high-volume tasky.
    *   Python skript v E2B (nebo Lambda/Serverless) běží jen zlomek vteřiny a platíte jen za compute time.

2.  **Verze a Testování (Code is Law):**
    *   Python kód lze verzovat v Gitu, dělat Code Review, psát Unit Testy.
    *   Vizuální workflow se špatně diffují a testují.

3.  **Flexibilita a Ekosystém:**
    *   V Pythonu máte přístup k celému PyPI (AI knihovny, data science, numpy/pandas).
    *   V n8n jste omezeni na existující nody nebo psaní JS snippetů.

4.  **Portabilita (Vendor Lock-in):**
    *   Standalone Python skript běží kdekoli (Docker, Kubernetes, Laptop, Raspberry Pi).
    *   Nejste závislí na běhu n8n serveru.
