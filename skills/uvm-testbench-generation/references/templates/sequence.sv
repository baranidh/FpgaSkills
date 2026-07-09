// Sequence item + sequence library skeleton.
// Copy and adapt field names to the interface contract; keep the
// directed/constrained-random split explicit rather than one sequence
// that tries to do both.

class input_txn extends uvm_sequence_item;
  rand bit [DATA_W-1:0] data;
  rand bit              last;
  rand int unsigned     idle_cycles_before;  // models backpressure/gap timing

  constraint c_idle_reasonable { idle_cycles_before inside {[0:8]}; }

  `uvm_object_utils_begin(input_txn)
    `uvm_field_int(data, UVM_ALL_ON)
    `uvm_field_int(last, UVM_ALL_ON)
    `uvm_field_int(idle_cycles_before, UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "input_txn");
    super.new(name);
  endfunction
endclass

// Directed: proves one specific spec'd corner case deterministically.
class seq_back_to_back_zero_idle extends uvm_sequence #(input_txn);
  `uvm_object_utils(seq_back_to_back_zero_idle)
  function new(string name = "seq_back_to_back_zero_idle");
    super.new(name);
  endfunction

  task body();
    repeat (16) begin
      input_txn tr = input_txn::type_id::create("tr");
      start_item(tr);
      tr.idle_cycles_before = 0;   // the specific case being directed
      void'(tr.randomize(data, last));
      finish_item(tr);
    end
  endtask
endclass

// Constrained-random: explores everything not explicitly directed.
class seq_random extends uvm_sequence #(input_txn);
  `uvm_object_utils(seq_random)
  function new(string name = "seq_random");
    super.new(name);
  endfunction

  task body();
    repeat (200) begin
      input_txn tr = input_txn::type_id::create("tr");
      start_item(tr);
      assert(tr.randomize());
      finish_item(tr);
    end
  endtask
endclass
