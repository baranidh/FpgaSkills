# Multi-seed regression runner template (Vivado xsim-flavored; adapt
# invocation lines for Questa/VCS, the seed-logging discipline is the
# part that matters regardless of simulator).

set num_seeds     50
set test_name     "test_random_traffic"
set log_dir       "./regression_logs"
set fail_count    0

file mkdir $log_dir

for {set i 0} {$i < $num_seeds} {incr i} {
    set seed [expr {int(rand() * 1000000)}]
    set log_file "${log_dir}/${test_name}_seed${seed}.log"

    puts "Running $test_name with seed $seed ..."

    # xsim invocation - substitute vsim/vcs equivalents as needed, keeping
    # the seed value itself passed explicitly and logged, never left
    # implicit (e.g. never rely on a simulator's own unlogged default seed).
    set result [exec xsim work.tb_top -testplusarg "UVM_TESTNAME=$test_name" \
                      -testplusarg "SEED=$seed" \
                      -log $log_file]

    if {[catch {exec grep -q "UVM_ERROR :    0" $log_file}]} {
        puts "FAIL: seed $seed - see $log_file"
        incr fail_count
    }
}

puts "Regression complete: [expr {$num_seeds - $fail_count}]/$num_seeds passed"
if {$fail_count > 0} {
    puts "Failing seeds are reproducible individually: re-run with SEED=<value> from the log filename"
    exit 1
}
exit 0
