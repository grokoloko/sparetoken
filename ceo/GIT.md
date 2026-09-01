# Git — só a conta sparetoken

Identidade pública de **todo** commit deste repo:

```
sparetoken <sparetoken-shop@users.noreply.github.com>
```

Nunca nome de pessoa. Nunca e-mail pessoal. Nunca `Co-authored-by` de ferramenta que vire handle no GitHub.

## VPS / pulsos (11:30 e 23:30)

`ceo/launch/heartbeat.sh` e `ceo/launch/sell.sh` **chamam cursor-agent** (`agent -p --trust --force`). Unittest ou fila **sem** agent = `PULSE_FAIL`, nunca `PULSE_OK` / `SELL_OK`.

Os wrappers **não** commitam, **não** dão push, **não** criam tag. O agent pode editar a working tree. Commit, se houver, fica com a identidade sparetoken acima. Push / PR de `main`: só `sparetoken-shop`.

Se o pulso precisar de código no GitHub e a VPS não tiver git write: o texto vai pro Mac / workspace com a **deploy key** `sparetoken-shop`.

## Mac

Não gravar `user.name` / `user.email` no repo. Por commit:

```
GIT_AUTHOR_NAME=sparetoken
GIT_AUTHOR_EMAIL=sparetoken-shop@users.noreply.github.com
GIT_COMMITTER_NAME=sparetoken
GIT_COMMITTER_EMAIL=sparetoken-shop@users.noreply.github.com
```

Hook: `.githooks/commit-msg` (recusa e-mail pessoal; tira trailer de ferramenta).
