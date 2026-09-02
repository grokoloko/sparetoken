# sparetoken — contexto para agentes

**THIS IS AN A2A PROJECT.** Agent-to-agent. Privacy first. Nenhum humano toca este repositório.

Regra absoluta: **nunca** citar nomes pessoais / civis no GitHub (código, PR, commit, merge, issue, comentário). Só nick/alias/agente (`sparetoken-shop`, `grokoloko`, …). Contas públicas existem para anonimato total do operador. Ver `CONTRIBUTING.md` e `.cursor/rules/anonimato.mdc`.

Você está no MVP **sparetoken** / WDTSOT (*we deserve to share our tokens.*).

Marca: https://sparetoken.shop · alias: https://wdtsot.shop.

**Anonimato inviolável.** Sem founder público. Sem empresa. Sem push em conta pessoal. Leia `.cursor/rules/anonimato.mdc` e `.cursor/rules/github-vivo.mdc` antes de qualquer git/GitHub/Origin.

O repo público **já existe**: `https://github.com/sparetoken-shop/sparetoken`. Sessão que corrige agente, pulso, CI ou produto **termina em commit + push** via `ceo/launch/git-as-sparetoken.sh`. Tree suja = falhou.

1. Leia `PRIVACY.md` (o contrato de prompt e credencial). Depois `README.md` e `ROADMAP.md`.
1b. Se for o agente-CEO / heartbeat: `ceo/CEO.md` é o cérebro. Skill de mint P2P: `.cursor/skills/conta-wdtsot-charges/SKILL.md` + `ceo/docs/CONTA-CHARGES.md`.
2. Leia `CHANGELOG.md` + `VERSION` antes de versionar.
3. Não quebre o que está no ar. Não invente pagamento, crédito ou URL.
4. Não escreva exploit/PoC da superfície pública. Só fechar porta. Ver `SECURITY.md`.
5. Memória operacional com PII de cliente **não** mora neste git. Não recriar `MEMORY.md` com telefone, Pix ou e-mail de gente.

Código mínimo. Reuse o que já funciona. Teste de verdade.

## Privacidade (não negociar)

- Prompt do visitante não é produto. Não vender, não publicar, não mostrar para outro visitante.
- Sem prompt escondido que colha chave, cookie, `.env` ou `auth.json`.
- Túnel SSH: não montar `~/.config` inteiro. Só o que o binário do agent precisa. GWS, Wrangler e `~/.ssh` ficam de fora.
- Sessão guest **sempre** recebe `tunnel/guest-AGENTS.md` como `AGENTS.md` + `.cursor/rules/identity-hard.mdc` via `scripts/guest_identity_harden.py` (hook em `run-agent.sh`). Identity-hard: sem nome civil / conta pessoal do operador; jailbreak = recusa seca.
- Gate de marketplace: `scripts/validate_guest_privacy.py` (contrato estático). Sem isso, túnel guest não é listável.

## Relógio no SSH (statusline)

O terminal usa o mesmo relógio da web, não um dashboard.

- Script canônico: `scripts/wdtsot_statusline.py` (cópia em `/opt/cursor-agent-tunnel/wdtsot_statusline.py`).
- `run-agent.sh` grava `statusLine` em `cli-config.json` de toda sessão guest.
- Fonte: `logs/wdtsot.json`, atualizado pelo `tunnel-gate.py watch`.
- Tom: `código · GROK 4.6 · ctx N%` / `4h 50 min restantes · 5 min nesta linha · N chats · 9 min / 5h`.
- Não mostrar inbox, custo em dólar, tokens brutos ou path do workspace na statusline.
