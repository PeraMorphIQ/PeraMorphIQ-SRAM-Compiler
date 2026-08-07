#!/usr/bin/env bash
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
#
# Test entry point for the SRAM compiler.
#
#   ./tests/run_tests.sh              layers 1-3, small configs   (~2 min)
#   ./tests/run_tests.sh --wide       also the 1024x2048 configs  (slower)
#   ./tests/run_tests.sh --gen        also real OpenRAM generation (needs venv)
#   ./tests/run_tests.sh --all        everything
#
# Layers 1-3 are stdlib-only and run on the system python3, so a fresh clone
# needs no setup. Only --gen requires:
#     python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
[ -f OpenRAM/__init__.py ] || { echo "must run from the sram-compiler root"; exit 1; }

RUN_GEN=0
WIDE=0
FULL_LAYOUT=0
for a in "$@"; do
    case "$a" in
        --gen)  RUN_GEN=1 ;;
        --wide) WIDE=1 ;;
        --full-layout) RUN_GEN=1; FULL_LAYOUT=1 ;;
        --all)  RUN_GEN=1; WIDE=1 ;;
        *) echo "unknown flag: $a"; exit 2 ;;
    esac
done

fails=0
step() { echo; echo "===================== $* ====================="; }

step "Layer 1: banking arithmetic"
python3 -m unittest tests.test_sizing || fails=$((fails+1))

step "Layer 2: wrapper rendering + golden regression"
python3 -m unittest tests.test_template_render || fails=$((fails+1))

step "Layer 3: VCS functional simulation"
if ! command -v vcs > /dev/null; then
    echo "  SKIP: vcs not on PATH"
else
    RENDER_ARGS=()
    [ $WIDE = 1 ] && RENDER_ARGS+=(--wide)
    python3 tests/render_cases.py "${RENDER_ARGS[@]}" || fails=$((fails+1))

    CIDS=$(python3 -c "
import sys; sys.path.insert(0,'tests'); import cases
print(' '.join(c.cid for c in (cases.ALL if $WIDE else cases.SMALL)))")
    for cid in $CIDS; do
        for model in openram sync; do
            bash tests/verilog/run_one.sh "$cid" "$model" || fails=$((fails+1))
        done
    done
fi

if [ $RUN_GEN = 1 ]; then
    step "Layer 4: real OpenRAM generation"
    if [ ! -x ./venv/bin/python ]; then
        echo "  SKIP: no venv. Run:"
        echo "    python3 -m venv venv && ./venv/bin/pip install -r requirements.txt"
        fails=$((fails+1))
    else
        GEN_ARGS=()
        [ $FULL_LAYOUT = 0 ] && GEN_ARGS+=(--netlist-only)
        # A vs D is the strongest end-to-end assertion available: the same macro
        # geometry reached through the horizontal path and through mixed(h,1).
        for cid in 32x512_4h1v 32x512_1h4v 32x512_2h2v 32x512_4h1v_m; do
            echo "--- generating $cid"
            ./venv/bin/python tests/gen_case.py --case "$cid" "${GEN_ARGS[@]}" \
                > "tests/build/gen_$cid.log" 2>&1 \
                || { echo "  FAIL: generation of $cid (see tests/build/gen_$cid.log)"; \
                     fails=$((fails+1)); continue; }
            bash tests/check_case.sh "$cid" || fails=$((fails+1))
        done

        echo "--- horizontal(4) vs mixed(4h,1v): same geometry, different code path"
        A=tests/build/gen/32x512_4h1v/verilog
        D=tests/build/gen/32x512_4h1v_m/verilog
        if [ -d "$A" ] && [ -d "$D" ]; then
            if diff -q "$A/sram_32b_512_1rw_freepdk45_sram_32x512_4h.v" \
                       "$D/sram_32b_512_1rw_freepdk45_sram_32x512_4h1v.v" \
                       > /dev/null 2>&1; then
                echo "  ok:   macro models identical"
            else
                # Only the module name may differ.
                if diff <(sed 's/_4h\b/_X/g' "$A/sram_32b_512_1rw_freepdk45_sram_32x512_4h.v") \
                        <(sed 's/_4h1v\b/_X/g' "$D/sram_32b_512_1rw_freepdk45_sram_32x512_4h1v.v") \
                        > /dev/null; then
                    echo "  ok:   macro models identical modulo the module name"
                else
                    echo "  FAIL: macro models differ beyond the name"
                    fails=$((fails+1))
                fi
            fi
        fi
    fi
fi

echo
if [ $fails -eq 0 ]; then
    echo "ALL PASS"
    exit 0
fi
echo "$fails FAILURE(S)"
exit 1
