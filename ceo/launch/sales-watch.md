# Launch · sales-watch

Função do CEO: **vender e dizer que vendeu.**

1. Ler sqlite da VPS (só SELECT). Tabelas: `purchases`, `pay_links`, `credit_wallets`.
2. Venda = purchase pago **ou** pay_link `closed` novo desde o último carimbo.
3. Se vendeu: rascunho de tweet em `data/celebrate.txt` (sem PII):
   `mais um bloco saiu da prateleira. R$5 · 5h. https://sparetoken.shop/?utm_source=x&utm_medium=social&utm_campaign=sold&utm_content=sNNN`
4. Mandar o rascunho pro `x-pulse` / Mac com sessão. VPS não posta sozinha sem cofre.
5. Se links Open < 3: escrever `RESTOCK +10` em `data/restock.flag`. Mint só no Chrome local.
6. Meta mês 1: 10 vendas pelo bot. Contar só o que este caso fechou (UTM do CEO), não referral de fora.
