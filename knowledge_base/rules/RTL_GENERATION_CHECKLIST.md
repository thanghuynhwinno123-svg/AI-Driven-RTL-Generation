# RTL Generation Checklist

## Contract and Output

- Implement exactly one SystemVerilog RTL module matching the frozen IR module name.
- Preserve every IR port and parameter: do not add, remove, rename, change direction, or change width.
- Use only direct dependency submodules listed in the DAG; do not instantiate unrelated passed modules.
- Output the complete `.sv` file only, with no Markdown fences or prose.

## File and Style

- Put exactly one `` `timescale 1ns/1ps`` directive at the top of the file.
- Use 4 spaces for indentation and keep lines reasonably short.
- Use `begin`/`end` for all conditional, loop, `case`, and procedural branches.
- Prefer `_i` for inputs, `_o` for outputs, and clear `_reg`, `_next`, `_int` suffixes for internal state.
- Use valid literal radices only: never write binary literals containing digits other than `0`, `1`, `x`, or `z`.

## Declarations

- Declare every signal, temporary, loop variable, array, struct, and helper at module scope before procedural blocks.
- Do not declare `logic`, `wire`, `reg`, `integer`, `int`, `bit`, arrays, structs, or temporaries inside `always_*`, `initial`, `final`, loops, conditionals, or fork blocks.
- Procedural blocks must only assign variables that were already declared.

## Drivers

- Every net, variable, output, and internal signal must have exactly one driver.
- Never assign to an input port.
- Never assign the same variable from two procedural blocks.
- Never drive a signal from both `assign` and `always_*`.
- Never connect two or more module output ports to the same net.
- If several sources can select a value, use separate source nets and one explicit mux/arbiter.
- If an output port is assigned procedurally, do not also drive it with `assign`; if using `assign`, drive it from a dedicated internal signal.
- Avoid self-assign aliases such as `assign signal = signal;`.

## Procedural Semantics

- Use `always_ff` for sequential logic and non-blocking assignments (`<=`) only.
- Use `always_comb` for combinational logic and blocking assignments (`=`) only.
- Do not mix blocking and non-blocking assignments in the same procedural block.
- In `always_comb`, assign safe default values at the start of the block for every driven variable.
- In `always_comb`, do not define a selector or control signal from its own current value.
- Register next-state flow must be explicit: compute `_next` in `always_comb`, then capture `_reg <= _next` in `always_ff`.
- When an output should reflect current-cycle combinational results, derive its next value from the current `_next`/combinational value, not the previous-cycle `_reg`.

## Reset, Clock, and State

- If the IR includes clock/reset, use conservative synchronous behavior unless the IR says otherwise.
- Every register written in `always_ff` must be assigned a deterministic reset value.
- Match reset polarity from the IR or port name (`*_n` and `*n` are active-low unless specified otherwise).
- Do not leave outputs or state registers uninitialized after reset.

## Case, Arithmetic, and Ranges

- Every `case` statement must include a safe `default` branch.
- Case labels must be unique.
- Any `case` branch with multiple statements must use `begin`/`end`.
- Use `unique case` only when all legal encodings are covered or the `default` is safe.
- Never slice outside declared ranges.
- Use concatenation for packing/shifting when it avoids width ambiguity.
- For RV32 multiply high-half operations, widen/cast operands before multiplication to avoid 32-bit truncation.
- Use standard RISC-V machine CSR addresses when implementing CSR decode: `mstatus=12'h300`, `mie=12'h304`, `mtvec=12'h305`, `mepc=12'h341`, `mcause=12'h342`, `mtval=12'h343`, `mip=12'h344`.
