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
# Edit this file, then run: python generate_sram.py
#
# CURRENT TARGET: sky130, 1024b x 2048w as 8 slices of 128b x 2048w.
# See "Ready-made configurations" at the bottom for the 45 nm one.
# ==============================================================================

# ==============================================================================
# SRAM Architecture Parameters
# ==============================================================================

# Word size: bits per word (the FULL array width, before banking divides it)
word_size = 512

# Number of words: depth of the array (the FULL depth, before banking divides it)
# Must be a power of 2.
num_words = 2048

# Number of banks: TOTAL physical macro instances in the array.
# Must be a power of 2 AND equal num_h_banks * num_v_banks.
num_banks = 32

# Banking Mode -- "vertical" | "horizontal" | "mixed"
# -----------------------------------------------------------------------------
# ONE physical macro is generated, of
#     (word_size / num_h_banks) bits  x  (num_words / num_v_banks) words
# and <name>_top.v instantiates num_h_banks * num_v_banks copies of it.
# There is no _top.lef/.lib/.db/.gds -- the wrapper is RTL glue.
#
#   "vertical"   -> (h, v) = (1, num_banks)      address space divided
#   "horizontal" -> (h, v) = (num_banks, 1)      word width divided (bit-slicing)
#   "mixed"      -> (h, v) = (num_h_banks, num_v_banks)   both axes
#
# WHY "mixed" HERE RATHER THAN "horizontal", despite num_v_banks = 1 making them
# geometrically identical: sky130 forces num_r_ports = 1 (see below), and the
# horizontal template's dout concatenation is hardcoded to port 0, so it emits
#     assign dout1 = { dout0_bank7, ... };
# i.e. the second read port silently returns the first port's data. It
# elaborates and simulates; it is just wrong. The mixed template handles every
# port correctly. Use "horizontal" only for genuinely single-port macros.
banking_mode = "mixed"

# Read when banking_mode == "mixed". Both powers of 2; product == num_banks.
#   num_h_banks -> word-width slices    (word_size must divide evenly)
#   num_v_banks -> address-space groups (num_words must divide evenly)
num_h_banks = 8
num_v_banks = 4

# ==============================================================================
# Port Configuration
# ==============================================================================
# sky130 sets array_row_multiple = 2 and array_col_multiple = 2. That constraint
# is enforced ONLY when the total port count is 1, and it requires
#     (num_cols + num_ports + num_spare_cols) % 2 == 0
# which a power-of-2 word size can never satisfy at one port. Adding
# num_spare_cols/num_spare_rows = 1 gets past the check but pushes the row count
# off a power of 2 (64 -> 65), which forces an extra row-address bit and makes
# characterisation index a bitcell that does not exist:
#     KeyError: (127, 125) in orig_bitcell_array.get_cell_name
# It fails AFTER the netlist is written, so it looks like it nearly worked.
#
# With a second port the check is skipped entirely and the geometry stays clean.
# This is almost certainly why sram_1rw1r_32_256_8_sky130 is the only macro in
# the VLSIDA sky130_sram_macros repo with real artifacts -- every plain-1rw
# recipe there has a .log and nothing else.
#
# Cost: an unused read port (clk1/csb1/addr1/dout1) that weight_resolver.v does
# not drive. Tie clk1/csb1/addr1 off and leave dout1 unconnected.
#
# *** freepdk45 has NO such constraint -- use num_r_ports = 0 there. ***
# The second port is not merely wasteful at 45 nm, it can make layout FAIL.
# Every pin is escape-routed to the macro perimeter, and dout1 nearly doubles
# the pin count on a wide macro. Measured on completed 45 nm layouts:
#     128b x  256w, 1rw     269 pins   4.75 um/pin   OK
#      64b x 2048w, 1rw1r   221 pins  10.97 um/pin   OK
#     128b x 1024w, 1rw1r  ~410 pins                 FAILED after 2.8 h in
#                                                    signal_escape_router
# When a pin's escaped wire never reaches the boundary the router used to pass
# None onward and die as "AttributeError: 'NoneType' object has no attribute
# 'layer'"; it now reports the pin and the cause. If you genuinely need dual
# port on a wide macro, set perimeter_pins = False to keep pins internal.
num_rw_ports = 1
num_r_ports = 0
num_w_ports = 0

# Write mask granularity, in bits. Leave unset (== word_size) for no mask.
# The 45 nm macro has NUM_WMASK = 0 and weight_resolver.v drives no mask, so a
# mask is not needed here. Note "horizontal" + a write mask is REFUSED by the
# compiler: that template wires one mask bit to an N-bit macro port. "mixed"
# slices it correctly, so enable it here if you ever want byte writes.
# write_size = 8

# ==============================================================================
# Technology Configuration
# ==============================================================================

# "freepdk45", "sky130", "gf180mcu", "scn4m_subm"
tech_name = "freepdk45"

# sky130 additionally needs, in the environment:
#     export PDK_ROOT=/mnt/hidden_home/e19129/pdk
# populated by, from OpenRAM/:  make sky130-pdk && make sky130-install

# Conda is already installed and active; do NOT let OpenRAM try to install it.
# options.py defaults this to True, and install_conda.sh is tracked mode 644, so
# leaving it unset makes OpenRAM exec a non-executable file and die with
# PermissionError before doing any work.
use_conda = False

# ==============================================================================
# Run Options
# ==============================================================================

# Parallel threads for generation
num_threads = 16

# Skip layout/GDS/LEF. Still produces .sp, .v, _top.v and the .lib corners --
# enough to check geometry and the wrapper. Drop this for the real run.
# netlist_only = True

# Analytical delay models (no SPICE). This DOES work for sky130: only
# regression_model.py reads the absent sim_data/, and the default model is
# "elmore", which does not.
analytical_delay = True

# DRC/LVS needs magic + netgen. Off while iterating.
check_lvsdrc = False

# Parasitic extraction (slow)
use_pex = False

# Characterise only the nominal corner rather than all of
# TT/SS/FF/SF/FS x 3 voltages x 3 temperatures.
nominal_corner_only = False

# ==============================================================================
# Auto-Generated Settings (Do Not Edit)
# ==============================================================================

# SRAM instance name (auto-generated from parameters)
# Suffix: '<N>v' vertical (default), '<N>h' horizontal, '<H>h<V>v' mixed.
# The single-axis forms are unchanged from before mixed banking existed, so
# legacy names such as sram_32x2048_1v and sram_1024x2048_8h are preserved.
# No legacy name contains both 'h' and 'v', so mixed names cannot collide.
# NOTE: this config yields sram_1024x2048_8h1v, NOT the 45 nm flow's
# sram_1024x2048_8h -- different tech, and the array is 8h x 1v via "mixed".
if banking_mode == "mixed":
    _banking_suffix = f"{num_h_banks}h{num_v_banks}v"
elif banking_mode == "horizontal":
    _banking_suffix = f"{num_banks}h"
else:
    _banking_suffix = f"{num_banks}v"
sram_name = f"sram_{word_size}x{num_words}_{_banking_suffix}"

# Output directory for generated files
output_path = "./outputs"

# ==============================================================================
# Ready-made configurations
# ==============================================================================
#
# --- The shipped 45 nm macro (what the PrimePower flow uses today) ---
# word_size = 1024;  num_words = 2048;  num_banks = 8
# banking_mode = "horizontal"
# tech_name = "freepdk45"
# num_rw_ports = 1;  num_r_ports = 0;  num_w_ports = 0
# -> sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h, macro 128b x 2048w
#
# --- Mixed 2-D, 45 nm: same 8 macros, split 4 wide x 2 deep ---
# word_size = 1024;  num_words = 2048;  num_banks = 8
# banking_mode = "mixed";  num_h_banks = 4;  num_v_banks = 2
# tech_name = "freepdk45"
# -> eight macros of 256b x 1024w
#    NOTE: reported memory power will NOT improve. OpenRAM's Liberty has no
#    deselected state -- clk0 bills identical energy for write, read, deselect
#    and idle -- so the csb deassertion on non-selected vertical groups buys
#    exactly zero in the report, while the extra per-macro peripheral logic
#    costs ~16-23%. The silicon is better; the number is not.
#
# --- Small sky130 smoke test (minutes, proves the toolchain) ---
# word_size = 32;  num_words = 256;  num_banks = 1
# banking_mode = "vertical";  num_h_banks = 1;  num_v_banks = 1
# tech_name = "sky130";  num_r_ports = 1;  write_size = 8
# netlist_only = True
# -> matches sram_1rw1r_32_256_8_sky130, addr_size 8
