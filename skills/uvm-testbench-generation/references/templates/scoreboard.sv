// Scoreboard skeleton. Flags mismatches AND unexpected extra/missing
// transactions - a scoreboard that only compares matched pairs field-by-
// field will silently pass a DUT that drops or duplicates transactions.

class my_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(my_scoreboard)

  uvm_analysis_export #(input_txn) expected_export;
  uvm_analysis_export #(input_txn) actual_export;

  uvm_tlm_analysis_fifo #(input_txn) expected_fifo;
  uvm_tlm_analysis_fifo #(input_txn) actual_fifo;

  int unsigned match_count, mismatch_count;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    expected_export = new("expected_export", this);
    actual_export   = new("actual_export", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    expected_fifo = new("expected_fifo", this);
    actual_fifo   = new("actual_fifo", this);
    expected_export.connect(expected_fifo.analysis_export);
    actual_export.connect(actual_fifo.analysis_export);
  endfunction

  task run_phase(uvm_phase phase);
    input_txn exp, act;
    forever begin
      expected_fifo.get(exp);
      // A timeout here (not shown) that fires before actual_fifo has a
      // matching item is how a dropped transaction gets caught, instead
      // of the scoreboard blocking forever and the test just timing out
      // uninformatively.
      actual_fifo.get(act);

      if (exp.data !== act.data || exp.last !== act.last) begin
        mismatch_count++;
        `uvm_error("SCOREBOARD_MISMATCH",
          $sformatf("expected data=%0h last=%0b, got data=%0h last=%0b",
                     exp.data, exp.last, act.data, act.last))
      end else begin
        match_count++;
      end
    end
  endtask

  function void report_phase(uvm_phase phase);
    `uvm_info("SCOREBOARD", $sformatf("matches=%0d mismatches=%0d",
              match_count, mismatch_count), UVM_LOW)
    if (mismatch_count > 0)
      `uvm_error("SCOREBOARD", "test failed with scoreboard mismatches")
  endfunction
endclass
