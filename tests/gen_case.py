#!/usr/bin/env python3
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
"""
Layer 4 driver: run the real OpenRAM generator for one case.

Deliberately NOT generate_sram.py, which rewrites the tracked run_post_process.sh
in place on every run (re.sub on SRAM_NAME) and reads the tracked config.py.
This builds OPTS directly and writes only into tests/build/gen/<cid>/.

Must run with cwd == the sram-compiler root: OpenRAM is imported by path from
"./OpenRAM", exactly as generate_sram.py does.

    ./venv/bin/python tests/gen_case.py --case 32x512_2h2v [--netlist-only]
"""

import argparse
import glob
import importlib.util
import os
import pathlib
import shutil
import sys

sys.setrecursionlimit(5000000)

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

if pathlib.Path.cwd().resolve() != REPO:
    sys.exit("ERROR: run from {} (OpenRAM is imported by relative path)".format(REPO))

sys.path.insert(0, "./")
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location(
    "openram", os.path.join("./", "OpenRAM", "__init__.py"),
    submodule_search_locations=[os.path.join("./", "OpenRAM")])
openram = importlib.util.module_from_spec(_spec)
sys.modules["openram"] = openram
_spec.loader.exec_module(openram)

_expected = os.path.realpath(os.path.join("./", "OpenRAM", "compiler"))
if os.path.realpath(openram.OPENRAM_HOME) != _expected:
    sys.exit("ERROR: OPENRAM_HOME is {}, expected {}".format(
        openram.OPENRAM_HOME, _expected))

from openram import globals as or_globals   # noqa: E402
from openram import sram_config             # noqa: E402
from openram import sram                    # noqa: E402

import cases                                # noqa: E402

FILE_MOVES = {
    "designs": ["*.gds", "*.lef"],
    "libs": ["*.lib"],
    "db": ["*.db"],
    "verilog": ["*.v"],
    "spice": ["*.sp"],
    "reports": ["*.html"],
    "configs": ["*.py"],
    "logs": ["*.log"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--netlist-only", action="store_true",
                    help="skip layout/GDS/LEF; still writes .v, _top.v, .sp, .lib")
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()

    c = cases.get(a.case)
    g = cases.geometry(c)
    name = cases.macro_name(c)
    out = (HERE / "build" / "gen" / c.cid).resolve()
    if out.exists():
        shutil.rmtree(out)
    for sub in ["designs", "libs", "verilog", "spice", "reports",
                "ndm", "db", "logs", "configs"]:
        (out / sub).mkdir(parents=True, exist_ok=True)

    # A minimal config module for init_openram, in place of the tracked config.py.
    cfg = out / "gen_config.py"
    cfg.write_text(
        "word_size = {}\nnum_words = {}\nnum_banks = {}\n"
        "banking_mode = {!r}\nnum_h_banks = {}\nnum_v_banks = {}\n"
        "tech_name = 'freepdk45'\nuse_conda = False\nnum_threads = {}\n"
        "analytical_delay = True\ncheck_lvsdrc = False\nuse_pex = False\n"
        "netlist_only = {}\noutput_path = {!r}\n".format(
            c.word_size, c.num_words, c.num_banks, c.mode, c.h, c.v,
            a.threads, bool(a.netlist_only), str(out) + "/"))

    sys.path.insert(0, str(out))
    or_globals.init_openram(str(cfg.with_suffix("")))
    or_globals.OPTS.output_path = str(out) + "/"
    or_globals.OPTS.num_threads = a.threads
    or_globals.OPTS.banking_mode = c.mode
    or_globals.OPTS.num_h_banks = c.h
    or_globals.OPTS.num_v_banks = c.v
    or_globals.OPTS.netlist_only = bool(a.netlist_only)

    conf = sram_config(word_size=c.word_size,
                       num_words=c.num_words,
                       num_banks=c.num_banks)
    s = sram(sram_config=conf, name="sram_{}x{}_{}".format(
        c.word_size, c.num_words, cases.suffix(c)))
    s.save()

    actual = s.s.name
    if actual != name:
        print("WARNING: generated name {!r} != expected {!r}".format(actual, name))

    for dest, patterns in FILE_MOVES.items():
        for pat in patterns:
            for f in glob.glob(str(out / pat)):
                base = os.path.basename(f)
                if dest == "configs" and base == "__init__.py":
                    continue
                shutil.move(f, str(out / dest / base))

    print("case            {}".format(c.cid))
    print("mode            {} ({}h x {}v)".format(c.mode, c.h, c.v))
    print("macro           {}".format(actual))
    print("macro geometry  {}b x {}w".format(g["bank_word_size"], g["words_per_bank"]))
    print("addr_size       {} (bank_addr_size {})".format(
        s.s.addr_size, s.s.bank_addr_size))
    print("top addr width  {}".format(g["top_addr_size"]))
    print("instances       {}".format(g["instances"]))
    print("output          {}".format(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
