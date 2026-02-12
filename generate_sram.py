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
num_rw_ports = getattr(config, 'num_rw_ports', 1)
num_r_ports = getattr(config, 'num_r_ports', 0)
num_w_ports = getattr(config, 'num_w_ports', 0)

# Validate port configuration
total_ports = num_rw_ports + num_r_ports + num_w_ports
if total_ports < 1 or total_ports > 2:
    print(f"\nERROR: Invalid port configuration!")
    print(f"  Total ports (num_rw_ports + num_r_ports + num_w_ports) must be 1 or 2")
    print(f"  Current: {num_rw_ports} RW + {num_r_ports} R + {num_w_ports} W = {total_ports} total")
    sys.exit(1)

print(f"Configuration:")
print(f"  Technology:  {config.tech_name}")
print(f"  Word Size:   {config.word_size} bits")
print(f"  Num Words:   {config.num_words}")
print(f"  Num Banks:   {config.num_banks}")
print(f"  Banking Mode: {banking_mode}")
print(f"  Port Config: {num_rw_ports} RW + {num_r_ports} R + {num_w_ports} W ({total_ports} port{'s' if total_ports > 1 else ''})")
print(f"  SRAM Name:   {config.sram_name}")
print(f"  Threads:     {config.num_threads}")

# =============================================================================
# Initialize OpenRAM
# =============================================================================
globals.init_openram("config")
globals.OPTS.num_threads = config.num_threads

# Set port configuration
globals.OPTS.num_rw_ports = num_rw_ports
globals.OPTS.num_r_ports = num_r_ports
globals.OPTS.num_w_ports = num_w_ports

# Set banking mode
if hasattr(config, 'banking_mode'):
    globals.OPTS.banking_mode = config.banking_mode
    print(f"\n  Banking mode set to: {config.banking_mode}")
print(f"  Port configuration set to: {num_rw_ports} RW, {num_r_ports} R, {num_w_ports} W")

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
print(f"  Port Config:  {num_rw_ports} RW + {num_r_ports} R + {num_w_ports} W")
if total_ports == 1:
    print(f"  Port Type:    Single-port")
else:
    port_types = []
    if num_rw_ports > 0:
        port_types.append(f"{num_rw_ports} RW")
    if num_r_ports > 0:
        port_types.append(f"{num_r_ports} R")
    if num_w_ports > 0:
        port_types.append(f"{num_w_ports} W")
    print(f"  Port Type:    Dual-port ({', '.join(port_types)})")
print(f"  Banking Mode: {banking_mode}")
if banking_mode == "horizontal":
    bits_per_bank = config.word_size // config.num_banks
    print(f"  Each bank:    {bits_per_bank}b x {config.num_words}w (horizontal bit-slicing)")
else:
    words_per_bank = config.num_words // config.num_banks
    print(f"  Each bank:    {config.word_size}b x {words_per_bank}w (vertical address division)")
print(f"  Total bits:   {config.word_size * config.num_words}")
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