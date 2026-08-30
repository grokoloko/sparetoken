---
name: conta-wdtsot-charges
description: >-
  Mints unique conta.vc Pix charges for the official WDTSOT SKU from
  https://app.conta.vc/receive/link/charge/new (R$5 / 5h / 4.6 High Fast),
  then appends Open /pay/fuzzy/c/… URLs to data/conta-links.txt. Use when
  creating payment links, restocking rotation, or the founder is on the
  logged-in charge/new page.
---

# conta.vc — mint do SKU oficial

Página de criação (já logado, máquina local — sem passkey):

**https://app.conta.vc/receive/link/charge/new**

Cada submit gera **um** charge único. A VPS nunca cria charge. Ela só lê a página pública `/pay/fuzzy/c/…` e credita quando deixa de estar `Open`.

## Produto padrão (não variar)

| Campo na UI | Valor |
|---|---|
| Amount / valor | `5.00` (R$ 5,00 · 500 centavos) |
| Description / purpose | `wdtsot · 5h · 4.6 High Fast` |
| SKU interno | `wdtsot-5h` |
| Horas | 5 (`18000` s) |
| Handle | `@fuzzy` |

Não mudar preço, horas nem o texto da descrição.

## Automação (Chrome local já autenticado)

1. Abrir **exato** `https://app.conta.vc/receive/link/charge/new`
2. Preencher valor `5.00` e descrição `wdtsot · 5h · 4.6 High Fast`
3. Criar o charge
4. Copiar o URL público `https://app.conta.vc/pay/fuzzy/c/…`
5. Repetir até o estoque (padrão: 10 Open)
6. Ingerir no site (não precisa restart):

```bash
python3 scripts/ingest_conta_links.py --append \
  'https://app.conta.vc/pay/fuzzy/c/TOKEN1' \
  'https://app.conta.vc/pay/fuzzy/c/TOKEN2'
```

No Mac, só abrir a tela de mint:

```bash
open -a "Google Chrome" "https://app.conta.vc/receive/link/charge/new"
```

Console do Chrome (página `charge/new` aberta) — tenta preencher o form:

```javascript
(() => {
  const DESC = "wdtsot · 5h · 4.6 High Fast";
  const fields = [...document.querySelectorAll("input,textarea")];
  const amount = fields.find((el) => /amount|valor|r\$/i.test(`${el.name} ${el.placeholder} ${el.ariaLabel || ""}`))
    || fields.find((el) => el.type === "number" || el.inputMode === "decimal");
  const desc = fields.find((el) => /desc|purpose|memo|what/i.test(`${el.name} ${el.placeholder} ${el.ariaLabel || ""}`))
    || fields.find((el) => el.tagName === "TEXTAREA")
    || fields[1];
  const set = (el, v) => {
    if (!el) return;
    el.focus();
    el.value = v;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  };
  set(amount, "5.00");
  set(desc, DESC);
})();
```

Depois de criar, o URL que importa é o `/pay/fuzzy/c/…`, não o `/receive/…`.

## Onde cada máquina entra

- **Chrome local (esta página):** mint. Founder já logado.
- **VPS (`wdtsot`):** `data/conta-links.txt` + reserva no checkout + claim só se o charge público fechou.

## Depois do Pix

Charge fecha sozinho. `Já paguei` no wdtsot só libera 5h se inspect ≠ `Open`. Link fechado não volta pra fila.

## Não fazer

- Reciclar um URL só para todo mundo
- Playwright / cookie / VPS Chrome no lugar do mint local
- Creditar sem o charge ter fechado
- Mudar a descrição do SKU
