# See LICENSE for licensing information.
#
# Copyright (c) 2016-2024 Regents of the University of California, Santa Cruz
# All rights reserved.
#
import os
import re
from math import log
from openram import debug
from openram import OPTS
from .template import template

TEMPLATES = {
    "horizontal": "modules/sram_multibank_horizontal_template.v",
    "vertical":   "modules/sram_multibank_template.v",
    "mixed":      "modules/sram_multibank_mixed_template.v",
}


class sram_multibank:
    """
    Builds the Verilog-only <name>_top.v wrapper that instantiates the ONE
    generated macro num_h_banks * num_v_banks times.

    There is deliberately no _top.lef / _top.lib / _top.db / _top.gds: only a
    single physical macro is ever generated, and this wrapper is RTL glue.
    """

    def __init__(self, sram):
        rw_ports = [i for i in sram.all_ports if i in sram.read_ports and i in sram.write_ports]
        r_ports = [i for i in sram.all_ports if i in sram.read_ports and i not in sram.write_ports]
        w_ports = [i for i in sram.all_ports if i not in sram.read_ports and i in sram.write_ports]

        banking_mode = getattr(OPTS, "banking_mode", "vertical")
        if banking_mode not in TEMPLATES:
            debug.error("Unknown banking_mode {!r}. Expected one of {}.".format(
                banking_mode, ", ".join(sorted(TEMPLATES))), -1)

        # (h, v) array shape, resolved once in sram_config and copied here by
        # set_local_config. No getattr fallback: a silent 1 builds the wrong
        # wrapper for a mixed config.
        h_banks = sram.num_h_banks
        v_banks = sram.num_v_banks
        bank_sel = int(log(v_banks, 2))

        # sram.word_size is already the PER-MACRO width; original_word_size is
        # the full top-level word. For h == 1 they are equal, which is why this
        # single expression reproduces both legacy branches:
        #   horizontal -> data_width = original_word_size, addr_width = bank_addr_size
        #   vertical   -> data_width = word_size,          addr_width = bank_addr_size + log2(N)
        bank_data_width = sram.word_size
        data_width = sram.original_word_size
        addr_width = sram.bank_addr_size + bank_sel

        # The horizontal template connects ONE mask bit per bank
        # (wmask{port}[{bank}]) to what is an num_wmasks-bit macro port, and
        # declares the top-level mask at the per-macro width. Both are wrong for
        # num_wmasks > 1. The shipped 8h macro has num_wmasks == 0 so it is
        # unaffected; refuse rather than silently emit a broken wrapper.
        if banking_mode == "horizontal" and sram.num_wmasks > 1 and h_banks > 1:
            debug.error(
                "Horizontal banking with a write mask (num_wmasks={}) is not "
                "supported: the wrapper template would connect 1 mask bit to an "
                "{}-bit macro port and declare the top-level mask {}x too narrow. "
                "Use banking_mode='mixed' with num_v_banks=1, which slices the "
                "mask correctly.".format(sram.num_wmasks, sram.num_wmasks, h_banks), -1)

        # Generate bank output concatenation string (legacy horizontal template
        # only). dout = {dout0_bank1, dout0_bank0} (MSB first).
        bank_outputs = [f"dout0_bank{b}" for b in reversed(range(sram.num_banks))]
        dout_concat = ", ".join(bank_outputs)

        self.dict = {
            'module_name': sram.name + '_top',
            'bank_module_name': sram.name,
            'vdd': 'vdd',
            'gnd': 'gnd',
            'ports': sram.all_ports,
            'rw_ports': rw_ports,
            'r_ports': r_ports,
            'w_ports': w_ports,
            'banks': list(range(sram.num_banks)),
            'num_banks': sram.num_banks,
            'data_width': data_width,
            'bank_data_width': bank_data_width,
            'addr_width': addr_width,
            'bank_sel': bank_sel,
            'num_wmask': sram.num_wmasks,
            'write_size': sram.write_size,
            'banking_mode': banking_mode,
            'dout_concat': dout_concat,

            # --- mixed template only -------------------------------------------
            # Loop keys must be literal dict entries; the engine cannot iterate
            # over an expression.
            'v_groups': list(range(v_banks)),
            'h_slices': list(range(h_banks)),
            'num_h_banks': h_banks,
            'num_v_banks': v_banks,
            'bank_addr_width': sram.bank_addr_size,
            'bank_num_wmask': sram.num_wmasks,          # per-macro mask bits
            'top_num_wmask': sram.num_wmasks * h_banks, # full-word mask bits
        }

    def verilog_write(self, name):
        banking_mode = self.dict.get('banking_mode', 'vertical')
        template_filename = os.path.join(os.path.abspath(os.environ["OPENRAM_HOME"]),
                                         TEMPLATES[banking_mode])

        t = template(template_filename, self.dict)
        t.write(name)
        with open(name, 'r') as f:
            text = f.read()
            badComma = re.compile(r',(\s*\n\s*\);)')
            text = badComma.sub(r'\1', text)

        # template.py swallows evaluation errors and emits the literal token, so
        # a one-character typo ships {{ bank_dat_width }} into generated Verilog
        # and only fails hours later at elaboration. None of the templates emits
        # '{{' or '{%' in valid output (Verilog replication is '{4{1'b0}}',
        # never '{{'), so any survivor is a bug.
        residue = re.findall(r'\{\{.*?\}\}|\{%.*?%\}', text)
        if residue:
            debug.error("Unexpanded template token(s) in {}: {}".format(
                name, sorted(set(residue))), -1)

        with open(name, 'w') as f:
            f.write(text)
