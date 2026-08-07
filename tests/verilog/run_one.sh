#!/usr/bin/env bash
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
#
# Compile and run the functional testbench for one rendered case.
#   run_one.sh <case-id> <openram|sync> [--debug]
set -euo pipefail

CID="${1:?usage: run_one.sh <case-id> <openram|sync> [--debug]}"
MODEL="${2:?usage: run_one.sh <case-id> <openram|sync> [--debug]}"
DEBUG="${3:-}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
B="$ROOT/tests/build/$CID"

[ -d "$B" ] || { echo "no rendered case at $B (run tests/render_cases.py)"; exit 1; }
# shellcheck source=/dev/null
. "$B/params.sh"

case "$MODEL" in
  openram) BANK="$B/$MACRO.v" ;;
  sync)    BANK="$B/${MACRO}_sync.v" ;;
  *) echo "model must be 'openram' or 'sync'"; exit 1 ;;
esac

RUN="$B/$MODEL"
rm -rf "$RUN"
mkdir -p "$RUN"

DBG=()
[ "$DEBUG" = "--debug" ] && DBG=(-debug_access+all)

# -error=PCWM turns a port-connection width mismatch ("din0 got 256 bits, port
# is 128") into a non-zero exit. That alone catches most template arithmetic
# errors, before any simulation runs.
vcs -full64 -sverilog +v2k -q -nc \
    -timescale=1ns/1ps \
    "${DBG[@]}" \
    +lint=PCWM,TFIPC-L -error=PCWM \
    -Mdir="$RUN/csrc" \
    -pvalue+sram_mixed_tb.W="$W" \
    -pvalue+sram_mixed_tb.D="$D" \
    -pvalue+sram_mixed_tb.H="$H" \
    -pvalue+sram_mixed_tb.V="$V" \
    -pvalue+sram_mixed_tb.AW="$AW" \
    "$BANK" "$B/${MACRO}_top.v" "$B/dut_wrap.v" \
    "$ROOT/tests/verilog/sram_mixed_tb.v" \
    -top sram_mixed_tb \
    -o "$RUN/simv" -l "$RUN/vcs.log" > /dev/null

"$RUN/simv" -l "$RUN/simv.log" > /dev/null 2>&1 || true

if grep -q '^PASS' "$RUN/simv.log"; then
    printf '  PASS  %-16s %-8s %s\n' "$CID" "$MODEL" "$(grep -o 'PASS.*' "$RUN/simv.log" | head -1)"
    exit 0
fi

echo "  FAIL  $CID $MODEL   (see $RUN/simv.log)"
grep -E '^(ERROR|FAIL|T[0-9])' "$RUN/simv.log" | head -20 || true
exit 1
