#!/bin/tcsh -f
# =============================================================================
# SRAM Library Compilation Script (Batch Mode)
# =============================================================================
# Usage: lc_shell -f compile_libs.tcl
# =============================================================================

puts "========== Starting Batch Library Compilation =========="

# 1. Path to Liberty library files (organized structure)
set SRAM_LIB_PATH "outputs/libs"
set SRAM_DB_PATH  "outputs/db"

# 2. Find all .lib files in that directory
set lib_files [glob -nocomplain "${SRAM_LIB_PATH}/*.lib"]

if {[llength $lib_files] == 0} {
    puts "ERROR: No .lib files found in $SRAM_LIB_PATH"
    exit 1
}

puts "Found [llength $lib_files] library files to process."

# 3. Loop through each file and compile
foreach lib_file $lib_files {
    
    # Create the output .db filename in the db directory
    set lib_basename [file tail [string range $lib_file 0 end-4]]
    set db_file "${SRAM_DB_PATH}/${lib_basename}.db"
    set short_name [file tail $lib_file]

    puts "\n--------------------------------------------------"
    puts "Processing: $short_name"
    
    # Check if DB already exists to save time (Optional: remove 'if' to force overwrite)
    if {![file exists $db_file]} {
        
        # A. Read the Liberty text file
        if {[catch {read_lib $lib_file} error_msg]} {
            puts "ERROR reading $short_name: $error_msg"
            continue
        }
        
        # B. Get the internal library name
        # (We use 'get_libs' to find the name of what we just read)
        set libs [get_libs *]
        set lib_name [get_object_name [lindex $libs end]]
        
        # C. Write the compiled binary .db file
        puts "  -> Compiling to .db..."
        write_lib $lib_name -format db -output $db_file
        
        # D. Clear memory for the next iteration
        remove_lib $lib_name
        
        puts "SUCCESS: Created $db_file"
        
    } else {
        puts "SKIPPING: .db file already exists."
    }
}

puts "\n========== Compilation Complete =========="
puts "All .db files are located in: $SRAM_LIB_PATH"
exit