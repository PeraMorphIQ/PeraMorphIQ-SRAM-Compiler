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
word_size = 64

# Number of words: Depth of the SRAM (number of addressable locations)
# Must be a power of 2: 32, 64, 128, 256, 512, 1024, 2048, 4096, etc.
num_words = 256

# Number of banks: Must be a power of 2 (1, 2, 4, 8, etc.)
# More banks = better performance but larger area
num_banks = 1

# ==============================================================================
# Technology Configuration
# ==============================================================================

# Process technology node
# Available: "freepdk45", "sky130", "gf180mcu", "scn4m_subm"
tech_name = "freepdk45"

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
# Post-Processing Configuration
# ==============================================================================

# Technology library path for Synopsys tools (NDM generation)
# Update this path to match your technology library location
tech_lib_path = "/path/to/your/tech/lib/NangateOpenCellLibrary.ndm"

# PVT corners to process during post-generation
# Format: <corner>_<voltage>_<temp>
# Example: "TT_1p0V_25C FF_1p1V_125C SS_0p9V_m40C"
pvt_corners = "TT_1p0V_25C"

# ==============================================================================
# Auto-Generated Settings (Do Not Edit)
# ==============================================================================

# SRAM instance name (auto-generated from parameters)
sram_name = f"sram_{word_size}x{num_words}_{num_banks}bank"

# Output directory for generated files
output_path = "./outputs"
