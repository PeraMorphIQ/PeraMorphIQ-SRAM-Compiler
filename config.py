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
word_size = 16

# Number of words: Depth of the SRAM (number of addressable locations)
# Must be a power of 2: 32, 64, 128, 256, 512, 1024, 2048, 4096, etc.
num_words = 32

# Number of banks: Must be a power of 2 (1, 2, 4, 8, etc.)
# More banks = better performance but larger area
num_banks = 1

# Banking Mode
# -----------------------------------------------------------------------------
# "vertical": Address space divided (current default)
#   - Each bank stores different words
#   - Bank selection via address bits
#   - Example 4 banks: Bank0=words 0-511, Bank1=512-1023, etc.
#
# "horizontal": Word width divided (bit-slicing)  
#   - Each bank stores portion of bits for ALL words
#   - All banks accessed simultaneously
#   - Example 1024-bit word, 4 banks: each bank stores 256 bits
#   - NO bank mux latency!
banking_mode = "vertical"  # Options: "vertical", "horizontal"

# Port Configuration
# -----------------------------------------------------------------------------
# OpenRAM supports single-port and dual-port SRAMs (max 2 ports)
# Three types of ports:
#   - RW (Read-Write): Can perform both read and write operations
#   - W (Write-only): Can only write data
#   - R (Read-only): Can only read data
#
# Common configurations:
#   Single-port:  num_rw_ports=1, num_r_ports=0, num_w_ports=0
#   Dual-port:    num_rw_ports=1, num_r_ports=1, num_w_ports=0 (1 RW + 1 R)
#   Dual-port:    num_rw_ports=0, num_r_ports=1, num_w_ports=1 (1 W + 1 R)
#
# Note: Total ports (num_rw_ports + num_r_ports + num_w_ports) must be <= 2
num_rw_ports = 1  # Number of read-write ports (default: 1 for single-port)
num_r_ports = 0   # Number of read-only ports (default: 0)
num_w_ports = 0   # Number of write-only ports (default: 0)

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
# Suffix: 'v' for vertical (default), 'h' for horizontal
_banking_suffix = "h" if banking_mode == "horizontal" else "v"
# Port suffix: e.g., "1rw0r0w" for single-port, "1rw1r0w" for dual-port
_port_suffix = f"{num_rw_ports}rw{num_r_ports}r{num_w_ports}w"
sram_name = f"sram_{_port_suffix}_{word_size}x{num_words}_{num_banks}{_banking_suffix}"

# Output directory for generated files
output_path = "./outputs"
