
# News Scenario Simulator

AI agent pro novináře - analyzuje aktuální témata a simuluje jejich budoucí vývoj.

## Idea

1. **Sběr témat** - Agent získá aktuální témata z novin přes MCP (Brave Search / Exa)
2. **Výběr tématu** - Vybere téma vhodné pro simulaci budoucího vývoje
3. **Research parametrů** - Použije Perplexity a ArXiv pro získání dat a nastavení parametrů
4. **Návrh simulace** - Předloží uživateli návrh simulačního scénáře
5. **Spuštění simulace** - Po schválení spustí Mesa model v E2B sandboxu
6. **Vizualizace** - Výsledky vizualizuje pro použití na webu (Plotly/D3)

## Technologie

- **Simulační framework**: Mesa (Python agent-based modeling)
- **Execution**: E2B sandbox
- **MCP servery**: Brave Search, Perplexity, ArXiv
- **Vizualizace**: Plotly pro interaktivní grafy

## Architektura

```
News MCP → Topic Selection → Perplexity/ArXiv Research
                                      ↓
                            Parameter Extraction
                                      ↓
                         Mesa Model Generation
                                      ↓
                    User Approval → E2B Execution
                                      ↓
                         Visualization (Plotly)
```

---

## Hackathon Info

https://luma.com/0vm36r4q?tk=fMGAuu

- Submit until 22. 11. 9:00 PDT
- Requirements: E2B sandbox + MCP from Docker Hub
- Resources: https://e2bdev.notion.site/MCP-Agents-Hackathon-Resources-2a4b8c29687380e9bd64dddb5a939e5c
