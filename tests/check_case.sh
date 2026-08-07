#!/usr/bin/env bash
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
#
# Layer 4 assertions on the artifacts a real OpenRAM run produced.
#   check_case.sh <case-id>
#
# LEF/GDS checks are skipped automatically when the case was generated with
# --netlist-only (no designs/*.lef).
set -uo pipefail

CID="${1:?usage: check_case.sh <case-id>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
D="$ROOT/tests/build/gen/$CID"

[ -d "$D" ] || { echo "no generated case at $D"; exit 1; }

# Expected values come from the shared case table, not from the artifacts.
eval "$(python3 - "$CID" <<'PY'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, "tests")
import cases
c = cases.get(sys.argv[1])
g = cases.geometry(c)
print("MACRO={}".format(cases.macro_name(c)))
print("BW={}".format(g["bank_word_size"]))
print("BAW={}".format(g["bank_addr_size"]))
print("TOPW={}".format(c.word_size))
print("TOPAW={}".format(g["top_addr_size"]))
print("INST={}".format(g["instances"]))
PY
)" || { echo "could not resolve case $CID"; exit 1; }

fails=0
fail() { echo "  FAIL: $*"; fails=$((fails+1)); }
ok()   { echo "  ok:   $*"; }

V="$D/verilog/$MACRO.v"
T="$D/verilog/${MACRO}_top.v"
LIB="$D/libs/${MACRO}_TT_1p0V_25C.lib"
LEF="$D/designs/$MACRO.lef"

echo "=== $CID  ($MACRO) ==="

for f in "$V" "$T" "$LIB"; do
    [ -s "$f" ] || fail "missing or empty $f"
done
[ $fails -eq 0 ] || { echo "$CID: $fails failure(s)"; exit 1; }

# --- macro behavioural model -------------------------------------------------
# base/verilog.py writes ADDR_WIDTH = bank_addr_size, so this is the truth the
# LEF and .lib must agree with.
grep -qE "parameter DATA_WIDTH = $BW ;" "$V" \
    && ok "macro DATA_WIDTH = $BW" || fail "macro DATA_WIDTH != $BW"
grep -qE "parameter ADDR_WIDTH = $BAW ;" "$V" \
    && ok "macro ADDR_WIDTH = $BAW" || fail "macro ADDR_WIDTH != $BAW"

# --- wrapper -----------------------------------------------------------------
grep -qE "parameter DATA_WIDTH *= *$TOPW;" "$T" \
    && ok "_top DATA_WIDTH = $TOPW" || fail "_top DATA_WIDTH != $TOPW"
grep -qE "parameter ADDR_WIDTH *= *$TOPAW;" "$T" \
    && ok "_top ADDR_WIDTH = $TOPAW" || fail "_top ADDR_WIDTH != $TOPAW"
n=$(grep -cE "^  $MACRO " "$T")
[ "$n" = "$INST" ] && ok "_top instantiates $INST macros" \
    || fail "_top instantiates $n macros, expected $INST"
if grep -qE '\{\{|\{%' "$T"; then fail "_top contains unexpanded template tokens"; \
    else ok "no unexpanded template tokens"; fi

# --- Liberty -----------------------------------------------------------------
libw=$(grep -aoE "word_width[[:space:]]*:[[:space:]]*[0-9]+" "$LIB" | head -1 | grep -oE "[0-9]+")
liba=$(grep -aoE "address_width[[:space:]]*:[[:space:]]*[0-9]+" "$LIB" | head -1 | grep -oE "[0-9]+")
[ "$libw" = "$BW" ] && ok ".lib word_width = $BW" || fail ".lib word_width $libw != $BW"
[ "$liba" = "$BAW" ] && ok ".lib address_width = $BAW" \
    || fail ".lib address_width $liba != $BAW (the addr_size over-declaration is back)"

# --- LEF (full-layout runs only) ---------------------------------------------
if [ -s "$LEF" ]; then
    declared=$(grep -acE "^[[:space:]]*PIN[[:space:]]+addr0\[" "$LEF")
    din=$(grep -acE "^[[:space:]]*PIN[[:space:]]+din0\[" "$LEF")
    dout=$(grep -acE "^[[:space:]]*PIN[[:space:]]+dout0\[" "$LEF")
    [ "$din" = "$BW" ]  && ok "LEF din0 pins = $BW"   || fail "LEF din0 pins $din != $BW"
    [ "$dout" = "$BW" ] && ok "LEF dout0 pins = $BW"  || fail "LEF dout0 pins $dout != $BW"
    [ "$declared" = "$liba" ] && ok "LEF addr0 pins = $declared (matches .lib)" \
        || fail "LEF declares $declared addr0 pins but .lib says $liba (NDM-031 ahead)"

    # Stub pins: a PIN whose PORT block carries no LAYER/RECT has no geometry.
    # Field comparison, NOT a regex -- the regex form
    #   /^[[:space:]]*END[[:space:]]+[A-Za-z]/
    # silently matches nothing and passes vacuously (see
    # synopsys/tech/sky130_typical/build_libs.sh, which records that trap).
    stubs=$(awk '
        $1 == "PIN"                         { pin=$2; body=0; next }
        $1 == "LAYER" || $1 == "RECT"       { body=1; next }
        $1 == "END" && NF > 1 && $2 == pin  { if (!body) print pin; pin="" }
    ' "$LEF")
    if [ -n "$stubs" ]; then
        fail "pins with no geometry: $(echo "$stubs" | tr '\n' ' ')"
    else
        ok "no stub pins (every declared pin is routed)"
    fi

    routed=$(awk '
        $1 == "PIN"                         { pin=$2; body=0; next }
        $1 == "LAYER" || $1 == "RECT"       { body=1; next }
        $1 == "END" && NF > 1 && $2 == pin  { if (body && pin ~ /^addr0\[/) n++; pin="" }
        END { print n+0 }
    ' "$LEF")
    [ "$routed" = "$BAW" ] && ok "routed addr0 pins = $BAW" \
        || fail "routed addr0 pins $routed != $BAW"

    size=$(grep -aoE "^[[:space:]]*SIZE .*" "$LEF" | head -1 | tr -s ' ')
    ok "LEF ${size# }"
else
    echo "  (netlist-only run: no LEF, skipping physical checks)"
fi

if [ $fails -gt 0 ]; then echo "$CID: $fails failure(s)"; exit 1; fi
echo "$CID: all checks passed"
