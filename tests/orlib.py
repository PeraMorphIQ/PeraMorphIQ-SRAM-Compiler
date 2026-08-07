# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
"""
Load OpenRAM's sram_multibank with a stub `openram` package.

sram_multibank needs only os.environ["OPENRAM_HOME"], `from openram import OPTS`,
`from openram import debug` and `from .template import template` -- so it can be
exercised with no OpenRAM initialisation, no tech, and no third-party
dependencies. That is what keeps the fast test tier runnable on a bare
interpreter.
"""

import importlib.util
import os
import pathlib
import sys
import types

REPO = pathlib.Path(__file__).resolve().parents[1]
OR = REPO / "OpenRAM" / "compiler"

# sram_multibank builds its template path from this.
os.environ["OPENRAM_HOME"] = str(OR)


class StubDebug:
    """Minimal stand-in for openram.debug: errors raise instead of exiting."""

    class Error(Exception):
        pass

    @staticmethod
    def error(msg, code=-1):
        raise StubDebug.Error(msg)

    @staticmethod
    def check(cond, msg):
        if not cond:
            raise StubDebug.Error(msg)

    @staticmethod
    def info(level, msg):
        pass

    @staticmethod
    def warning(msg):
        pass


def _install_stub_openram(**opts):
    fake = types.ModuleType("openram")

    class _Opts:
        pass

    fake.OPTS = _Opts()
    for k, v in opts.items():
        setattr(fake.OPTS, k, v)
    fake.debug = StubDebug
    fake.__path__ = []  # let openram.tech resolve as a submodule
    sys.modules["openram"] = fake

    # base/verilog.py does `from openram.tech import spice`. Only the key names
    # are consulted, so a minimal mapping is enough.
    tech = types.ModuleType("openram.tech")
    tech.spice = {"vdd_name": "vdd", "gnd_name": "gnd"}
    sys.modules["openram.tech"] = tech
    fake.tech = tech

    pkg = types.ModuleType("orm")
    pkg.__path__ = [str(OR / "modules")]
    sys.modules["orm"] = pkg


def _load(name, filename):
    spec = importlib.util.spec_from_file_location("orm." + name, OR / "modules" / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["orm." + name] = mod
    spec.loader.exec_module(mod)
    return mod


def multibank_class(**opts):
    """Return the sram_multibank class, with OPTS populated from **opts."""
    _install_stub_openram(**opts)
    _load("template", "template.py")
    return _load("sram_multibank", "sram_multibank.py").sram_multibank


class FakeSram:
    """
    Stand-in for the sram_1bank object sram_multibank consumes.

    __getattr__ raises on anything not explicitly set, so the stub cannot
    silently drift from the real object: if sram_multibank starts reading a new
    attribute, the tests fail loudly instead of picking up a None.
    """

    _FIELDS = (
        "all_ports", "read_ports", "write_ports",
        "word_size", "original_word_size",
        "num_banks", "num_h_banks", "num_v_banks",
        "bank_addr_size", "num_wmasks", "write_size", "name",
    )

    def __init__(self, **kwargs):
        unknown = set(kwargs) - set(self._FIELDS)
        if unknown:
            raise AssertionError("unknown FakeSram field(s): {}".format(sorted(unknown)))
        object.__setattr__(self, "_set", dict(kwargs))
        object.__setattr__(self, "touched", set())

    def __getattr__(self, item):
        if item.startswith("_"):
            raise AttributeError(item)
        store = object.__getattribute__(self, "_set")
        if item not in store:
            raise AssertionError(
                "sram_multibank read undeclared attribute {!r}; add it to "
                "FakeSram._FIELDS and to the test cases".format(item))
        object.__getattribute__(self, "touched").add(item)
        return store[item]


def bank_model_writer():
    """
    Return OpenRAM's own base/verilog.py `verilog` mixin.

    The behavioural bank model used by the testbenches is produced by the real
    compiler code, not hand-written, so a change to verilog.py cannot drift away
    from what the tests exercise. Note it writes ADDR_WIDTH = bank_addr_size --
    the per-macro width, which is also what addr_size is now.
    """
    _install_stub_openram()
    spec = importlib.util.spec_from_file_location(
        "orbase.verilog", OR / "base" / "verilog.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["orbase.verilog"] = mod
    spec.loader.exec_module(mod)
    return mod.verilog


def write_bank_model(path, name, word_size, num_words, bank_addr_size,
                     num_wmasks=0, write_size=None):
    """Emit the single-macro behavioural model via OpenRAM's own writer."""
    base = bank_model_writer()

    class _Bank(base):
        pass

    b = _Bank()
    b.name = name
    b.word_size = word_size
    b.num_words = num_words
    # verilog.py only emits the wmask port when write_size != word_size.
    b.write_size = write_size if write_size is not None else word_size
    b.num_wmasks = num_wmasks
    b.num_spare_cols = 0
    b.num_banks = 1
    b.bank_addr_size = bank_addr_size
    b.all_ports = [0]
    b.readwrite_ports = [0]
    b.read_ports = [0]
    b.write_ports = [0]
    b.vdd_name = "vdd"
    b.gnd_name = "gnd"
    b.verilog_write(str(path))
    return path


def make_sram(word_size, num_words, num_banks, h, v, name,
              num_wmasks=0, write_size=None, bank_addr_size=None,
              words_per_row=1):
    """
    Build a FakeSram the way sram_config would, for a (h, v) split.

    bank_addr_size defaults to log2(num_words / v) with words_per_row folded in,
    matching address_sizes(): row bits + column-mux bits.
    """
    per_bank_words = num_words // v
    if bank_addr_size is None:
        num_rows = per_bank_words // words_per_row
        bank_addr_size = (num_rows - 1).bit_length() + (words_per_row - 1).bit_length()
    per_bank_word_size = word_size // h
    return FakeSram(
        all_ports=[0],
        read_ports=[0],
        write_ports=[0],
        word_size=per_bank_word_size,
        original_word_size=word_size,
        num_banks=num_banks,
        num_h_banks=h,
        num_v_banks=v,
        bank_addr_size=bank_addr_size,
        num_wmasks=num_wmasks,
        write_size=write_size if write_size is not None else per_bank_word_size,
        name=name,
    )
