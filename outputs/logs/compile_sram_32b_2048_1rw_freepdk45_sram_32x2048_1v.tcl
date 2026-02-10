# Auto-generated library compilation script
puts "========== Compiling Libraries for sram_32b_2048_1rw_freepdk45_sram_32x2048_1v =========="

# Corner: TT_1p0V_25C
if {![file exists "outputs/db/sram_32b_2048_1rw_freepdk45_sram_32x2048_1v_TT_1p0V_25C.db"]} {
    puts "Processing: TT_1p0V_25C"
    if {[catch {read_lib "outputs/libs/sram_32b_2048_1rw_freepdk45_sram_32x2048_1v_TT_1p0V_25C.lib"} error_msg]} {
        puts "ERROR: $error_msg"
    } else {
        set libs [get_libs *]
        set lib_name [get_object_name [lindex $libs end]]
        write_lib $lib_name -format db -output "outputs/db/sram_32b_2048_1rw_freepdk45_sram_32x2048_1v_TT_1p0V_25C.db"
        remove_lib $lib_name
        puts "SUCCESS: Created outputs/db/sram_32b_2048_1rw_freepdk45_sram_32x2048_1v_TT_1p0V_25C.db"
    }
} else {
    puts "SKIPPING: outputs/db/sram_32b_2048_1rw_freepdk45_sram_32x2048_1v_TT_1p0V_25C.db already exists"
}

exit
