# SRAM compiler test suite

```bash
./tests/run_tests.sh                # layers 1-3, small configs
./tests/run_tests.sh --wide         # also the full-size 1024x2048 configs
./tests/run_tests.sh --gen          # also real OpenRAM generation (needs ./venv)
./tests/run_tests.sh --full-layout  # --gen, but with layout/LEF/GDS instead of netlist-only
./tests/run_tests.sh --all          # --gen --wide
```

Layers 1-3 are **stdlib-only** and run on a bare `python3`: a fresh clone can
gate on them with no setup. Only `--gen` needs

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/pip list | grep -i coverage    # MUST be empty -- see below
```

> Do **not** reuse `models/smnist_lif_model/venv`. It has `coverage` installed,
> which turns OpenRAM's harmless "Failed to find coverage installation" warning
> into a hard `sqlite3` `ImportError` via VCS's old `libsqlite3` on
> `LD_LIBRARY_PATH` (documented in
> `synopsys/tech/nangate45_typical/NEW_SRAM_MACRO.md` §9.1).

## What each layer proves

### Layer 1 — banking arithmetic (`test_sizing.py`)

Exercises `OpenRAM/compiler/banking.py`, which imports nothing from OpenRAM.
The three call sites that used to carry three copies of the
horizontal/vertical branch (`sram_config.compute_sizes`,
`sram_config.recompute_sizes`, `bank.compute_sizes`) now all route through it.

Key assertions:

- **conservation of bits** — `num_bits_per_bank * num_banks == word_size * num_words`
- **degenerate equivalence** — `mixed(h=n, v=1)` equals `horizontal(n)` and
  `mixed(h=1, v=n)` equals `vertical(n)`, field for field. This is the cheapest
  zero-regression proof that unifying the modes moved neither existing one.
- **`addr_size == bank_addr_size`** — the regression test for the LEF stub-pin
  bug (see below).
- **`top_addr_size == log2(num_words)`** for every split — what keeps a wrapper
  drop-in compatible however the array is divided.
- errors **raise** rather than truncate: a bad `h*v`, a non-divisible
  `word_size`, a non-power-of-2, an out-of-range depth, and an unrecognised
  `banking_mode` string (which used to fall through to vertical, so
  `"Horizontal"` built a vertical macro whose file name said otherwise).

### Layer 2 — wrapper rendering (`test_template_render.py`)

Loads the real `sram_multibank` with a stub `openram` package (`orlib.py`) — no
OpenRAM init, no tech, no third-party deps.

**The gate, run first:** horizontal N=8 must render **byte-identically** to the
committed `rtl/weight_resolver/sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h_top.v`.
That file is checked-in RTL compiled into the blackbox testbench and the
PrimePower flow, so a change there does not error — it produces a different
number, hours later, in a 3+ hour `rtl_opt` run.

Also: `din` slices tile `[0, DATA_WIDTH)` exactly; instance names unique; no
negative or reversed part-selects at `v == 1`; write-mask slices tile; no
unexpanded template tokens; and negative controls proving the guards fire.

### Layer 3 — VCS functional simulation (`verilog/sram_mixed_tb.v`)

One black-box testbench, run against every case and against **both** bank
models: OpenRAM's own generated one (negedge write, `#DELAY` read, `T_HOLD` X)
and the hand-edited fully-synchronous one that `rtl/weight_resolver/` actually
uses. Both satisfy the same contract — data for the address present at posedge
*k* is stable at posedge *k+1* — so one latency model covers all three modes.

- **T1** full address sweep with a slice-distinguishing, address-dependent
  pattern (each horizontal slice of a word gets a different value)
- **T2** H-slice one-hot, localising a concatenation fault to a slice index
- **T3** vertical-group write isolation — the test for the csb/web decode
- **T4** boundary crossing back-to-back with no idle cycles — catches an
  unregistered or double-registered mux select
- **T5** deselect: garbage on the bus with `csb` high changes nothing
- **T6** 5000 randomised ops against a 1-deep-pipeline scoreboard

**Negative controls run during development** (not part of the suite): swapping
two horizontal slice assignments, un-registering the group-select mux, and
making a vertical group default to enabled were each injected into a rendered
wrapper and each was caught, by T1, T1/T0 and T3 respectively.

### Layer 4 — real OpenRAM generation (`gen_case.py`, `check_case.sh`)

Deliberately **not** `generate_sram.py`: that rewrites the tracked
`run_post_process.sh` in place on every run and reads the tracked `config.py`.
`gen_case.py` builds OPTS directly and writes only into `tests/build/gen/<cid>/`.

Asserts the macro `.v` widths, the `_top.v` widths and instance count, the
`.lib` `word_width` / `address_width`, and — on full-layout runs — the LEF pin
counts plus the **stub-pin check**: a `PIN` whose `PORT` block carries no
`LAYER`/`RECT` has no geometry. That check uses field comparison, not a regex;
the regex form `/^[[:space:]]*END[[:space:]]+[A-Za-z]/` silently matches nothing
and passes vacuously (recorded in `synopsys/tech/sky130_typical/build_libs.sh`).

`32x512_4h1v` (horizontal) and `32x512_4h1v_m` (mixed with `v=1`) generate the
**same macro geometry through different code paths**, and the runner diffs their
macro models — the strongest end-to-end equivalence assertion available.

## The before/after gate — and what OpenRAM does NOT reproduce

When changing the sizing code, generate the same config from a pristine checkout
and from the working tree, then:

```bash
./tests/compare_runs.sh <pristine>/outputs <modified>/outputs
```

**Do not expect byte-identical output trees — you will not get them, even from
two runs of identical code.** Measured 2026-08-07 on `32b x 256w, 1 bank,
vertical`, running the pristine tree twice and the modified tree once:

| artifact | reproducible? |
|----------|---------------|
| `.lib` (all 7 corners), `.v` | **yes, byte-identical** — these are what the flow consumes |
| `.sp`, `.lef` | same multiset of lines, **different order every run** |
| `*_stim.sp`, `*_meas.sp` | never — `characterizer/functional.py:38` seeds with `time.time_ns()` |
| `.gds`, `.html`, `datasheet.info`, `configs/*.py` | never — timestamps and run metadata |

The `.sp`/`.lef` reordering comes from OpenRAM iterating sets/dicts whose order
depends on `PYTHONHASHSEED`, which CPython randomises per process. **It was
confirmed by a control run**: pristine-vs-pristine reorders exactly the same way
as pristine-vs-modified, so it says nothing about a code change. `compare_runs.sh`
encodes all of this — it compares `.sp`/`.lef` sorted, skips the genuinely
non-reproducible files, and fails only on a real difference.

Result of the gate for this change: **EQUIVALENT**. All seven Liberty files and
the Verilog model byte-identical; `.sp`/`.lef` reordered only.

## The `addr_size` change

`sram_config` used to set `addr_size = bank_addr_size + log2(num_banks)`,
unguarded. `sram_1bank.add_pins` created those extra pins and
`characterizer/lib.py` wrote them into `address_width`, but nothing routed them:
they left the LEF with an empty `PORT`, and disagreed with the `ADDR_WIDTH` that
`base/verilog.py` writes into the behavioural model.

On the shipped 45 nm macro that is `addr0[11]`, `[12]`, `[13]` — **declared 14,
decoded 11** — with `.lib` `address_width : 14` against `.v` `ADDR_WIDTH = 11`.

It is now `addr_size = bank_addr_size` for every mode. Consequences:

- **`num_banks == 1` is a no-op**, so the default single-bank config still
  generates bit-identically.
- `_top.v` and the behavioural `.v` are unaffected in every mode (both already
  used `bank_addr_size`), so the Layer-2 golden gate still holds.
- **The committed artifacts for `sram_1024x2048_8h` no longer reproduce from
  this compiler.** `synopsys/tech/nangate45_typical/src/*.lef` / `*.lib` /
  `*.db` and the `.ndm` built from them still describe a 14-address-pin macro; a
  regeneration would now emit 11. They remain usable as-is — nothing in the flow
  was changed — but they are a snapshot, not a reproducible output. Regenerating
  costs a full OpenRAM run plus `run_post_process.sh --all` plus
  `build_libs.sh --sram`.

## Measured wall clock (this machine, 2026-08-07)

| task | time |
|------|------|
| Layers 1+2 | < 1 s |
| Layer 3, one case one model (32b x 512w) | ~12 s (VCS compile dominates) |
| Layer 3, all 6 small cases x 2 models | ~2.5 min |
| Layer 4, one 32x512 case, `--netlist-only` | ~15 s |
| Layer 4, one 32x512 case, full layout | minutes (measure and update this row) |

`--netlist-only` sets `OPTS.netlist_only`, which skips `create_layout`, GDS and
LEF while still producing `.sp`, `.v`, `_top.v` and all seven `.lib` corners.
That is enough for every check except the LEF ones.
