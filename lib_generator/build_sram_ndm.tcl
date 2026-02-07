# build_sram_ndm.tcl
# Usage: icc2_lm_shell -f build_sram_ndm.tcl

# 1. Configuration
set TECH_LIB "NangateOpenCellLibrary"

# Updated paths for organized directory structure
set DESIGNS_DIR "outputs/designs"
set LIBS_DIR    "outputs/libs"
set DB_DIR      "outputs/db"
set NDM_DIR     "outputs/ndm"

set SRAM_LEF "${DESIGNS_DIR}/sram_32b_32_1rw_freepdk45_sram_32x32.lef"
set SRAM_LIB "${LIBS_DIR}/sram_32b_32_1rw_freepdk45_sram_32x32_TT_1p0V_25C.lib"
set SRAM_DB  "${DB_DIR}/sram_32b_32_1rw_freepdk45_sram_32x32_TT_1p0V_25C.db"

# 2. Cleanup
file delete -force sram_build_work
file delete -force ${NDM_DIR}/sram_32x32.ndm

# 3. Create Workspace
puts "Creating Workspace..."
create_workspace sram_build_work \
    -flow exploration \
    -use_technology_lib $TECH_LIB

# 4. Read Data
puts "Reading Logical Data (.lib)..."
# CHANGE: Use read_lib
# read_lib $SRAM_LIB
read_db $SRAM_DB

puts "Reading Physical Data (.lef)..."
read_lef $SRAM_LEF

# 5. Group & Build
puts "Grouping and Committing..."
group_libs
check_workspace
process_workspaces

puts "Done."
exit