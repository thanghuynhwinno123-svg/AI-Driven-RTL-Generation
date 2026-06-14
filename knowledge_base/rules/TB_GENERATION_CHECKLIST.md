# Testbench Generation Checklist

## Contract and Output

- Create one self-contained SystemVerilog testbench module named `<dut>_tb`.
- The TB module must have no `input`, `output`, or `inout` ports.
- Instantiate the DUT inside the TB, preferably as `u_dut`.
- Declare all DUT inputs as internal `logic` driven only by the TB.
- Declare all DUT outputs as internal observed signals; never drive a DUT output from the TB.
- Output the complete testbench `.sv` file only, with no Markdown fences or prose.

## Black-Box Verification

- Treat the DUT as a black box.
- Build stimulus, expected values, scoreboards, and assertions from the spec, frozen IR, contract summary, and architecture notes.
- Do not copy, mirror, or reimplement internal RTL expressions as the expected-value oracle.
- Do not depend on implementation-only internal signals.
- For every meaningful stimulus, define expected behavior before checking DUT outputs.

## File and Declarations

- Put exactly one `` `timescale 1ns/1ps`` directive at the top of the file.
- Do not emit malformed directives such as `timescale 1ns/1ps` without the backtick.
- Declare every expected value, temporary, loop variable, array, struct, helper, task-local storage, and counter before procedural blocks.
- Do not declare `logic`, `wire`, `reg`, `integer`, `int`, `bit`, arrays, structs, or temporaries inside `always_*`, `initial`, `final`, loops, conditionals, or fork blocks.
- Procedural blocks and tasks must only assign already-declared variables.
- Use valid literal radices only: never write binary literals containing digits other than `0`, `1`, `x`, or `z`.
- For SystemVerilog struct assignment patterns, use `'{field: value}` syntax, never C-style `'{.field = value}`.

## Clock, Reset, and Initialization

- Initialize every DUT input to a known value at time 0.
- Initialize clock before toggling, for example `initial clk = 0; always #5 clk = ~clk;`.
- If reset is active-low (`reset_n`, `rst_n`, or similar), assert `0`, deassert `1`, then wait with `@(posedge reset_n)` or `wait(reset_n == 1'b1)`.
- Never wait for active-low reset deassertion with `@(negedge reset_n)`.
- If reset is active-high, assert `1`, deassert `0`, then wait with `@(negedge reset)` or `wait(reset == 1'b0)`.
- Return inputs to idle values between test cases when the protocol requires it.

## Timing and Protocol

- Check synchronous outputs only after a well-defined clock edge, reset event, or protocol handshake.
- Do not validate synchronous or pipelined DUT outputs using raw `#` delays alone.
- After any `@(posedge clk)` or task that waits for a clock edge, do not immediately read or compare registered DUT outputs in the same simulation time slot.
- Insert a post-edge sampling delay such as `#1;` before checking registered outputs, or use a clocking block with input skew.
- For registered outputs, use the pattern `@(posedge clk); #1; check_output(...);`.
- If the frozen IR says outputs are synchronous or registered, assume checks need post-edge sampling delay unless a clocking block or equivalent skew is used.
- Do not interpret one-cycle shifted actual values, previous-beat data, or reset/default values as RTL bugs until TB sampling timing has been reviewed.
- If the interface has `valid`, `ready`, `done`, or equivalent handshake signals, wait for the correct handshake before comparing data.
- For ready/valid interfaces, a payload is accepted when `valid && ready` are high together; after acceptance, `valid` may deassert in the next observed cycle.
- Do not require `valid` to remain asserted after a handshake has accepted the payload.
- To test hold behavior, drive downstream `ready` low before the DUT produces `valid`, then check that `valid` and payload remain stable while `ready` is low.
- To test immediate acceptance, sample payload on the valid/ready handshake cycle or explicitly document the accepted-cycle timing; do not check one or more cycles later and expect `valid` to still be high.
- If a `valid` mismatch occurs while `ready` was high, review whether the TB observed after legal consumption before classifying the DUT as wrong.
- For fetch/decode style interfaces, distinguish packet metadata from current architectural state: `fetch_pc_o` or similarly named packet PC belongs to the instruction packet, while `pc_o` or current PC/debug outputs may already point to the next fetch address.
- Do not use current PC/debug outputs as the expected packet PC unless the frozen IR explicitly defines them that way.
- Encapsulate repeated bus, memory, serial, or request/response transactions in tasks.
- Serial protocols must be driven bit-by-bit according to the protocol; do not force parallel values onto serial pins.
- For pipelined DUTs, compare each output against the expected stage and latency from the spec/IR.

## Self-Checking and Reporting

- The TB must include real self-checking comparisons; `$display`-only tests are not sufficient.
- Maintain an `integer`/`int` error counter.
- On every functional mismatch, increment the error counter and print one parseable line beginning with `FAIL_FUNC:`.
- Every `FAIL_FUNC:` line must use key-value fields and include: `module=`, `test_id=`, `test_name=`, `feature=`, `phase=`, `signal=`, `expected=`, `actual=`, `time=`, `cycle=`, `spec_rule=`, `inputs=`, `timing_context=`, and `mismatch_type=`.
- Use `mismatch_type=value`, `mismatch_type=timing`, `mismatch_type=missing_valid`, `mismatch_type=unexpected_valid`, `mismatch_type=protocol`, `mismatch_type=reset_state`, `mismatch_type=x_or_z`, or another short diagnostic category.
- Do not print generic messages like `FAIL`, `Mismatch`, or `Wrong result` without the required diagnostic fields.
- For multi-signal checks, print one `FAIL_FUNC:` line per failed signal.
- Include enough stimulus context in `inputs=` for an RTL repair agent to reproduce the case.
- Include latency, applied cycle, checked cycle, and handshake wait details in `timing_context=` when the DUT is synchronous or protocol-based.
- Print `PASS:` only at the final summary when the error counter is zero.
- If the error counter is nonzero at the end, print a final `FAIL:` summary and call `$fatal(1)`.
- Prefer continuing after individual mismatches so one run can report multiple failures; use final `$fatal(1)` for the aggregate failure.
- Use case equality (`===` / `!==`) when comparing values that could contain X/Z.

Required functional failure example:

```text
FAIL_FUNC: module=alu test_id=12 test_name=SLTU_basic feature=ALU phase=check_result signal=result_o expected=0x00000001 actual=0x00000000 time=120 cycle=12 spec_rule="SLTU compares operands as unsigned" inputs="{op=SLTU,a=0xffffffff,b=0x00000001}" timing_context="{applied_cycle=11,checked_cycle=12,latency=1}" mismatch_type=value
```

## Watchdog and Finish

- Every TB must include a watchdog timeout to catch hangs.
- The TB must maintain progress tracking variables: `current_test_id`, `current_test_name`, `current_phase`, `last_completed_test_id`, `waiting_for`, and a cycle counter.
- Update `current_test_id`, `current_test_name`, `current_phase`, and `waiting_for` before each important stimulus, wait, handshake, check, cleanup, and finish step.
- Update `last_completed_test_id` only after a testcase has fully completed all checks.
- The watchdog is a failure path only: it must print one parseable line beginning with `FAIL_WATCHDOG:` and call `$fatal(1)`.
- Every `FAIL_WATCHDOG:` line must use key-value fields and include: `module=`, `current_test_id=`, `current_test_name=`, `current_phase=`, `last_completed_test_id=`, `cycle=`, `waiting_for=`, `timeout_cycles=`, and `status_outputs=`.
- Include important DUT status outputs in `status_outputs=` when the IR exposes them, such as valid, ready, done, busy, state, error, stall, or flush.
- The normal passing path must reach `$finish` before the watchdog.
- Do not let a watchdog be the only way the simulation terminates.

Required watchdog failure example:

```text
FAIL_WATCHDOG: module=alu current_test_id=12 current_test_name=SLTU_basic current_phase=wait_response last_completed_test_id=11 cycle=340 waiting_for=valid_o timeout_cycles=1000 status_outputs="{valid_o=0,ready_o=1,busy_o=1}"
```

## Flow

- VCS runs with `<module>_tb` as the top; do not require a separate `top_<module>.sv` wrapper.
- The compile set may include the DUT RTL and previously passed direct/needed submodule RTL files, but the TB source itself must remain self-contained.
- Passing artifacts are the DUT RTL and `<module>_tb.sv`; do not depend on wrapper artifacts for pass/skip decisions.
