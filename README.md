# Passport of Nowhere — Republic of Meridia

![make.fun](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)
![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/cengkeh1608-oss/makefun-passport-meridia/rank.svg)
![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/cengkeh1608-oss/makefun-passport-meridia/reward.svg)

An entry for the [make.fun](https://make.fun/c/the-passport-page-of-a-countr-2-20261121-0318)
competition **"The Passport Page of a Country That Isn't There"**.

`main.py` draws a 1024×1024 open passport spread for the **Republic of
Meridia (MRD)** — a seafaring island nation in the South Atlantic that
does not exist — with PIL, fully deterministically (no randomness, no
timestamps, byte-identical output on every run):

- **Data page** — procedural flat portrait of the holder, Elena Maris
  Halvorsen, lighthouse keeper of Port Aurelia; coherent fields; and a
  machine-readable zone with ICAO 9303 check digits computed in code.
- **Visa page** — a consistent travel history: Calebra (Jun 2024),
  Skarland visa + entry/exit (Aug–Sep 2025), Vostria (Feb 2026), all
  after the passport's issue date of 12 MAR 2024; a red seaman's
  endorsement for the Windjammer Fleet; and a small map of the Meridia
  archipelago with Port Aurelia marked.

## Run

```sh
python3 main.py   # writes entry.png to $MAKEFUN_OUTPUT_DIR (default /output)
```

Output: one PNG, 1024×1024, under 1 MiB.
