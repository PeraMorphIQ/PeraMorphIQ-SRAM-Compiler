# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
#
# This file is part of Pera-OpenRAM.
# Developed by the PeraCom Neuromorphic Research Group.
#
# Author: PeraMorphIQ Team

# ==============================================================================
# PeraMorphIQ SRAM Configuration
# ==============================================================================
# Edit this file to customize your SRAM design, then run: python generate_sram.py
# ==============================================================================

# ==============================================================================
# SRAM Architecture Parameters
# ==============================================================================

# Word size: Number of bits per word (data width)
# Common values: 8, 16, 32, 64, 128, 256
word_size = 32

# Number of words: Depth of the SRAM (number of addressable locations)
# Must be a power of 2: 32, 64, 128, 256, 512, 1024, 2048, 4096, etc.
# NOTE: OpenRAM limit is 2048 words per bank - use multiple banks for larger SRAMs
num_words = 2048

# Number of banks: TOTAL number of physical macro instances in the array.
# Must be a power of 2 (1, 2, 4, 8, ...) and must equal num_h_banks * num_v_banks.
# More banks = better performance but larger area
# For 65536 words with 2048 max per bank: need 32 banks minimum
num_banks = 1

# Banking Mode
# -----------------------------------------------------------------------------
# "vertical": Address space divided (default)      -> (h, v) = (1, num_banks)
#   - Each bank stores different words
#   - Bank selection via address bits
#   - Example 4 banks: Bank0=words 0-511, Bank1=512-1023, etc.
#
# "horizontal": Word width divided (bit-slicing)   -> (h, v) = (num_banks, 1)
#   - Each bank stores portion of bits for ALL words
#   - All banks accessed simultaneously
#   - Example 1024-bit word, 4 banks: each bank stores 256 bits
#   - NO bank mux latency!
#
# "mixed": BOTH at once (2-D array)                -> (h, v) = (num_h_banks, num_v_banks)
#   - ONE physical macro of
#         (word_size / num_h_banks) bits  x  (num_words / num_v_banks) words
#     is generated, and <name>_top.v instantiates num_h_banks * num_v_banks copies.
#   - The top log2(num_v_banks) address bits select the vertical group.
#   - All num_h_banks slices of the selected group fire in parallel and their
#     outputs assemble into the full word.
#   - Non-selected vertical groups have csb deasserted.
#   - Example 1024b x 2048w with 4h x 2v: eight 256b x 1024w macros.
banking_mode = "vertical"  # Options: "vertical", "horizontal", "mixed"

# Read ONLY when banking_mode == "mixed". Both must be powers of 2, and their
# product must equal num_banks.
#   num_h_banks -> word-width slices   (word_size must divide evenly)
#   num_v_banks -> address-space groups (num_words must divide evenly)
num_h_banks = 1
num_v_banks = 1

# ==============================================================================
# Technology Configuration
# ==============================================================================

# Process technology node
# Available: "freepdk45", "sky130", "gf180mcu", "scn4m_subm"
tech_name = "freepdk45"

# Use conda for dependency management (set to False to skip conda installation)
use_conda = False

# ==============================================================================
# Advanced Options (Optional)
# ==============================================================================

# Number of parallel threads for generation (default: 4)
num_threads = 4

# Performance optimizations (uncomment to enable)
# analytical_delay = True        # Use fast analytical delay models (no SPICE)
# use_pex = False                # Disable parasitic extraction (faster)
# check_lvsdrc = False           # Skip DRC/LVS checks (faster iteration)
# trim_netlist = True            # Remove unused subcircuits

# ==============================================================================
# Auto-Generated Settings (Do Not Edit)
# ==============================================================================

# SRAM instance name (auto-generated from parameters)
# Suffix: '<N>v' vertical (default), '<N>h' horizontal, '<H>h<V>v' mixed.
# The single-axis forms are unchanged from before mixed banking existed, so
# legacy names such as sram_32x2048_1v and sram_1024x2048_8h are preserved.
# No legacy name contains both 'h' and 'v', so mixed names cannot collide.
if banking_mode == "mixed":
    _banking_suffix = f"{num_h_banks}h{num_v_banks}v"
elif banking_mode == "horizontal":
    _banking_suffix = f"{num_banks}h"
else:
    _banking_suffix = f"{num_banks}v"
sram_name = f"sram_{word_size}x{num_words}_{_banking_suffix}"

# Output directory for generated files
output_path = "./outputs"
