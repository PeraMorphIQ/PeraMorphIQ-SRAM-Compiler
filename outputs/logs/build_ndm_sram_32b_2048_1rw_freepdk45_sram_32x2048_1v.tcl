# Auto-generated NDM build script for sram_32b_2048_1rw_freepdk45_sram_32x2048_1v

# Configuration
set TECH_LIB "/tech/45nm/nangate45nm_ndm-main/Nangate.ndm"
set SRAM_LEF "outputs/designs/sram_32b_2048_1rw_freepdk45_sram_32x2048_1v.lef"
set SRAM_DB  "outputs/db/sram_32b_2048_1rw_freepdk45_sram_32x2048_1v_TT_1p0V_25C.db"
set NDM_OUT  "outputs/ndm/sram_32b_2048_1rw_freepdk45_sram_32x2048_1v.ndm"

# Cleanup
file delete -force sram_build_work
file delete -force $NDM_OUT
foreach old_ndm [glob -nocomplain *_lib.ndm] {
    file delete -force $old_ndm
}

# Create Workspace
puts "Creating Workspace..."
create_workspace sram_build_work \
    -flow exploration \
    -use_technology_lib $TECH_LIB

# Read Data
puts "Reading Logical Data (.db)..."
read_db $SRAM_DB

puts "Reading Physical Data (.lef)..."
read_lef $SRAM_LEF

# Group & Build
puts "Grouping and Committing..."
group_libs
check_workspace
process_workspaces

# Move the NDM to the desired location
set actual_ndm [glob -nocomplain *_lib.ndm]
if {$actual_ndm != ""} {
    puts "Moving $actual_ndm to $NDM_OUT..."
    file rename -force $actual_ndm $NDM_OUT
    puts "Successfully moved NDM to $NDM_OUT"
} else {
    puts "Warning: No *_lib.ndm file found to move"
}

puts "Done. NDM created at: $NDM_OUT"
exit
