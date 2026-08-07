# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
"""
Shared banking-configuration table.

One table drives the sizing tests, the template-render tests and the VCS
functional testbench, so the three layers can never disagree about what a
configuration means.
"""

import collections

Case = collections.namedtuple(
    "Case", "cid mode word_size num_words num_banks h v words_per_row wide")


def _mk(cid, mode, W, N, banks, h, v, words_per_row=1, wide=False):
    return Case(cid, mode, W, N, banks, h, v, words_per_row, wide)


# Small configurations: fast to elaborate and simulate, run by default.
SMALL = [
    _mk("32x512_4h1v", "horizontal", 32, 512, 4, 4, 1),
    _mk("32x512_1h4v", "vertical",   32, 512, 4, 1, 4),
    _mk("32x512_2h2v", "mixed",      32, 512, 4, 2, 2),
    _mk("32x512_4h1v_m", "mixed",    32, 512, 4, 4, 1),   # degenerate == horizontal
    _mk("32x512_1h4v_m", "mixed",    32, 512, 4, 1, 4),   # degenerate == vertical
    _mk("64x256_2h2v", "mixed",      64, 256, 4, 2, 2),
]

# Full-size configurations matching the shipped 45 nm array. Slow; --wide only.
WIDE = [
    _mk("1024x2048_8h",   "horizontal", 1024, 2048, 8, 8, 1, wide=True),
    _mk("1024x2048_1h8v", "vertical",   1024, 2048, 8, 1, 8, wide=True),
    _mk("1024x2048_8h1v", "mixed",      1024, 2048, 8, 8, 1, wide=True),
    _mk("1024x2048_4h2v", "mixed",      1024, 2048, 8, 4, 2, wide=True),
    _mk("1024x2048_2h4v", "mixed",      1024, 2048, 8, 2, 4, wide=True),
    _mk("1024x2048_1h8v_m", "mixed",    1024, 2048, 8, 1, 8, wide=True),
]

ALL = SMALL + WIDE


def suffix(c):
    if c.mode == "mixed":
        return "{}h{}v".format(c.h, c.v)
    if c.mode == "horizontal":
        return "{}h".format(c.num_banks)
    return "{}v".format(c.num_banks)


def macro_name(c):
    """The name OpenRAM would produce: output_name + '_' + config.sram_name."""
    return "sram_{}b_{}_1rw_freepdk45_sram_{}x{}_{}".format(
        c.word_size, c.num_words, c.word_size, c.num_words, suffix(c))


def geometry(c):
    """Derived widths for a case, independent of the compiler under test."""
    words_per_bank = c.num_words // c.v
    num_rows = words_per_bank // c.words_per_row
    row_addr = (num_rows - 1).bit_length()
    col_addr = (c.words_per_row - 1).bit_length()
    bank_addr = row_addr + col_addr
    return {
        "bank_word_size": c.word_size // c.h,
        "words_per_bank": words_per_bank,
        "bank_addr_size": bank_addr,
        "bank_sel": (c.v - 1).bit_length(),
        "top_addr_size": bank_addr + (c.v - 1).bit_length(),
        "instances": c.h * c.v,
    }


def get(cid):
    for c in ALL:
        if c.cid == cid:
            return c
    raise KeyError("no such case: {} (have {})".format(
        cid, ", ".join(x.cid for x in ALL)))
