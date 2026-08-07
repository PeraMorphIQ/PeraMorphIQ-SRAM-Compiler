#!/usr/bin/env bash
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
#
# Compare two OpenRAM output trees artifact by artifact.
#
#   compare_runs.sh <outputs-dir-A> <outputs-dir-B>
#
# Used as the before/after gate when changing the sizing code: generate the same
# config from a pristine checkout and from the working tree, then run this.
#
# NOT everything OpenRAM writes is reproducible, and pretending otherwise makes
# the gate useless. Three categories:
#
#   DETERMINISTIC   .lib, .v, .db   -- must be byte-identical. These are what
#                                      the downstream flow actually consumes.
#   ORDER-UNSTABLE  .sp, .lef       -- same multiset of lines, emitted in a
#                                      different order run to run. OpenRAM
#                                      iterates sets/dicts whose order depends
#                                      on PYTHONHASHSEED, which CPython
#                                      randomises per process. Compare sorted.
#   NON-REPRODUCIBLE
#       *_stim.sp, *_meas.sp        -- characterizer/functional.py:38 seeds with
#                                      time.time_ns() unless OPTS.functional_seed
#                                      is set, so the stimulus differs every run.
#       *.gds                       -- carries a timestamp.
#       configs/*.py                -- a copy of the user's config.py.
#       datasheet.info, *.html      -- run metadata.
#       Anything with an absolute path in it also differs simply because the two
#       trees are in different directories.
#
# Exit non-zero only if a DETERMINISTIC artifact differs, or an ORDER-UNSTABLE
# one differs by more than ordering.
set -uo pipefail

A="${1:?usage: compare_runs.sh <outputs-A> <outputs-B>}"
B="${2:?usage: compare_runs.sh <outputs-A> <outputs-B>}"

for d in "$A" "$B"; do
    [ -d "$d" ] || { echo "not a directory: $d"; exit 2; }
done

fails=0
(cd "$A" && find . -type f | sort) > /tmp/.cmp_a.$$
(cd "$B" && find . -type f | sort) > /tmp/.cmp_b.$$
if ! diff -q /tmp/.cmp_a.$$ /tmp/.cmp_b.$$ > /dev/null; then
    echo "FAIL: the two runs produced different file sets"
    diff /tmp/.cmp_a.$$ /tmp/.cmp_b.$$
    fails=$((fails+1))
fi

while read -r f; do
    case "$f" in
        *_stim.sp|*_meas.sp|*.gds|*.log|./logs/*|./configs/*|./datasheet.info|*.html)
            printf '  skip (non-reproducible)  %s\n' "$f"; continue ;;
    esac

    if cmp -s "$A/$f" "$B/$f"; then
        printf '  IDENTICAL                %s\n' "$f"
        continue
    fi

    case "$f" in
        *.lib|*.v|*.db)
            printf '  FAIL (must be identical) %s\n' "$f"
            diff "$A/$f" "$B/$f" | head -20
            fails=$((fails+1)) ;;
        *.sp|*.lef)
            if [ "$(sort "$A/$f" | md5sum)" = "$(sort "$B/$f" | md5sum)" ]; then
                printf '  reordered only           %s\n' "$f"
            else
                printf '  FAIL (content differs)   %s\n' "$f"
                diff "$A/$f" "$B/$f" | head -20
                fails=$((fails+1))
            fi ;;
        *)
            printf '  differs (unclassified)   %s\n' "$f" ;;
    esac
done < /tmp/.cmp_a.$$

rm -f /tmp/.cmp_a.$$ /tmp/.cmp_b.$$
echo
if [ $fails -eq 0 ]; then echo "EQUIVALENT"; exit 0; fi
echo "$fails DIFFERENCE(S) THAT MATTER"
exit 1
