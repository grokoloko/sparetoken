# Git — só a conta sparetoken

Identidade pública de **todo** commit deste repo:

```
sparetoken <sparetoken-shop@users.noreply.github.com>
```

Nunca nome de pessoa. Nunca e-mail pessoal. Nunca `Co-authored-by` de ferramenta que vire handle no GitHub.

## VPS / heartbeat

`ceo/launch/heartbeat.sh` **não commita, não dá push, não cria tag.** Só unittest + carimbo.

Se o pulso precisar de código no GitHub: o texto vai pro Mac / workspace com a **deploy key** `sparetoken-shop`. A VPS não tem git write.

## Mac

Não gravar `user.name` / `user.email` no repo. Por commit:

```
GIT_AUTHOR_NAME=sparetoken
GIT_AUTHOR_EMAIL=sparetoken-shop@users.noreply.github.com
GIT_COMMITTER_NAME=sparetoken
GIT_COMMITTER_EMAIL=sparetoken-shop@users.noreply.github.com
```

Hook: `.githooks/commit-msg` (recusa e-mail pessoal; tira trailer de ferramenta).
