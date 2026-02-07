# See LICENSE for licensing information.
#
# Copyright (c) 2016-2024 Regents of the University of California, Santa Cruz
# All rights reserved.
#
import os
import re
from math import ceil, log
from openram import OPTS
from .template import template


class sram_multibank:

    def __init__(self, sram):
        rw_ports = [i for i in sram.all_ports if i in sram.read_ports and i in sram.write_ports]
        r_ports = [i for i in sram.all_ports if i in sram.read_ports and i not in sram.write_ports]
        w_ports = [i for i in sram.all_ports if i not in sram.read_ports and i in sram.write_ports]
        
        # Determine banking mode
        banking_mode = OPTS.get("banking_mode", "vertical")  # Default to vertical for backward compatibility
        
        # Calculate parameters based on banking mode
        if banking_mode == "horizontal":
            # Horizontal banking: word width divided across banks
            bank_data_width = sram.word_size // sram.num_banks
            addr_width = sram.bank_addr_size  # No bank select bits needed
            bank_sel = 0  # Not used in horizontal mode
        else:
            # Vertical banking: address space divided across banks
            bank_data_width = sram.word_size
            addr_width = sram.bank_addr_size + ceil(log(sram.num_banks, 2))
            bank_sel = ceil(log(sram.num_banks, 2))
        
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
            'data_width': sram.word_size,
            'bank_data_width': bank_data_width,
            'addr_width': addr_width,
            'bank_sel': bank_sel,
            'num_wmask': sram.num_wmasks,
            'write_size': sram.write_size,
            'banking_mode': banking_mode
        }

    def verilog_write(self, name):
        # Select template based on banking mode
        banking_mode = self.dict.get('banking_mode', 'vertical')
        
        if banking_mode == "horizontal":
            template_filename = os.path.join(os.path.abspath(os.environ["OPENRAM_HOME"]), 
                                            "modules/sram_multibank_horizontal_template.v")
        else:
            template_filename = os.path.join(os.path.abspath(os.environ["OPENRAM_HOME"]), 
                                            "modules/sram_multibank_template.v")
        
        t = template(template_filename, self.dict)
        t.write(name)
        with open(name, 'r') as f:
            text = f.read()
            badComma = re.compile(r',(\s*\n\s*\);)')
            text = badComma.sub(r'\1', text)
        with open(name, 'w') as f:
            f.write(text)
