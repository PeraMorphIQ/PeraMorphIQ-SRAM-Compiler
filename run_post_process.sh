#!/bin/bash
# Copyright (c) 2026 PeraMorphIQ
# SPDX-License-Identifier: BSD-3-Clause
#
# This file is part of Pera-OpenRAM.
# Developed by the PeraCom Neuromorphic Research Group.
#
# Author: PeraMorphIQ Team

# =============================================================================
# SRAM Post-Processing Automation Script
# =============================================================================
# Runs all TCL scripts for library compilation and NDM generation
# 
# Usage: ./run_post_process.sh [options]
#   Options:
#     --compile-libs    Only compile .lib to .db
#     --build-ndm       Only build NDM
#     --fix-lef         Only fix LEF layer names
#     --all             Run all steps (default)
#     --help            Show this help
# =============================================================================

set -e  # Exit on error

# =============================================================================
# USER CONFIGURATION - Auto-populated by generate_sram.py
# =============================================================================

# SRAM base name (without corner/voltage suffix)
SRAM_NAME="sram_32b_2048_1rw_freepdk45_sram_32x2048_1v"

# Technology library path (for NDM generation)
TECH_LIB="/tech/45nm/nangate45nm_ndm-main/Nangate.ndm"

# PVT corners to process (space-separated)
# Format: <corner>_<voltage>_<temp>
PVT_CORNERS="TT_1p0V_25C SS_1p0V_25C FF_1p0V_25C TT_1p0V_100C TT_1p0V_0C TT_0p9V_25C TT_1p1V_25C"

# =============================================================================
# DERIVED PATHS - Auto-generated from SRAM_NAME
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

OUTPUT_DIR="outputs"
LIBS_DIR="${OUTPUT_DIR}/libs"
DB_DIR="${OUTPUT_DIR}/db"
DESIGNS_DIR="${OUTPUT_DIR}/designs"
NDM_DIR="${OUTPUT_DIR}/ndm"
LOGS_DIR="${OUTPUT_DIR}/logs"

# File paths derived from SRAM_NAME
SRAM_LEF="${DESIGNS_DIR}/${SRAM_NAME}.lef"
SRAM_GDS="${DESIGNS_DIR}/${SRAM_NAME}.gds"
SRAM_VERILOG="${OUTPUT_DIR}/verilog/${SRAM_NAME}.v"
SRAM_SPICE="${OUTPUT_DIR}/spice/${SRAM_NAME}.sp"

# Generate library file paths for each corner
get_lib_file() {
    local corner="$1"
    echo "${LIBS_DIR}/${SRAM_NAME}_${corner}.lib"
}

get_db_file() {
    local corner="$1"
    echo "${DB_DIR}/${SRAM_NAME}_${corner}.db"
}

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_tool() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 found"
        return 0
    else
        print_warning "$1 not found - skipping related steps"
        return 1
    fi
}

print_config() {
    print_header "Configuration"
    echo ""
    echo "  SRAM Name:    ${SRAM_NAME}"
    echo "  Tech Library: ${TECH_LIB}"
    echo "  PVT Corners:  ${PVT_CORNERS}"
    echo ""
    echo "  File Paths:"
    echo "    LEF:     ${SRAM_LEF}"
    echo "    GDS:     ${SRAM_GDS}"
    echo "    Verilog: ${SRAM_VERILOG}"
    echo "    SPICE:   ${SRAM_SPICE}"
    echo ""
    echo "  Liberty Files:"
    for corner in $PVT_CORNERS; do
        echo "    $(get_lib_file $corner)"
    done
    echo ""
}

# =============================================================================
# Step 1: Fix LEF Layer Names
# =============================================================================

fix_lef_files() {
    print_header "Step 1: Fixing LEF Layer Names"
    
    if [ ! -f "$SRAM_LEF" ]; then
        print_error "LEF file not found: $SRAM_LEF"
        return 1
    fi
    
    backup_file="${SRAM_LEF}.bak"
    
    # Create backup if doesn't exist
    if [ ! -f "$backup_file" ]; then
        cp "$SRAM_LEF" "$backup_file"
        echo "  Backup: $backup_file"
    fi
    
    # Convert layer names: M1->metal1, M2->metal2, etc. (Nangate45 expects 'metal' prefix)
    # Process in reverse order to avoid conflicts (M10 before M1)
    sed -i 's/\bM10\b/metal10/g' "$SRAM_LEF"
    sed -i 's/\bM9\b/metal9/g' "$SRAM_LEF"
    sed -i 's/\bM8\b/metal8/g' "$SRAM_LEF"
    sed -i 's/\bM7\b/metal7/g' "$SRAM_LEF"
    sed -i 's/\bM6\b/metal6/g' "$SRAM_LEF"
    sed -i 's/\bM5\b/metal5/g' "$SRAM_LEF"
    sed -i 's/\bM4\b/metal4/g' "$SRAM_LEF"
    sed -i 's/\bM3\b/metal3/g' "$SRAM_LEF"
    sed -i 's/\bM2\b/metal2/g' "$SRAM_LEF"
    sed -i 's/\bM1\b/metal1/g' "$SRAM_LEF"
    
    # Also handle VIA layers if needed
    sed -i 's/\bVIA1\b/via1/g' "$SRAM_LEF"
    sed -i 's/\bVIA2\b/via2/g' "$SRAM_LEF"
    sed -i 's/\bVIA3\b/via3/g' "$SRAM_LEF"
    sed -i 's/\bVIA4\b/via4/g' "$SRAM_LEF"
    
    # Fix power/ground pin directions: INOUT → INPUT (to match Liberty)
    sed -i '/PIN vdd/,/END vdd/ s/DIRECTION INOUT/DIRECTION INPUT/' "$SRAM_LEF"
    sed -i '/PIN gnd/,/END gnd/ s/DIRECTION INOUT/DIRECTION INPUT/' "$SRAM_LEF"
    
    print_success "Fixed: $(basename $SRAM_LEF) (M# → metal#, power pin directions)"
}

# =============================================================================
# Step 2: Compile Liberty to DB
# =============================================================================

compile_libs() {
    print_header "Step 2: Compiling Liberty Libraries (.lib → .db)"
    
    if [ ! -d "$LIBS_DIR" ]; then
        print_error "Libs directory not found: $LIBS_DIR"
        return 1
    fi
    
    # Check which corners exist
    local found_libs=0
    for corner in $PVT_CORNERS; do
        lib_file=$(get_lib_file $corner)
        if [ -f "$lib_file" ]; then
            echo "  Found: $(basename $lib_file)"
            found_libs=$((found_libs + 1))
        fi
    done
    
    if [ "$found_libs" -eq 0 ]; then
        print_warning "No .lib files found for configured corners"
        return 0
    fi
    
    echo "  Found $found_libs library files for SRAM: $SRAM_NAME"
    
    # Generate TCL script dynamically
    TCL_SCRIPT="${LOGS_DIR}/compile_${SRAM_NAME}.tcl"
    cat > "$TCL_SCRIPT" << EOF
# Auto-generated library compilation script
puts "========== Compiling Libraries for ${SRAM_NAME} =========="

EOF
    
    for corner in $PVT_CORNERS; do
        lib_file=$(get_lib_file $corner)
        db_file=$(get_db_file $corner)
        if [ -f "$lib_file" ]; then
            cat >> "$TCL_SCRIPT" << EOF
# Corner: $corner
if {![file exists "$db_file"]} {
    puts "Processing: $corner"
    if {[catch {read_lib "$lib_file"} error_msg]} {
        puts "ERROR: \$error_msg"
    } else {
        set libs [get_libs *]
        set lib_name [get_object_name [lindex \$libs end]]
        write_lib \$lib_name -format db -output "$db_file"
        remove_lib \$lib_name
        puts "SUCCESS: Created $db_file"
    }
} else {
    puts "SKIPPING: $db_file already exists"
}

EOF
        fi
    done
    
    echo "exit" >> "$TCL_SCRIPT"
    
    # Check for lc_shell
    if check_tool "lc_shell"; then
        echo "  Running: lc_shell -f $TCL_SCRIPT"
        lc_shell -f "$TCL_SCRIPT" 2>&1 | tee "${LOGS_DIR}/compile_libs.log"
        print_success "Library compilation complete"
    else
        print_warning "Skipping library compilation (lc_shell not available)"
        echo "  Generated TCL script: $TCL_SCRIPT"
        echo "  To compile manually, run: lc_shell -f $TCL_SCRIPT"
    fi
}

# =============================================================================
# Step 3: Build NDM
# =============================================================================

build_ndm() {
    print_header "Step 3: Building NDM (New Data Model)"
    
    # Check for required files
    local db_file=$(get_db_file "TT_1p0V_25C")  # Use typical corner
    if [ ! -f "$db_file" ]; then
        print_warning "DB file not found: $db_file - run compile_libs first"
        return 1
    fi
    
    if [ ! -f "$SRAM_LEF" ]; then
        print_warning "LEF file not found: $SRAM_LEF"
        return 1
    fi
    
    # Generate TCL script dynamically
    TCL_SCRIPT="${LOGS_DIR}/build_ndm_${SRAM_NAME}.tcl"
    cat > "$TCL_SCRIPT" << EOF
# Auto-generated NDM build script for ${SRAM_NAME}

# Configuration
set TECH_LIB "${TECH_LIB}"
set SRAM_LEF "${SRAM_LEF}"
set SRAM_DB  "${db_file}"
set NDM_OUT  "${NDM_DIR}/${SRAM_NAME}.ndm"

# Cleanup
file delete -force sram_build_work
file delete -force \$NDM_OUT
foreach old_ndm [glob -nocomplain *_lib.ndm] {
    file delete -force \$old_ndm
}

# Create Workspace
puts "Creating Workspace..."
create_workspace sram_build_work \\
    -flow exploration \\
    -use_technology_lib \$TECH_LIB

# Read Data
puts "Reading Logical Data (.db)..."
read_db \$SRAM_DB

puts "Reading Physical Data (.lef)..."
read_lef \$SRAM_LEF

# Group & Build
puts "Grouping and Committing..."
group_libs
process_workspaces

# Move the NDM to the desired location
set actual_ndm [glob -nocomplain *_lib.ndm]
if {\$actual_ndm != ""} {
    puts "Moving \$actual_ndm to \$NDM_OUT..."
    file rename -force \$actual_ndm \$NDM_OUT
    puts "Successfully moved NDM to \$NDM_OUT"
} else {
    puts "Warning: No *_lib.ndm file found to move"
}

puts "Done. NDM created at: \$NDM_OUT"
exit
EOF
    
    if check_tool "icc2_lm_shell"; then
        echo "  Running: icc2_lm_shell -f $TCL_SCRIPT"
        icc2_lm_shell -f "$TCL_SCRIPT" 2>&1 | tee "${LOGS_DIR}/build_ndm.log"
        print_success "NDM build complete"
    else
        print_warning "Skipping NDM build (icc2_lm_shell not available)"
        echo "  Generated TCL script: $TCL_SCRIPT"
        echo "  To build manually, run: icc2_lm_shell -f $TCL_SCRIPT"
    fi
}

# =============================================================================
# Summary
# =============================================================================

print_summary() {
    print_header "Summary for ${SRAM_NAME}"
    
    echo ""
    echo "Generated files:"
    [ -f "$SRAM_LEF" ] && echo -e "  ${GREEN}✓${NC} LEF: $SRAM_LEF" || echo -e "  ${RED}✗${NC} LEF: $SRAM_LEF"
    [ -f "$SRAM_GDS" ] && echo -e "  ${GREEN}✓${NC} GDS: $SRAM_GDS" || echo -e "  ${RED}✗${NC} GDS: $SRAM_GDS"
    [ -f "$SRAM_VERILOG" ] && echo -e "  ${GREEN}✓${NC} Verilog: $SRAM_VERILOG" || echo -e "  ${YELLOW}?${NC} Verilog: $SRAM_VERILOG"
    [ -f "$SRAM_SPICE" ] && echo -e "  ${GREEN}✓${NC} SPICE: $SRAM_SPICE" || echo -e "  ${YELLOW}?${NC} SPICE: $SRAM_SPICE"
    echo ""
    
    echo "Library files by corner:"
    for corner in $PVT_CORNERS; do
        lib_file=$(get_lib_file $corner)
        db_file=$(get_db_file $corner)
        lib_status="${RED}✗${NC}"
        db_status="${RED}✗${NC}"
        [ -f "$lib_file" ] && lib_status="${GREEN}✓${NC}"
        [ -f "$db_file" ] && db_status="${GREEN}✓${NC}"
        printf "  %-20s LIB: %b  DB: %b\n" "$corner" "$lib_status" "$db_status"
    done
    echo ""
    
    echo "NDM:"
    ndm_file="${NDM_DIR}/${SRAM_NAME}.ndm"
    [ -d "$ndm_file" ] && echo -e "  ${GREEN}✓${NC} $ndm_file" || echo -e "  ${RED}✗${NC} $ndm_file"
    echo ""
}

# =============================================================================
# Usage
# =============================================================================

show_help() {
    echo "SRAM Post-Processing Automation Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --config            Show current configuration"
    echo "  --compile-libs      Only compile .lib to .db (requires lc_shell)"
    echo "  --build-ndm         Only build NDM (requires icc2_lm_shell)"
    echo "  --fix-lef           Only fix LEF layer names"
    echo "  --all               Run all steps (default)"
    echo "  --help              Show this help"
    echo ""
    echo "Current Configuration:"
    echo "  SRAM_NAME:    $SRAM_NAME"
    echo "  PVT_CORNERS:  $PVT_CORNERS"
    echo ""
    echo "Note: This script is auto-updated by generate_sram.py"
    echo ""
    echo "Prerequisites:"
    echo "  - Synopsys Library Compiler (lc_shell) for .lib → .db"
    echo "  - Synopsys ICC2 Library Manager (icc2_lm_shell) for NDM"
}

# =============================================================================
# Main
# =============================================================================

main() {
    # Ensure log directory exists
    mkdir -p "$LOGS_DIR"
    mkdir -p "$DB_DIR"
    mkdir -p "$NDM_DIR"
    
    case "${1:-all}" in
        --help|-h)
            show_help
            ;;
        --config)
            print_config
            print_summary
            ;;
        --compile-libs)
            print_config
            compile_libs
            ;;
        --build-ndm)
            print_config
            build_ndm
            ;;
        --fix-lef)
            print_config
            fix_lef_files
            ;;
        --all|*)
            print_config
            fix_lef_files
            compile_libs
            build_ndm
            print_summary
            ;;
    esac
}

# Run main with all arguments
main "$@"
