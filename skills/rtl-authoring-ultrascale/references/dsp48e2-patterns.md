# DSP48E2 inference patterns (UltraScale+)

DSP48E2 is the UltraScale+ DSP slice: a 27x18 multiplier feeding a 48-bit ALU, with dedicated A/B/C/D input registers, an M (multiply) pipeline register, a P (output) register, a pre-adder, and dedicated cascade paths (`ACIN`/`ACOUT`, `PCIN`/`PCOUT`, `MULTSIGNIN`/`MULTSIGNOUT`) to its north/south neighbor slice. Every pattern below exists to keep the tool mapping onto those dedicated resources instead of falling back to fabric logic.

## Basic multiply-accumulate (fully pipelined)

```systemverilog
// 3-stage pipeline matching A/B input reg -> M reg -> P reg
logic signed [26:0] a_r;
logic signed [17:0] b_r;
logic signed [47:0] m_r;
logic signed [47:0] p_r;

always_ff @(posedge clk) begin
  a_r <= a_in;
  b_r <= b_in;
  m_r <= a_r * b_r;                 // maps to the M register
  p_r <= accumulate ? p_r + m_r : m_r;  // maps to the P register + ALU
end
```
Keep each register directly between its named stage and the next — no combinational logic in between, or the tool pulls that register out of the DSP slice and back into fabric, costing you both the "free" register and a fabric route.

## Pre-adder pattern (A +/- D before multiply)

```systemverilog
logic signed [26:0] preadd_r;
always_ff @(posedge clk) begin
  preadd_r <= a_in + d_in;   // maps to the dedicated pre-adder, not a separate adder + mult
  m_r      <= preadd_r * b_r;
end
```
Writing `(a_in + d_in) * b_in` as a single combinational expression relies on the synthesis tool recognizing the pre-adder shape; registering the sum explicitly as shown is more reliable across tool versions.

## Cascade chain (wide accumulate / systolic FIR taps)

```systemverilog
// Each tap only connects to its immediate neighbor via P cascade -
// do NOT route PCOUT through any fabric logic between taps.
always_ff @(posedge clk) begin
  p_r[i] <= (i == 0) ? m_r[i] : p_r[i-1] + m_r[i];
end
```
This is the classic systolic FIR/accumulate structure. The moment you insert a mux, a saturate/round step, or any other logic between `p_r[i-1]` and the next stage's adder input, the cascade breaks and each stage becomes an independent fabric-routed adder — a common, silent cause of timing failures that only appears after place & route, not in the synthesis utilization report.

## Frequency budget: 322.265625 vs. 644.53125 MHz

At 322.265625 MHz (period 3.10303 ns, see `../../../references/clock-family-reference.md`), a 3-stage DSP48E2 pipeline (input/M/P registers) comfortably meets timing with margin for reasonable clock uncertainty. At 644.53125 MHz (period 1.55152 ns), the same 3-stage pipeline is often *at* the DSP slice's own internal timing budget — expect to need every dedicated register stage (no skipping the M register "to save a cycle") and to check `report_timing -through` specifically on DSP-to-DSP cascade paths, since cascade routing has its own delay characteristic distinct from general fabric routing.

## How to confirm inference actually happened

Never assume from the RTL shape alone — check `synth_1/*.dcp` reports or the synthesis log for `DSP48E2` cell instantiation counts, and cross-check against expected count (one per pipelined multiply/accumulate structure, or one per cascade tap). `report_utilization -hierarchical` also shows DSP usage per instance, which is the fastest way to spot a tap that silently fell back to fabric logic and LUT-based multipliers.
