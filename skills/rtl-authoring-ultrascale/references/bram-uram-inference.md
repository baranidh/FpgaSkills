# BRAM / URAM inference patterns (UltraScale+)

UltraScale+ has two on-chip memory primitives worth distinguishing: **Block RAM (BRAM)**, 36 Kb per tile (splittable to 2x18Kb), and **UltraRAM (URAM)**, 288 Kb per tile, available on UltraScale+ parts that include it. URAM is the better fit for deep buffers (packet buffers, large lookup tables) where BRAM would need many tiles cascaded; BRAM is more flexible in width/depth ratio and is the only option on parts without URAM.

## Canonical simple dual-port template (infers BRAM or URAM depending on size/pragma)

```systemverilog
(* ram_style = "block" *)   // or "ultra" to force URAM; omit to let the tool decide by size
logic [DATA_W-1:0] mem [0:DEPTH-1];

logic [DATA_W-1:0] rd_data_r;

always_ff @(posedge clk) begin
  if (wr_en) mem[wr_addr] <= wr_data;
  rd_data_r <= mem[rd_addr];       // registered read address -> this IS the output register
end

assign rd_data = rd_data_r;
```

The critical detail: `rd_data_r` must be registered **from a read performed with a registered address**, matching the primitive's own read-first/write-first/no-change timing exactly. If your RTL instead has a combinational read (`assign rd_data = mem[rd_addr]`) followed by a register stage added elsewhere, the tool may still infer a BRAM but add an *extra* fabric register for the second stage, silently costing an extra cycle of latency that won't match the latency budget from `../../fpga-functional-spec/references/latency-budget-worksheet.md`.

## Read-before-write vs. write-before-read

State which one the design needs *explicitly* in the interface contract, then match it in code:

```systemverilog
// Write-first (new data forwarded to read output on simultaneous same-address access)
always_ff @(posedge clk) begin
  if (wr_en) begin
    mem[wr_addr] <= wr_data;
    if (wr_addr == rd_addr) rd_data_r <= wr_data;
    else rd_data_r <= mem[rd_addr];
  end else begin
    rd_data_r <= mem[rd_addr];
  end
end
```

Getting this mismatched against what the spec assumes is a common source of "works in simulation with the default memory model, fails on hardware" bugs — the behavior on simultaneous same-address read/write is primitive-specific and must be tested explicitly (see `../../functional-coverage-closure/` for covering this case).

## URAM-specific notes

- URAM is always simple dual-port (one read port, one write port, or true dual-port with restrictions) — don't design assuming BRAM's more flexible port configurations are available if you intend to force `ram_style = "ultra"`.
- URAM has a fixed 4Kb x 72-bit native shape per tile; narrower/wider or shallower/deeper memories still consume whole tiles, so check `report_utilization` for actual tile count rather than assuming your requested depth maps efficiently.
- URAM's output register is not optional in the way BRAM's can feel optional — budget for it in the latency table from the start.

## Confirming inference

Check `report_utilization -hierarchical` for `RAMB36`/`RAMB18` (BRAM) or `URAM288` (URAM) counts per instance immediately after synthesis, not after full implementation — a memory that fell back to distributed RAM (LUT-based) shows up as a large, otherwise-unexplained LUT count increase in that same instance, plus a functional/timing risk since distributed RAM doesn't have the same dedicated timing characteristics.
