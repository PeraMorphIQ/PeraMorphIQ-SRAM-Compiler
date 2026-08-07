#!/usr/bin/env python3
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
"""
Layer 1: the banking arithmetic.

Runs on a bare interpreter -- OpenRAM/compiler/banking.py imports nothing from
OpenRAM, so this tier needs no venv and no tech.
"""

import importlib.util
import math
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import cases  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "banking", REPO / "OpenRAM" / "compiler" / "banking.py")
banking = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(banking)


class TestResolveBanking(unittest.TestCase):

    def test_single_axis_modes(self):
        self.assertEqual(banking.resolve_banking("horizontal", 8), (8, 1))
        self.assertEqual(banking.resolve_banking("vertical", 8), (1, 8))
        self.assertEqual(banking.resolve_banking("mixed", 8, 4, 2), (4, 2))

    def test_unknown_mode_raises(self):
        # Used to fall through to vertical, so "Horizontal" built a vertical
        # macro whose generated file name said otherwise.
        for bad in ("Horizontal", "HORIZONTAL", "mixxed", "", None):
            with self.assertRaises(ValueError):
                banking.resolve_banking(bad, 4)


class TestBankGeometry(unittest.TestCase):

    # (mode, W, N, banks, h, v, word/bank, words/bank, bank_sel)
    TABLE = [
        ("horizontal", 1024, 2048, 8, 8, 1,  128, 2048, 0),
        ("vertical",   1024, 2048, 8, 1, 8, 1024,  256, 3),
        ("mixed",      1024, 2048, 8, 8, 1,  128, 2048, 0),
        ("mixed",      1024, 2048, 8, 4, 2,  256, 1024, 1),
        ("mixed",      1024, 2048, 8, 2, 4,  512,  512, 2),
        ("mixed",      1024, 2048, 8, 1, 8, 1024,  256, 3),
        ("mixed",        32,  512, 4, 2, 2,   16,  256, 1),
        ("horizontal",   32, 2048, 1, 1, 1,   32, 2048, 0),   # the default config
        ("vertical",     32, 2048, 1, 1, 1,   32, 2048, 0),
    ]

    def _geo(self, mode, W, N, banks, h, v):
        return banking.bank_geometry(W, N, banks, mode, h, v)

    def test_table(self):
        for mode, W, N, banks, h, v, wpb, npb, bs in self.TABLE:
            with self.subTest(mode=mode, W=W, N=N, h=h, v=v):
                g = self._geo(mode, W, N, banks, h, v)
                self.assertEqual(g["word_size_per_bank"], wpb)
                self.assertEqual(g["words_per_bank"], npb)
                self.assertEqual(g["bank_sel_bits"], bs)
                self.assertEqual(g["num_h_banks"] * g["num_v_banks"], banks)

    def test_conservation_of_bits(self):
        """The strongest single invariant: no bits created or destroyed."""
        for mode, W, N, banks, h, v, _, _, _ in self.TABLE:
            with self.subTest(mode=mode, h=h, v=v):
                g = self._geo(mode, W, N, banks, h, v)
                self.assertEqual(g["num_bits_per_bank"] * banks, W * N)

    def test_bank_sel_is_log2_v(self):
        for mode, W, N, banks, h, v, _, _, _ in self.TABLE:
            with self.subTest(mode=mode, h=h, v=v):
                g = self._geo(mode, W, N, banks, h, v)
                self.assertEqual(g["bank_sel_bits"], int(math.log(v, 2)))

    def test_degenerate_equivalence(self):
        """
        mixed(h=n, v=1) must equal horizontal(n), and mixed(h=1, v=n) must equal
        vertical(n), field for field. This is the cheapest zero-regression proof
        that unifying the three modes did not move either existing one.
        """
        for W, N, n in [(1024, 2048, 8), (32, 512, 4), (64, 256, 2), (128, 1024, 4)]:
            with self.subTest(W=W, N=N, n=n):
                self.assertEqual(
                    banking.bank_geometry(W, N, n, "mixed", n, 1),
                    banking.bank_geometry(W, N, n, "horizontal"))
                self.assertEqual(
                    banking.bank_geometry(W, N, n, "mixed", 1, n),
                    banking.bank_geometry(W, N, n, "vertical"))

    def test_errors_raise_not_truncate(self):
        bad = [
            # (kwargs, why)
            (dict(word_size=1024, num_words=2048, num_banks=8,
                  banking_mode="mixed", num_h_banks=4, num_v_banks=4),
             "h*v != num_banks"),
            (dict(word_size=100, num_words=2048, num_banks=8,
                  banking_mode="mixed", num_h_banks=8, num_v_banks=1),
             "word_size not divisible by h"),
            (dict(word_size=1024, num_words=100, num_banks=8,
                  banking_mode="mixed", num_h_banks=1, num_v_banks=8),
             "num_words not divisible by v"),
            (dict(word_size=1024, num_words=2048, num_banks=6,
                  banking_mode="mixed", num_h_banks=3, num_v_banks=2),
             "h not a power of 2"),
            (dict(word_size=1024, num_words=2048, num_banks=6,
                  banking_mode="mixed", num_h_banks=2, num_v_banks=3),
             "v not a power of 2"),
            (dict(word_size=32, num_words=2048, num_banks=8,
                  banking_mode="horizontal"),
             "per-macro word too narrow (4 bits)"),
            (dict(word_size=1024, num_words=64, num_banks=8,
                  banking_mode="vertical"),
             "per-macro depth 8 < 16"),
            (dict(word_size=1024, num_words=65536, num_banks=8,
                  banking_mode="horizontal"),
             "per-macro depth 65536 > 4096"),
            (dict(word_size=1024, num_words=2048, num_banks=8,
                  banking_mode="mixed", num_h_banks=8, num_v_banks=1,
                  write_size=24),
             "write_size does not divide the per-macro word"),
            (dict(word_size=1024, num_words=2048, num_banks=8,
                  banking_mode="Horizontal"),
             "unknown mode"),
        ]
        for kwargs, why in bad:
            with self.subTest(why=why):
                with self.assertRaises(ValueError, msg=why):
                    banking.bank_geometry(**kwargs)


class TestAddressSizes(unittest.TestCase):

    def test_macro_declares_only_what_it_decodes(self):
        """
        The regression test for the LEF stub-pin bug. Legacy OpenRAM set
        addr_size = bank_addr_size + log2(num_banks), so the shipped 45 nm macro
        declared 14 address pins while decoding 11; addr0[11..13] came out of
        the LEF with an empty PORT and the .lib overstated address_width.
        """
        for num_rows, wpr, v in [(2048, 1, 1), (256, 1, 8), (1024, 1, 2),
                                 (128, 4, 4), (512, 2, 2)]:
            with self.subTest(rows=num_rows, wpr=wpr, v=v):
                a = banking.address_sizes(num_rows, wpr, v)
                self.assertEqual(a["addr_size"], a["bank_addr_size"])

    def test_top_addr_width_is_log2_num_words(self):
        """
        What keeps a wrapper drop-in compatible: however the array is split,
        the wrapper's address width is always log2(total words).
        """
        for c in cases.ALL:
            with self.subTest(case=c.cid):
                g = cases.geometry(c)
                num_rows = g["words_per_bank"] // c.words_per_row
                a = banking.address_sizes(num_rows, c.words_per_row, c.v)
                self.assertEqual(a["top_addr_size"], int(math.log(c.num_words, 2)))
                self.assertEqual(a["bank_addr_size"], g["bank_addr_size"])

    def test_bad_words_per_row_raises(self):
        # amend_words_per_row() can return e.g. 3, after which
        # col_addr_size = int(log(3,2)) = 1 disagrees with num_cols = 3*word_size.
        for wpr in (3, 5, 6, 32, 0):
            with self.subTest(wpr=wpr):
                with self.assertRaises(ValueError):
                    banking.address_sizes(256, wpr, 1)


class TestSharedCaseTable(unittest.TestCase):

    def test_cases_agree_with_banking(self):
        """cases.geometry() and banking.bank_geometry() must not drift apart."""
        for c in cases.ALL:
            with self.subTest(case=c.cid):
                g = cases.geometry(c)
                b = banking.bank_geometry(c.word_size, c.num_words, c.num_banks,
                                          c.mode, c.h, c.v)
                self.assertEqual(g["bank_word_size"], b["word_size_per_bank"])
                self.assertEqual(g["words_per_bank"], b["words_per_bank"])
                self.assertEqual(g["bank_sel"], b["bank_sel_bits"])
                self.assertEqual(g["instances"], c.h * c.v)


class TestModuleIdentity(unittest.TestCase):

    def test_shadow_tree_is_not_the_live_one(self):
        """
        OpenRAM/openram/ is a stale shadow copy of OpenRAM/compiler/ that differs
        in exactly the banking files. OpenRAM/__init__.py puts compiler/ on
        __path__, so the shadow is unreachable -- but an ambient
        `export OPENRAM_HOME=.../OpenRAM/openram` would silently load it.
        Guard against anyone editing the wrong tree.
        """
        import orlib
        mb = orlib.multibank_class(banking_mode="vertical")
        self.assertIn("compiler/modules", sys.modules[mb.__module__].__file__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
