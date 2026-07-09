# Non-project batch-mode Vivado flow skeleton.
# Run with: vivado -mode batch -source this_file.tcl
#
# Every setting explicit here (no reliance on a GUI-editable .xpr project
# file) so the flow is reproducible in CI and diffable in version control.

set part        "xcvu9p-flga2104-2L-e"      ;# substitute the actual target part
set top         "top_module"
set rtl_dir     "./rtl"
set xdc_dir     "./constraints"
set out_dir     "./build"
set strategy    "Default"                    ;# see strategy-selection-guide.md

file mkdir $out_dir

# --- Elaboration / synthesis -------------------------------------------
read_verilog -sv [glob -nocomplain "${rtl_dir}/*.sv"]
read_verilog        [glob -nocomplain "${rtl_dir}/*.v"]
read_xdc [glob -nocomplain "${xdc_dir}/*.xdc"]

synth_design -top $top -part $part -flatten_hierarchy rebuilt

write_checkpoint -force "${out_dir}/post_synth.dcp"
report_utilization -file "${out_dir}/post_synth_util.rpt"
report_timing_summary -file "${out_dir}/post_synth_timing.rpt"

# --- Implementation ------------------------------------------------------
opt_design
place_design
phys_opt_design                              ;# post-place physical optimization pass
route_design
phys_opt_design -directive AggressiveExplore ;# post-route physical optimization pass, if needed

write_checkpoint -force "${out_dir}/post_route.dcp"
report_timing_summary -file "${out_dir}/post_route_timing.rpt" -report_unconstrained
report_clock_utilization -file "${out_dir}/post_route_clock_util.rpt"
report_utilization -file "${out_dir}/post_route_util.rpt"
report_design_analysis -congestion -file "${out_dir}/congestion.rpt"

# --- Sign-off gate (fail the CI job on negative slack) --------------------
set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]
if {$wns < 0} {
    puts "TIMING FAILED: WNS = $wns"
    exit 1
}

# --- Bitstream (see bitstream-and-bringup for options/debug cores) -------
write_bitstream -force "${out_dir}/${top}.bit"

puts "Build complete: WNS = $wns"
