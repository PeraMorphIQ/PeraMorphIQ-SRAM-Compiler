# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
#
# This file is part of Pera-OpenRAM.
"""
Banking arithmetic: the single source of truth for how a banking mode maps onto
the ONE physical macro that gets generated and the wrapper that instantiates it.

This module deliberately imports NOTHING from OpenRAM -- no OPTS, no tech, no
factory. Three call sites used to carry three copies of the same
horizontal/vertical branch (sram_config.compute_sizes, sram_config.recompute_sizes
and bank.compute_sizes); they now all come here, and the fast test tier can
exercise this file on a bare interpreter.

Background: sram.py only ever builds a single sram_1bank. "Banking" therefore
means (a) how that one macro is sized and (b) which Verilog wrapper template is
rendered -- there is no stitched LEF/.lib/.db/.gds for a multi-bank array.
"""

from math import log

BANKING_MODES = ("vertical", "horizontal", "mixed")

# OpenRAM's own limits, enforced downstream by amend_words_per_row().
MIN_WORDS_PER_BANK = 16
MAX_WORDS_PER_BANK = 4096
RECOMMENDED_MAX_WORDS_PER_BANK = 2048

# A macro narrower than this is not physically sensible.
MIN_BITS_PER_BANK = 8

VALID_WORDS_PER_ROW = (1, 2, 4, 8, 16)


def is_pow2(n):
    return n >= 1 and int(n) == n and (int(n) & (int(n) - 1)) == 0


def resolve_banking(banking_mode, num_banks, num_h_banks=1, num_v_banks=1):
    """
    Map a banking mode onto the (h, v) shape of the macro array.

        horizontal -> (num_banks, 1)   word width divided
        vertical   -> (1, num_banks)   address space divided
        mixed      -> (num_h_banks, num_v_banks)

    Every sizing formula is written in terms of (h, v), so the two single-axis
    modes are exactly the degenerate cases of the mixed one.

    Raises ValueError on an unrecognised mode. Do NOT reintroduce a default:
    the old `if mode == "horizontal": ... else: (vertical)` meant a typo such as
    "Horizontal" silently built a vertical macro whose file name said otherwise.
    """
    if banking_mode == "horizontal":
        return num_banks, 1
    if banking_mode == "vertical":
        return 1, num_banks
    if banking_mode == "mixed":
        return num_h_banks, num_v_banks
    raise ValueError(
        "Unknown banking_mode {!r}. Expected one of {}.".format(
            banking_mode, ", ".join(repr(m) for m in BANKING_MODES)))


def bank_geometry(word_size, num_words, num_banks, banking_mode,
                  num_h_banks=1, num_v_banks=1, write_size=None):
    """
    Describe the ONE physical macro that gets generated, plus the array shape.

    Returns a dict; raises ValueError with an explicit message on any invalid
    combination. Every check here corresponds to something that used to be
    silently wrong: a truncating //, an unvalidated product, or a mode typo.
    """
    h, v = resolve_banking(banking_mode, num_banks, num_h_banks, num_v_banks)

    if not is_pow2(num_banks):
        raise ValueError("num_banks ({}) must be a power of 2.".format(num_banks))
    if not is_pow2(h):
        raise ValueError("num_h_banks ({}) must be a power of 2.".format(h))
    if not is_pow2(v):
        raise ValueError("num_v_banks ({}) must be a power of 2.".format(v))
    if h * v != num_banks:
        raise ValueError(
            "num_h_banks ({}) * num_v_banks ({}) = {} must equal num_banks ({}).".format(
                h, v, h * v, num_banks))
    if word_size % h:
        raise ValueError(
            "word_size ({}) must divide evenly by num_h_banks ({}).".format(word_size, h))
    if num_words % v:
        raise ValueError(
            "num_words ({}) must divide evenly by num_v_banks ({}).".format(num_words, v))

    word_size_per_bank = word_size // h
    if word_size_per_bank < MIN_BITS_PER_BANK:
        raise ValueError(
            "Per-macro word size {} bits (word_size {} / num_h_banks {}) is too "
            "narrow; {} bits is the practical minimum.".format(
                word_size_per_bank, word_size, h, MIN_BITS_PER_BANK))

    words_per_bank = num_words // v
    if words_per_bank < MIN_WORDS_PER_BANK:
        raise ValueError(
            "Per-macro depth {} words (num_words {} / num_v_banks {}) is below "
            "OpenRAM's minimum of {}.".format(
                words_per_bank, num_words, v, MIN_WORDS_PER_BANK))
    if words_per_bank > MAX_WORDS_PER_BANK:
        raise ValueError(
            "Per-macro depth {} words (num_words {} / num_v_banks {}) exceeds "
            "OpenRAM's maximum of {}. Increase num_v_banks.".format(
                words_per_bank, num_words, v, MAX_WORDS_PER_BANK))

    if write_size and word_size_per_bank % write_size:
        raise ValueError(
            "Per-macro word size {} bits must divide evenly by write_size ({}), "
            "otherwise the top-level and per-macro write-mask widths disagree.".format(
                word_size_per_bank, write_size))

    # num_words_per_bank is a true division on purpose: that is exactly what the
    # vertical path has always produced, so this expression reproduces it
    # bit-for-bit. Every consumer is either a float-safe product or an int()
    # truncation, and the operands are powers of 2, so the value is exact.
    return {
        "num_h_banks": h,
        "num_v_banks": v,
        "num_banks": num_banks,
        "original_word_size": word_size,
        "word_size_per_bank": word_size_per_bank,
        "words_per_bank": words_per_bank,
        "num_words_per_bank": num_words / v,
        "num_bits_per_bank": word_size_per_bank * (num_words / v),
        "bank_sel_bits": int(log(v, 2)),
    }


def address_sizes(num_rows, words_per_row, num_v_banks):
    """
    Address widths for a macro of num_rows x words_per_row in an array with
    num_v_banks vertical groups.

    addr_size is what the MACRO declares. This fork only ever builds a single
    sram_1bank, which decodes exactly col_addr_size + row_addr_size bits, so
    addr_size == bank_addr_size.

    Legacy OpenRAM set addr_size = bank_addr_size + log2(num_banks) here.
    sram_1bank.add_pins created those extra pins and characterizer/lib.py wrote
    them into address_width, but nothing ever routed them -- they left the LEF
    with an empty PORT, and disagreed with the ADDR_WIDTH that base/verilog.py
    writes into the behavioural model. On the shipped 45 nm macro that is
    addr0[11..13]: declared 14, decoded 11.

    top_addr_size is what the WRAPPER declares: the macro's bits plus the
    vertical-group select. It always equals log2(num_words), which is what keeps
    a wrapper drop-in compatible regardless of how the array is split.
    """
    if words_per_row not in VALID_WORDS_PER_ROW:
        raise ValueError(
            "words_per_row must be one of {}, got {}.".format(
                VALID_WORDS_PER_ROW, words_per_row))
    row_addr_size = (num_rows - 1).bit_length() if num_rows > 1 else 0
    col_addr_size = int(log(words_per_row, 2))
    bank_addr_size = col_addr_size + row_addr_size
    return {
        "row_addr_size": row_addr_size,
        "col_addr_size": col_addr_size,
        "bank_addr_size": bank_addr_size,
        "addr_size": bank_addr_size,
        "top_addr_size": bank_addr_size + int(log(num_v_banks, 2)),
    }
