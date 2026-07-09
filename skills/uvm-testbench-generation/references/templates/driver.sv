// Driver skeleton. Timing here must match the interface contract's
// signal table exactly (which edge, valid/ready semantics) - the driver
// is where a misread spec first becomes a wrong stimulus.

class input_driver extends uvm_driver #(input_txn);
  `uvm_component_utils(input_driver)

  virtual dut_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual dut_if)::get(this, "", "vif", vif))
      `uvm_fatal("NOVIF", "virtual interface not set for input_driver")
  endfunction

  task run_phase(uvm_phase phase);
    vif.valid <= 1'b0;
    forever begin
      input_txn tr;
      seq_item_port.get_next_item(tr);

      repeat (tr.idle_cycles_before) @(posedge vif.clk);

      @(posedge vif.clk);
      vif.valid <= 1'b1;
      vif.data  <= tr.data;
      vif.last  <= tr.last;

      // Respect backpressure: hold valid/data stable until ready is seen,
      // per the interface contract's backpressure rule - do not just
      // pulse valid for one cycle regardless of ready.
      do @(posedge vif.clk); while (!vif.ready);

      vif.valid <= 1'b0;
      seq_item_port.item_done();
    end
  endtask
endclass
