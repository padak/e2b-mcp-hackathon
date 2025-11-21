# High level cíl

Chci vyvinout systém, který konvertuje n8n workflows do Claude Code agentů běžících v E2B. 

## Princip

Zadáš mu JSON s n8n workflow a on z něj udělá Python kód, který dělá to stejné co n8n.

## Duvod

1. líp se to verzuje
2. líp se to rozvíjí
3. líp se to integruje s okolím
4. nejsi závislý na modulech n8n
5. nejsi závislý na n8n cloudu nebo správě n8n na tvé infrastruktuře
6. je to mnohem chytřejší (protože real agenti, python, E2B)

## Detail nápadu

Vysvětlení n8n workflow: https://github.com/czlonkowski/n8n-mcp
(tohle když napojíme do e2b (https://e2b.dev/docs/mcp/custom-servers) tak bysme mohli interpretovat ty n8n workflows

Napojení agenta na okolní svět můžeme zkusit udělat přes PICA (https://www.picaos.com/), který má MCP v Dockeru (https://hub.docker.com/mcp/server/pica/overview) a tím splníme podmínky hackathonu. 

Možná bysme pomocí Pica mohli vytahat nějaký info na napsat stand-alone kód v E2B na ty integrace. Ale máme 1 den a nekomplikoval bych to (https://docs.picaos.com/get-started).

V Dockeru je taky Perplexity MCP - to bysme mohli používat na init research pro agenta.


# Hackathon

https://luma.com/0vm36r4q?tk=fMGAuu

## Info

3. ​To qualify for winners, you need to submit a functioning code, a demo shorter than 2 minutes, and need to be using E2B sandbox, and at least one MCP from the Docker Hub
4. ​Judges evaluate technical quality, innovation factor, and overall impression of your solution. To ensure fair evaluation, judges are developers, founders, and technical experts across companies.
5. ​⏭ Submit online solution until 22. 11. 9:00 PDT
7. ​🚨 Submissions before start or after end of the hackathon don't count. You can only submit one project, and only choose one track (online, or offline).
8. ⚒️ To win, you need to use: 
   1. E2B sandbox
   2. At least one MCP from the Docker Hub inside the E2B sandbox
9. To get inspired, see: examples, resources and the quickstart (https://e2bdev.notion.site/MCP-Agents-Hackathon-Resources-2a4b8c29687380e9bd64dddb5a939e5c).
11. ​🚨 If needing technical support, join E2B Discord



# Existing solutions

https://n8n2py.me/
https://github.com/francofuji/n8n-to-python-transpiler
