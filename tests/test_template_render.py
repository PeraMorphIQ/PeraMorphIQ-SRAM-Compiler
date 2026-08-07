#!/usr/bin/env python3
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
"""
Layer 2: wrapper rendering.

The first test is the gate: horizontal N=8 must render byte-identically to the
committed rtl/weight_resolver/..._8h_top.v. If mixed-banking support moved the
horizontal path at all, that fails.

Runs on a bare interpreter (see orlib).
"""

import difflib
import pathlib
import re
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import orlib  # noqa: E402

BUILD = HERE / "build" / "render"
GOLDEN = HERE / "golden"

# The shipped 45 nm macro. Its _top.v is committed RTL, compiled into the
# blackbox testbench and the PrimePower flow.
SHIPPED_8H = "sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h"
SHIPPED_8V = "sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v"


def render(mode, W, N, banks, h, v, name, bank_addr_size=None, num_wmasks=0,
           write_size=None):
    BUILD.mkdir(parents=True, exist_ok=True)
    mb = orlib.multibank_class(banking_mode=mode)
    s = orlib.make_sram(W, N, banks, h=h, v=v, name=name,
                        bank_addr_size=bank_addr_size,
                        num_wmasks=num_wmasks, write_size=write_size)
    path = BUILD / (name + "_top.v")
    obj = mb(s)
    obj.verilog_write(str(path))
    return path.read_text(), obj.dict


def strip_header(text):
    """Drop the leading comment block so two modes can be compared on substance."""
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and (lines[i].startswith("//") or not lines[i].strip()):
        i += 1
    return "".join(lines[i:])


class TestGoldenRegression(unittest.TestCase):

    def test_horizontal_8h_is_byte_identical_to_shipped(self):
        got, d = render("horizontal", 1024, 2048, 8, 8, 1, SHIPPED_8H,
                        bank_addr_size=11)
        want = (GOLDEN / (SHIPPED_8H + "_top.v")).read_text()
        if got != want:
            diff = "".join(difflib.unified_diff(
                want.splitlines(keepends=True), got.splitlines(keepends=True),
                fromfile="golden", tofile="rendered"))
            self.fail("horizontal path changed:\n" + diff)
        self.assertEqual(d["data_width"], 1024)
        self.assertEqual(d["bank_data_width"], 128)
        self.assertEqual(d["addr_width"], 11)
        self.assertEqual(d["bank_sel"], 0)

    def test_vertical_8v_matches_golden(self):
        got, d = render("vertical", 1024, 2048, 8, 1, 8, SHIPPED_8V,
                        bank_addr_size=8)
        want = (GOLDEN / (SHIPPED_8V + "_top.v")).read_text()
        self.assertEqual(got, want, "vertical path changed")
        self.assertEqual(d["addr_width"], 11)
        self.assertEqual(d["bank_sel"], 3)


class TestMixedRender(unittest.TestCase):

    SPLITS = [(8, 1), (4, 2), (2, 4), (1, 8)]

    def _mixed(self, h, v, W=1024, N=2048, banks=8):
        name = "sram_{}b_{}_1rw_freepdk45_sram_{}x{}_{}h{}v".format(W, N, W, N, h, v)
        bank_addr = (N // v - 1).bit_length()
        return render("mixed", W, N, banks, h, v, name, bank_addr_size=bank_addr)

    def test_parameters(self):
        for h, v in self.SPLITS:
            with self.subTest(h=h, v=v):
                text, d = self._mixed(h, v)
                self.assertEqual(d["data_width"], 1024)
                self.assertEqual(d["bank_data_width"], 1024 // h)
                self.assertEqual(d["bank_sel"], (v - 1).bit_length())
                # Always 11 = log2(2048), whatever the split.
                self.assertEqual(d["addr_width"], 11)
                self.assertEqual(
                    int(re.search(r"parameter DATA_WIDTH\s*=\s*(\d+)", text).group(1)), 1024)
                self.assertEqual(
                    int(re.search(r"parameter ADDR_WIDTH\s*=\s*(\d+)", text).group(1)), 11)

    def test_instance_count_and_unique_names(self):
        for h, v in self.SPLITS:
            with self.subTest(h=h, v=v):
                text, _ = self._mixed(h, v)
                names = re.findall(r"\bbank_v(\d+)_h(\d+)\b", text)
                self.assertEqual(len(set(names)), h * v)
                insts = re.findall(r"^\s+\S+ (bank_v\d+_h\d+) \($", text, re.M)
                self.assertEqual(len(insts), h * v)
                self.assertEqual(len(set(insts)), h * v, "duplicate instance name")

    def test_din_slices_tile_exactly(self):
        for h, v in self.SPLITS:
            with self.subTest(h=h, v=v):
                text, d = self._mixed(h, v)
                sl = sorted({(int(a), int(b))
                             for a, b in re.findall(r"din0\[(\d+) : (\d+)\]", text)},
                            key=lambda x: x[1])
                self.assertEqual(len(sl), h, "expected one slice per h-bank")
                cov = 0
                for hi, lo in sl:
                    self.assertEqual(lo, cov, "gap or overlap in din slices")
                    self.assertEqual(hi - lo + 1, d["bank_data_width"])
                    cov = hi + 1
                self.assertEqual(cov, d["data_width"])

    def test_no_negative_or_reversed_ranges(self):
        """v == 1 makes BANK_SEL 0; every construct that would emit [-1:0] or a
        reversed range must be guarded out."""
        for h, v in self.SPLITS + [(2, 1), (1, 1)]:
            if h * v == 1:
                continue
            with self.subTest(h=h, v=v):
                text, _ = self._mixed(h, v, banks=h * v)
                self.assertNotIn("[-1 :", text)
                self.assertNotIn("[-1:", text)
                for hi, lo in re.findall(r"\[(\d+) : (\d+)\]", text):
                    self.assertGreaterEqual(int(hi), int(lo),
                                            "reversed part-select in {}h{}v".format(h, v))

    def test_no_unexpanded_tokens(self):
        for h, v in self.SPLITS:
            with self.subTest(h=h, v=v):
                text, _ = self._mixed(h, v)
                self.assertEqual(re.findall(r"\{\{.*?\}\}|\{%.*?%\}", text), [])

    def test_degenerate_matches_single_axis_modes(self):
        """
        mixed(h=8,v=1) and horizontal(8) must be identical below the header
        comment; likewise mixed(h=1,v=8) and vertical(8). The wrappers differ
        only in instance naming style, so compare structure, not bytes.
        """
        mh, _ = self._mixed(8, 1)
        mv, _ = self._mixed(1, 8)
        hh, _ = render("horizontal", 1024, 2048, 8, 8, 1, SHIPPED_8H, bank_addr_size=11)
        vv, _ = render("vertical", 1024, 2048, 8, 1, 8, SHIPPED_8V, bank_addr_size=8)

        def sig(t):
            """
            The externally visible contract: port names, directions and widths,
            plus the slice decomposition.

            Deliberately normalised for two differences that are invisible at
            the module boundary:
              * whitespace inside range expressions;
              * `output reg` vs `output`. The mixed template always drives dout
                from an always @(*) mux (even at v == 1, where it degenerates to
                a single assignment), while the horizontal template uses a
                continuous assign to a wire. Both are combinational and
                synthesise identically; the port is `output [W-1:0]` either way.
            Behavioural equivalence is proven separately by the VCS testbench,
            which runs the same source against mixed(h,1) and horizontal(h).
            """
            ports = []
            for direction, width, nm in re.findall(
                    r"^\s+(input|output reg|output)\s+(\[[^\]]+\]\s*)?(\w+);", t, re.M):
                ports.append(("output" if direction.startswith("output") else "input",
                              re.sub(r"\s+", "", width or ""),
                              nm))
            dw = int(re.search(r"parameter DATA_WIDTH\s*=\s*(\d+)", t).group(1))
            # Distinct din bit-ranges each macro is fed. The vertical template
            # connects `.din0(din0)` bare where the mixed one emits an explicit
            # full-width part-select `din0[W-1:0]`; normalise an absent slice to
            # the full range so the two compare equal.
            slices = {(int(a), int(b))
                      for a, b in re.findall(r"din0\[(\d+) : (\d+)\]", t)}
            if not slices:
                slices = {(dw - 1, 0)}
            return (
                sorted(ports),
                dw,
                int(re.search(r"parameter ADDR_WIDTH\s*=\s*(\d+)", t).group(1)),
                sorted(slices),
            )

        self.assertEqual(sig(mh), sig(hh), "mixed(8h,1v) != horizontal(8)")
        self.assertEqual(sig(mv), sig(vv), "mixed(1h,8v) != vertical(8)")

    def test_wmask_slices_tile(self):
        """
        The horizontal template connects one mask bit per bank to an N-bit macro
        port and declares the top mask at the per-macro width. The mixed
        template slices it properly; check that.
        """
        name = "sram_1024b_2048_1rw_freepdk45_sram_1024x2048_4h2v_wm"
        text, d = render("mixed", 1024, 2048, 8, 4, 2, name,
                         bank_addr_size=10, num_wmasks=32, write_size=8)
        self.assertEqual(d["top_num_wmask"], 32 * 4)
        self.assertEqual(d["bank_num_wmask"], 32)
        self.assertEqual(
            int(re.search(r"parameter NUM_WMASK\s*=\s*(\d+)", text).group(1)), 128)
        sl = sorted({(int(a), int(b))
                     for a, b in re.findall(r"wmask0\[(\d+) : (\d+)\]", text)},
                    key=lambda x: x[1])
        self.assertEqual(len(sl), 4)
        cov = 0
        for hi, lo in sl:
            self.assertEqual(lo, cov)
            self.assertEqual(hi - lo + 1, 32)
            cov = hi + 1
        self.assertEqual(cov, 128)


class TestGuards(unittest.TestCase):

    def test_horizontal_with_write_mask_is_refused(self):
        """
        Known-broken path: rather than silently emit a wrapper that connects one
        mask bit to a 16-bit port, sram_multibank errors and points at mixed.
        """
        with self.assertRaises(orlib.StubDebug.Error) as cm:
            render("horizontal", 1024, 2048, 8, 8, 1, SHIPPED_8H,
                   bank_addr_size=11, num_wmasks=16, write_size=8)
        self.assertIn("mixed", str(cm.exception))

    def test_unknown_banking_mode_is_refused(self):
        with self.assertRaises(orlib.StubDebug.Error):
            render("Horizontal", 1024, 2048, 8, 8, 1, SHIPPED_8H, bank_addr_size=11)

    def test_unexpanded_token_guard_fires(self):
        """
        Negative control for the guard itself: corrupt the template dict so a
        substitution cannot resolve, and require an error rather than a file
        containing a literal token.
        """
        mb = orlib.multibank_class(banking_mode="mixed")
        s = orlib.make_sram(1024, 2048, 8, h=4, v=2,
                            name="sram_probe", bank_addr_size=10)
        obj = mb(s)
        del obj.dict["bank_data_width"]
        BUILD.mkdir(parents=True, exist_ok=True)
        with self.assertRaises(orlib.StubDebug.Error) as cm:
            obj.verilog_write(str(BUILD / "sram_probe_top.v"))
        self.assertIn("Unexpanded template token", str(cm.exception))


class TestCaseTableRenders(unittest.TestCase):

    def test_every_case_renders_cleanly(self):
        for c in cases.ALL:
            with self.subTest(case=c.cid):
                g = cases.geometry(c)
                name = cases.macro_name(c)
                text, d = render(c.mode, c.word_size, c.num_words, c.num_banks,
                                 c.h, c.v, name,
                                 bank_addr_size=g["bank_addr_size"])
                self.assertEqual(d["addr_width"], g["top_addr_size"])
                self.assertEqual(d["bank_data_width"], g["bank_word_size"])
                self.assertEqual(re.findall(r"\{\{.*?\}\}|\{%.*?%\}", text), [])
                self.assertNotIn("[-1", text)
                n = len(re.findall(r"^\s+%s \w+ \($" % re.escape(name), text, re.M))
                self.assertEqual(n, g["instances"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
