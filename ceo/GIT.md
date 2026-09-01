# Git — só a conta sparetoken

Identidade pública de **todo** commit deste repo:

```
sparetoken <sparetoken-shop@users.noreply.github.com>
```

Nunca nome de pessoa. Nunca e-mail pessoal. Nunca `Co-authored-by` de ferramenta que vire handle no GitHub.

## Publicar

Helper: `ceo/launch/git-as-sparetoken.sh`. Ele grava a identidade, liga `.githooks` e usa a deploy key (`sparetoken_shop_ed25519`). Nunca `gh` pessoal.

```
ceo/launch/git-as-sparetoken.sh commit -m "why"
ceo/launch/git-as-sparetoken.sh push-alive
```

`push-alive` manda o HEAD atual **e** `main`. Tree suja no fim de pulso ou de correção de agente = falhou.

## VPS / heartbeat

O wrapper (`heartbeat.sh` / `sell.sh`) **não** chama `git`. Depois do unittest (noite) ele **acorda o Cursor Agent**. O agent (processo filho) publica com o helper, só como sparetoken-shop.

Se o pulso precisar de código no GitHub: deploy key `sparetoken-shop`. Nunca remote pessoal.

## Mac

Não gravar `user.name` / `user.email` no repo. Por commit:

```
GIT_AUTHOR_NAME=sparetoken
GIT_AUTHOR_EMAIL=sparetoken-shop@users.noreply.github.com
GIT_COMMITTER_NAME=sparetoken
GIT_COMMITTER_EMAIL=sparetoken-shop@users.noreply.github.com
```

Hook: `.githooks/commit-msg` (recusa e-mail pessoal; tira trailer de ferramenta).
