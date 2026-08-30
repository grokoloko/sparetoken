# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).  
Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planned

- 0.2.9 — WhatsApp libera token; fechar chat anônimo e SSH sem senha (ver ROADMAP)
- Repo Origin numa conta nova (ainda não existe URL)

## [0.2.8] — 2026-08-30

O relógio na web é só o pacote: mesma carteira, sem herdar texto.

### Changed

- `?code=` abre a carteira e a lista de chats. Não cria linha nova. Não pinta bolhas
- `&resume=` e o ↗ só mudam o balde de tempo daquela linha
- Copiar link volta a ser o link do bloco (`?code=` só)

## [0.2.7] — 2026-08-30

Cada linha do menu abre o resume daquele chat.

### Added

- Seta ↗ no menu: tela com o link web e o comando SSH, copiar e abrir

## [0.2.6] — 2026-08-30

Resume na web, no mesmo espírito do SSH. Contexto de volta na statusline.

### Added

- `?code=&resume=<id>` reabre o fio daquela linha. `?code=` sozinho continua linha nova, sem texto
- Fio gravado por id da linha (`chat_turns`). Copiar link copia o resume
- Statusline SSH volta a mostrar `ctx N%`

## [0.2.5] — 2026-08-30

Plano de resume fechado. O SSH mostra o mesmo relógio da web.

### Added

- Statusline do terminal: código, restante, minutos desta linha, N chats, total / 5h
- `tunnel-gate` atualiza `logs/wdtsot.json` enquanto o GROK processa
- `run-agent.sh` liga a statusline em toda sessão guest (código no Nome já libera o bloco)

### Changed

- ROADMAP trava as três camadas: código / linha / resume — iguais na web e no SSH

## [0.2.4] — 2026-08-30

O pacote de 5h aparece no chat, não num dashboard.

### Added

- Botão pequeno no composer pago: título da sessão, minutos de cada linha, rodapé `N chats · processado / 5h`
- `?code=` libera a mesma carteira em outra aba ou anônima e abre linha nova — sem herdar texto
- Renomear o chat ativo; clicar linha antiga só troca o balde de tempo

### Changed

- Grátis (50 mensagens, sem código): o botão não aparece
- Fora: inbox, busca, exportar, reabrir bolhas

## [0.2.3] — 2026-08-30

Tempo = processamento do GROK. Vários chats no mesmo código. SSH cobra com Pix Open.

### Changed

- Relógio web só anda do envio até a resposta. Digitar ou deixar a aba aberta não desconta
- Landing deixa o modelo de uso explícito: **GROK 4.6 High Fast**, 5h de processing
- Modal antes do Pix: pagar → confirmar → voltar → Já paguei
- Barra do bloco: restante, processado, código, link de volta, lista de chats
- SSH (`tunnel-gate.py`) mostra um charge ainda Open, libera a mesma carteira, conta processing por atividade do agente
- Sweep a cada 2 min tira links Closed da rotação do site e do SSH

## [0.2.2] — 2026-08-30

Quem pagou um link direto, sem clicar **Pagar R$5**, também libera o bloco.

### Added

- **Já paguei** com e-mail/WhatsApp pega o único charge Closed ainda sem dono e gera o código do bloco
- Aceita o link do Pix no mesmo campo do código, se houver mais de um Closed

## [0.2.1] — 2026-08-30

Estoque de 10 charges únicos + relógio real das 5h.

### Added

- Fila com 10 links Open do conta.vc (SKU `wdtsot · 5h · 4.6 High Fast`)
- Relógio usado / restante; só anda com sessão ativa
- Pause, retomar e começar outra no mesmo bloco
- Aviso nos últimos 5 minutos e bloqueio quando zera (convite a pagar de novo)

## [0.2.0] — 2026-08-30

Pagamento real e fallback para liberar o bloco de 5h.

### Added

- Estoque de charges únicos (`data/conta-links.txt`). Cada checkout reserva um link ainda Open.
- **Já paguei** só credita se a página pública do conta.vc deixar de estar Open
- Fallback na landing: e-mail, WhatsApp ou código do bloco retoma o mesmo bloco
- Mesmo identificador retoma o mesmo bloco noutro cookie / aparelho
- Chat pago passa das 50 mensagens enquanto houver saldo

### Changed

- Card R$5 deixa o aviso de alpha e passa a ser o checkout + “já paguei”

## [0.1.0] — 2026-08-29

Primeiro MVP no ar nesta VPS.

### Added

- Landing editorial (hero, chat, preço, terminal, manifesto, skills teaser, privacy)
- Chat anônimo: 50 prompts, cookie, SSE, `agent --mode ask`
- Módulo de créditos + testes (5h, pause, reconnect, zero)
- Nginx isolado para `wdtsot.shop` (default conecte.mail preservado)
- `systemd` `wdtsot.service` em `127.0.0.1:8787`
- Túnel Cloudflare quick (`cloudflared-wdtsot`) para teste HTTPS
- Vhost também no IP `150.136.116.206` para teste sem DNS

### Reused

- Túnel SSH `agent-guest` + Cursor Agent isolado (`/opt/cursor-agent-tunnel`)

### Known

- `wdtsot.shop` ainda no parking GoDaddy
- Relógio da homepage ainda é artefato visual até existir sessão ativa
- URL trycloudflare muda se o unit reiniciar
