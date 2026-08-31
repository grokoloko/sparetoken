# Alma: mint de charges P2P (conta.vc)

Isto não é um “script de billing”. É como o experimento **multiplica** pagamento sem virar processador de cartão.

Skill canônica (o CEO lê):

`.cursor/skills/conta-wdtsot-charges/SKILL.md`

Código que a VPS já usa:

- `scripts/ingest_conta_links.py` — entra URL `/pay/fuzzy/c/…` no pool
- `scripts/sweep_pay_links.py` — o que ainda está Open
- `data/conta-links.txt` — estoque (não vai no git)
- `pay.py` — inspect do charge público; `paid` só com evidência

## A regra que o CEO não pode esquecer

| Quem | Faz |
|---|---|
| Chrome **local**, já logado em `app.conta.vc/receive/link/charge/new` | **Minta** charges únicos |
| VPS | **Só lê** a página pública. Nunca cria charge. Nunca guarda cookie do conta.vc |

SKU único, sempre:

- Amount `5.00`
- Description `wdtsot · 5h · 4.6 High Fast`
- Handle `@fuzzy`
- URL que importa: `https://app.conta.vc/pay/fuzzy/c/…` — nunca o `/receive/…`

Estoque padrão: **10 Open**. Charge fecha sozinho no Pix. `Já paguei` no shop só libera se o inspect ≠ Open.

## Por que isso é web3 / P2P

O fuzzy é um money link. Pix na borda, liquidação na Conta (saldo on-chain do lado deles). A loja não custodia chave. Multiplicar links = multiplicar **prateleiras de um bloco**, não “abrir um gateway”. Quem indica (referral) e quem publica skill usa a **mesma** prateleira.

Quando o heartbeat precisar de estoque: abrir a skill, mintar no Mac, `ingest_conta_links.py --append`. Não inventar outro Pix.
