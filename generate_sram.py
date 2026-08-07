#!/usr/bin/env python3
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
#
# This file is part of Pera-OpenRAM.
# Developed by the PeraCom Neuromorphic Research Group.
#
# Author: PeraMorphIQ Team

"""
PeraMorphIQ SRAM Generator
==========================
A streamlined OpenRAM-based SRAM compiler with automated output organization.

Usage:
    python generate_sram.py

Configuration:
    Edit config.py to customize your SRAM parameters.
"""

import sys
import os
import shutil
import glob

# Add the parent directory so Python can find the openram package
parent_dir = os.path.expanduser("./")
sys.setrecursionlimit(5000000)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import OpenRAM package
import importlib.util

import_spec = importlib.util.spec_from_file_location(
    "openram", 
    os.path.join(parent_dir, "OpenRAM", "__init__.py"),
    submodule_search_locations=[os.path.join(parent_dir, "OpenRAM")]
)

openram = importlib.util.module_from_spec(import_spec)
sys.modules["openram"] = openram
import_spec.loader.exec_module(openram)

# -----------------------------------------------------------------------------
# Guard: OPENRAM_HOME must point at THIS checkout's OpenRAM/compiler.
# -----------------------------------------------------------------------------
# OpenRAM/__init__.py honours an ambient $OPENRAM_HOME, and sram_multibank builds
# its Verilog template path from it. OpenRAM/openram/ is a stale shadow copy of
# OpenRAM/compiler/ that differs in exactly the banking files, so a leftover
# `export OPENRAM_HOME=.../OpenRAM/openram` would silently load the shadow
# sram_config and the shadow templates and emit a wrong _top.v with no error.
_expected_home = os.path.realpath(os.path.join(parent_dir, "OpenRAM", "compiler"))
_actual_home = os.path.realpath(openram.OPENRAM_HOME)
if _actual_home != _expected_home:
    sys.exit(
        "ERROR: OPENRAM_HOME does not point at this checkout.\n"
        "  expected: {}\n"
        "  actual:   {}\n"
        "Unset OPENRAM_HOME (or point it at the expected path) and re-run.".format(
            _expected_home, _actual_home))

# Import OpenRAM modules
from openram import globals
from openram import sram_config
from openram import sram

# =============================================================================
# Load Configuration
# =============================================================================
print("="*70)
print("  OpenRAM SRAM Generator")
print("="*70)

# Import user configuration
import config

banking_mode = getattr(config, 'banking_mode', 'vertical')

# Resolve the (h, v) array shape through the same helper the compiler uses, so
# the banner can never disagree with what is actually built.
from openram import resolve_banking

try:
    h_banks, v_banks = resolve_banking(banking_mode,
                                       config.num_banks,
                                       getattr(config, 'num_h_banks', 1),
                                       getattr(config, 'num_v_banks', 1))
except ValueError as e:
    sys.exit("ERROR: {}".format(e))

print(f"Configuration:")
print(f"  Technology:  {config.tech_name}")
print(f"  Word Size:   {config.word_size} bits")
print(f"  Num Words:   {config.num_words}")
print(f"  Num Banks:   {config.num_banks}")
print(f"  Banking Mode: {banking_mode}  ({h_banks}h x {v_banks}v)")
print(f"  SRAM Name:   {config.sram_name}")
print(f"  Threads:     {config.num_threads}")

# =============================================================================
# Initialize OpenRAM
# =============================================================================
globals.init_openram("config")
globals.OPTS.num_threads = config.num_threads

# Set banking mode. read_config already copies these from config.py, but set
# them explicitly so a config that omits num_h_banks/num_v_banks still gets the
# resolved pair rather than options.py's (1, 1).
globals.OPTS.banking_mode = banking_mode
globals.OPTS.num_h_banks = h_banks
globals.OPTS.num_v_banks = v_banks
print(f"\n  Banking mode set to: {banking_mode} ({h_banks}h x {v_banks}v)")

# =============================================================================
# Setup Output Directory Structure
# =============================================================================
output_base = "./outputs"
subdirs = ["designs", "libs", "verilog", "spice", "reports", "stimulus", 
           "ndm", "db", "logs", "configs"]

for subdir in subdirs:
    os.makedirs(os.path.join(output_base, subdir), exist_ok=True)

globals.OPTS.output_path = os.path.abspath(output_base) + "/"

# =============================================================================
# Generate SRAM
# =============================================================================
print(f"\nGenerating SRAM...")

conf = sram_config(word_size=config.word_size,
                   num_words=config.num_words,
                   num_banks=config.num_banks)

s = sram(sram_config=conf, name=config.sram_name)
s.save()

# Get the actual generated name (OpenRAM uses its own naming convention)
actual_sram_name = s.s.name
print(f"\n  OpenRAM generated name: {actual_sram_name}")

# =============================================================================
# Organize Output Files
# =============================================================================
design_name = actual_sram_name
print(f"\n{'='*70}")
print(f"  Organizing Output Files for {design_name}")
print(f"{'='*70}")

# Define file moves
file_moves = {
    "designs": ["*.gds", "*.lef"],
    "libs": ["*.lib"],
    "db": ["*.db"],
    "verilog": ["*.v"],
    "spice": ["*.sp", "*.lvs.sp"],
    "stimulus": ["*_stim.sp", "*_meas.sp"],
    "reports": ["*.html"],
    "configs": ["*.py"],
    "logs": ["*.log"]
}

# Move files to organized directories
for dest_dir, patterns in file_moves.items():
    for pattern in patterns:
        for f in glob.glob(os.path.join(output_base, pattern)):
            # Skip __init__.py
            if dest_dir == "configs" and os.path.basename(f) == "__init__.py":
                continue
            
            dest = os.path.join(output_base, dest_dir, os.path.basename(f))
            if os.path.exists(f):
                shutil.move(f, dest)
                print(f"  [OK] {os.path.basename(f):40s} -> {dest_dir}/")

# =============================================================================
# Update Post-Processing Script Configuration
# =============================================================================
print(f"\n{'='*70}")
print(f"  Updating Post-Processing Script")
print(f"{'='*70}")

post_process_script = "run_post_process.sh"

# Read current script
with open(post_process_script, 'r') as f:
    script_content = f.read()

# Update SRAM_NAME
import re
script_content = re.sub(
    r'SRAM_NAME="[^"]*"',
    f'SRAM_NAME="{design_name}"',
    script_content
)

# Write back
with open(post_process_script, 'w') as f:
    f.write(script_content)

print(f"  [OK] Updated SRAM_NAME to: {design_name}")

# =============================================================================
# Summary
# =============================================================================
print(f"\n{'='*70}")
print(f"  Generation Complete!")
print(f"{'='*70}")
print(f"\nGenerated SRAM: {design_name}")
print(f"  Architecture: {config.word_size}b x {config.num_words}w x {config.num_banks}banks")
print(f"  Banking Mode: {banking_mode}  ({h_banks}h x {v_banks}v)")
print(f"  Each macro:   {config.word_size // h_banks}b x {config.num_words // v_banks}w")
print(f"  Macro count:  {h_banks} slices x {v_banks} groups = {h_banks * v_banks}")
print(f"  Total bits:   {config.word_size * config.num_words}")

# The macro's declared address width must match what it decodes. A mismatch
# means the LEF carries address pins with no geometry and the .lib overstates
# address_width, which surfaces much later as NDM-031 Port missing.
_declared = s.s.addr_size
_decoded = s.s.bank_addr_size
print(f"  Macro addr:   declared {_declared} bits, decodes {_decoded} bits")
if _declared != _decoded:
    print(f"  *** WARNING: macro declares addr[{_declared - 1}:{_decoded}] with no")
    print(f"      geometry. LEF/.lib will not match the Verilog model.")
if h_banks * v_banks > 1:
    print(f"  Wrapper:      {design_name}_top.v "
          f"({_decoded + (v_banks - 1).bit_length()} addr bits, "
          f"{config.word_size} data bits)")
    print(f"  NOTE: <name>_top.v is RTL glue only -- there is no _top.lef,")
    print(f"        _top.lib, _top.db or _top.gds. Only ONE macro is generated.")
print(f"\nOutput files organized in: {output_base}/")
print(f"  - Designs (GDS/LEF):  {output_base}/designs/")
print(f"  - Liberty files:      {output_base}/libs/")
print(f"  - Verilog models:     {output_base}/verilog/")
print(f"  - SPICE netlists:     {output_base}/spice/")
print(f"  - Reports:            {output_base}/reports/")
print(f"\nNext steps:")
print(f"  1. Run post-processing: ./run_post_process.sh --all")
print(f"  2. Check NDM generation: ls {output_base}/ndm/")
print(f"  3. Integrate into design flow")
print()