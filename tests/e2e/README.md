# Jornadas E2E (Playwright + SSH)

Ainda sem spec armada na CI. Quando ligar: job extra em `protect-main.yml`, **depois** do unittest.

## O que validar

1. **Pagar** — landing → Gerar PIX (página pública fuzzy Open). Sem login. Sem mint.
2. **Já paguei + código** — código da carteira vira login. Fixture fake (`wdtsot-TEST`).
3. **Relógio** — 5h, pause, outra linha, `?code=` não herda texto; `&resume=` herda.
4. **Indicar** — mesmo `?code=` no convite. Popup rápido. Pix continua um passo.
5. **SSH** — `ssh -t agent-guest@…` + statusline = mesmo relógio. Sem gravar WhatsApp no artefato.

## Anonimato no print

Antes de salvar PNG: cobrir e-mail, telefone, código real, nome. Fixture só. Quem compra e quem vende não aparece no CI.

Não usar Playwright para `charge/new`. Isso é a skill no Mac.
