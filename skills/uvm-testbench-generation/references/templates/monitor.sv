// Monitor skeleton. Passive only - never drives vif signals, so this
// class stays reusable when the DUT is instantiated inside a larger
// integration environment where something else drives the interface.

class input_monitor extends uvm_monitor;
  `uvm_component_utils(input_monitor)

  virtual dut_if vif;
  uvm_analysis_port #(input_txn) item_collected_port;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    item_collected_port = new("item_collected_port", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual dut_if)::get(this, "", "vif", vif))
      `uvm_fatal("NOVIF", "virtual interface not set for input_monitor")
  endfunction

  task run_phase(uvm_phase phase);
    forever begin
      input_txn tr;
      @(posedge vif.clk);
      if (vif.valid && vif.ready) begin   // only sample on an actual transfer
        tr = input_txn::type_id::create("tr");
        tr.data = vif.data;
        tr.last = vif.last;
        item_collected_port.write(tr);
      end
    end
  endtask
endclass
