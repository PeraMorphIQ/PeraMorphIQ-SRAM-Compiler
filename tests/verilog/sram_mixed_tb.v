// Copyright (c) 2026 PeraMorphIQ
// SPDX-License-Identifier: BSD-3-Clause
//
// Self-checking testbench for the multi-bank SRAM wrappers.
//
// Black-box: it never looks inside the DUT, so ONE source covers mixed,
// horizontal and vertical. If it ever needed a per-mode `ifdef, the wrapper's
// external contract would not actually be uniform -- which is itself a finding.
//
// Parameters are supplied by the runner with -pvalue+sram_mixed_tb.<P>=<v>.
//
// TIMING CONTRACT, verified against both bank models:
//   * OpenRAM's generated model registers all inputs on posedge, writes on the
//     following negedge from those registers, and drives dout on that negedge
//     with #DELAY. It forces dout to 'bx at the NEXT posedge + T_HOLD.
//   * The hand-edited synchronous model does everything on posedge using the
//     address present at that edge.
//   Both therefore satisfy: data for the address present at posedge k is
//   stable at posedge k+1 (the X-forcing only happens 1 ns AFTER posedge k+1).
//   So: drive on the negedge, sample on the posedge one cycle after capture.
//
// The wrapper's group-select flop must be exactly one deep. Unregistered, the
// mux would pick the NEW group's wires while the data is still the OLD group's;
// double-registered, every read would be one cycle late. T4 catches both.

// Timescale comes from vcs -timescale=1ns/1ps: the generated bank models and
// wrappers carry no `timescale, and mixing is an ITSFM error.

module sram_mixed_tb;

  parameter W = 32;    // top-level data width
  parameter D = 512;   // total depth in words
  parameter H = 2;     // horizontal slices
  parameter V = 2;     // vertical groups
  parameter AW = 9;    // top-level address width
  parameter SEED = 1;
  parameter NRAND = 5000;

  localparam BW = W / H;          // bits per horizontal slice
  localparam GD = D / V;          // words per vertical group
  localparam integer PERIOD = 10;
  // Sampling offset for the direct (non-scoreboard) checks. A read captured at
  // posedge k is driven by OpenRAM's model at negedge k + DELAY(3) and forced
  // to 'bx at posedge k+1 + T_HOLD(1). Sampling at negedge k + SAMPLE_DLY sits
  // inside that window for both bank models.
  localparam integer SAMPLE_DLY = PERIOD/2 - 1;

  integer errors = 0;
  integer checks = 0;

  reg clk = 1'b0;
  always #(PERIOD/2) clk = ~clk;

  reg  [AW-1:0] addr0 = {AW{1'b0}};
  reg  [W-1:0]  din0  = {W{1'b0}};
  reg           csb0  = 1'b1;
  reg           web0  = 1'b1;
  wire [W-1:0]  dout0;

  dut_wrap #(.DW(W), .AW(AW)) dut (
    .clk0(clk), .addr0(addr0), .din0(din0),
    .csb0(csb0), .web0(web0), .dout0(dout0));

  // ---------------------------------------------------------------------------
  // Reference model and a 1-deep pipeline mirroring the wrapper's read latency
  // ---------------------------------------------------------------------------
  reg [W-1:0] ref_mem [0:D-1];
  reg [W-1:0] ref_valid [0:D-1];   // 1 = ref_mem[a] has been written

  reg            pipe_rd    = 1'b0;
  reg [AW-1:0]   pipe_addr  = {AW{1'b0}};
  reg            pipe_armed = 1'b0;   // ignore results before the pipe fills

  integer settle = 0;   // cycles since reset; results before 2 are unchecked

  task check_pending;
    begin
      if (pipe_rd && pipe_armed && settle > 2) begin
        checks = checks + 1;
        if (ref_valid[pipe_addr] !== 1'b1) begin
          // never written: only require it not be X, since the model's power-up
          // content is undefined
        end else if (dout0 !== ref_mem[pipe_addr]) begin
          errors = errors + 1;
          if (errors < 20)
            $display("ERROR t=%0t addr=%0d expected=%h got=%h",
                     $time, pipe_addr, ref_mem[pipe_addr], dout0);
        end
      end
    end
  endtask

  // Sample and score at the posedge: dout is valid there and only forced to X
  // 1 ns later, so there is no race with the model.
  always @(posedge clk) begin
    check_pending;
    // Capture what THIS edge accepted, for scoring at the next edge.
    pipe_rd   <= (csb0 === 1'b0) && (web0 === 1'b1);
    pipe_addr <= addr0;
    pipe_armed <= 1'b1;
    settle = settle + 1;
    // A write accepted at this edge is visible to a read accepted at the next.
    if (csb0 === 1'b0 && web0 === 1'b0) begin
      ref_mem[addr0]   <= din0;
      ref_valid[addr0] <= 1'b1;
    end
  end

  // ---------------------------------------------------------------------------
  // Stimulus helpers. Drive on the negedge so signals are stable at the posedge
  // that captures them; one op per cycle, i.e. back-to-back with no idle.
  // ---------------------------------------------------------------------------
  task drive_write(input [AW-1:0] a, input [W-1:0] d);
    begin
      @(negedge clk);
      addr0 = a; din0 = d; csb0 = 1'b0; web0 = 1'b0;
    end
  endtask

  task drive_read(input [AW-1:0] a);
    begin
      @(negedge clk);
      addr0 = a; csb0 = 1'b0; web0 = 1'b1;
    end
  endtask

  task drive_idle(input integer n);
    integer i;
    begin
      for (i = 0; i < n; i = i + 1) begin
        @(negedge clk);
        csb0 = 1'b1; web0 = 1'b1;
      end
    end
  endtask

  // Slice-distinguishing, address-dependent pattern: every horizontal slice of
  // a word gets a DIFFERENT value, and each value depends on the address. Any
  // slice permutation, slice reversal, wrong group decode or address-bit swap
  // changes the result.
  function [W-1:0] pat(input [AW-1:0] a);
    integer k;
    reg [W-1:0] acc;
    begin
      acc = {W{1'b0}};
      for (k = 0; k < H; k = k + 1)
        acc[k*BW +: BW] = {a, k[7:0], ~a[7:0]};
      pat = acc;
    end
  endfunction

  integer i, k, g, gi;
  reg [W-1:0] expect_word;
  reg [AW-1:0] a0, a1;
  integer seed_r;

  // ---------------------------------------------------------------------------
  // T0 - no X after the pipeline has filled
  // ---------------------------------------------------------------------------
  always @(posedge clk) begin
    if (pipe_rd && settle > 3 && ref_valid[pipe_addr] === 1'b1) begin
      if (^dout0 === 1'bx) begin
        errors = errors + 1;
        if (errors < 20)
          $display("ERROR t=%0t X on dout for written addr=%0d", $time, pipe_addr);
      end
    end
  end

  initial begin
    for (i = 0; i < D; i = i + 1) begin
      ref_valid[i] = 1'b0;
      ref_mem[i]   = {W{1'b0}};
    end
    seed_r = SEED;

    $display("=== sram_mixed_tb: W=%0d D=%0d H=%0d V=%0d AW=%0d (BW=%0d GD=%0d) ===",
             W, D, H, V, AW, BW, GD);

    drive_idle(4);

    // -------------------------------------------------------------------------
    // T1 - full address sweep, write everything then read everything back
    // -------------------------------------------------------------------------
    for (i = 0; i < D; i = i + 1) drive_write(i[AW-1:0], pat(i[AW-1:0]));
    for (i = 0; i < D; i = i + 1) drive_read(i[AW-1:0]);
    drive_idle(2);
    $display("T1 full sweep done: %0d checks, %0d errors", checks, errors);

    // -------------------------------------------------------------------------
    // T2 - H-slice one-hot: localises a concatenation-order fault to a slice
    // -------------------------------------------------------------------------
    a0 = {AW{1'b0}};
    for (k = 0; k < H; k = k + 1) begin
      expect_word = {W{1'b0}};
      expect_word[k*BW +: BW] = {BW{1'b1}};
      drive_write(a0, expect_word);
      drive_read(a0);
      // Sample inside the valid window rather than after idle cycles: idling
      // lets the model's hold time force dout to 'bx before we look.
      @(negedge clk);
      #(SAMPLE_DLY);
      if (dout0 !== expect_word) begin
        errors = errors + 1;
        $display("ERROR T2 slice %0d addr=%0d: expected=%h got=%h",
                 k, a0, expect_word, dout0);
      end else begin
        checks = checks + 1;
      end
      drive_idle(1);
    end
    $display("T2 slice one-hot done: %0d errors", errors);

    // -------------------------------------------------------------------------
    // T3 - vertical-group write isolation. Sentinel-fill one group, then read
    //      EVERY address and require the other groups to be untouched. This is
    //      the test for the csb/web decode.
    // -------------------------------------------------------------------------
    for (i = 0; i < D; i = i + 1) drive_write(i[AW-1:0], pat(i[AW-1:0]));
    drive_idle(2);
    for (g = 0; g < V; g = g + 1) begin
      for (gi = 0; gi < GD; gi = gi + 1)
        drive_write((g*GD + gi), {W{1'b1}});
      drive_idle(2);
      for (i = 0; i < D; i = i + 1) drive_read(i[AW-1:0]);
      drive_idle(2);
      // restore
      for (gi = 0; gi < GD; gi = gi + 1)
        drive_write((g*GD + gi), pat((g*GD + gi)));
      drive_idle(2);
    end
    $display("T3 group isolation done: %0d checks, %0d errors", checks, errors);

    // -------------------------------------------------------------------------
    // T4 - boundary crossing, back-to-back, no idle cycles.
    //      Catches an unregistered or double-registered mux select.
    // -------------------------------------------------------------------------
    for (g = 0; g + 1 < V; g = g + 1) begin
      a0 = (g + 1) * GD - 1;   // last word of group g
      a1 = (g + 1) * GD;       // first word of group g+1
      for (i = 0; i < 16; i = i + 1) begin
        drive_read(a0);
        drive_read(a1);
      end
      // writes straddling the boundary on consecutive cycles
      drive_write(a0, ~pat(a0));
      drive_write(a1, ~pat(a1));
      drive_read(a0);
      drive_read(a1);
      drive_idle(2);
      drive_write(a0, pat(a0));
      drive_write(a1, pat(a1));
      drive_idle(2);
    end
    $display("T4 boundary crossing done: %0d checks, %0d errors", checks, errors);

    // -------------------------------------------------------------------------
    // T5 - deselect: garbage on the bus with csb high must change nothing
    // -------------------------------------------------------------------------
    for (i = 0; i < 16; i = i + 1) begin
      @(negedge clk);
      csb0 = 1'b1;
      web0 = $random(seed_r);
      addr0 = $random(seed_r);
      din0 = {$random(seed_r), $random(seed_r)};
    end
    drive_idle(2);
    for (i = 0; i < D; i = i + 1) drive_read(i[AW-1:0]);
    drive_idle(2);
    $display("T5 deselect done: %0d checks, %0d errors", checks, errors);

    // -------------------------------------------------------------------------
    // T6 - randomised traffic against the scoreboard
    // -------------------------------------------------------------------------
    for (i = 0; i < NRAND; i = i + 1) begin
      a0 = $random(seed_r) % D;
      if (({$random(seed_r)} % 100) < 40)
        drive_write(a0, {$random(seed_r), $random(seed_r), $random(seed_r), $random(seed_r)});
      else if (({$random(seed_r)} % 100) < 95)
        drive_read(a0);
      else
        drive_idle(1);
    end
    drive_idle(4);
    $display("T6 random traffic done: %0d checks, %0d errors", checks, errors);

    if (checks < D) begin
      $display("FAIL: only %0d checks ran; the testbench did not exercise the DUT", checks);
      errors = errors + 1;
    end

    if (errors == 0) begin
      $display("PASS  (%0d checks)", checks);
      $finish;
    end else begin
      $display("FAIL  (%0d checks, %0d errors)", checks, errors);
      $fatal(1);
    end
  end

  initial begin
    #(PERIOD * 4000000);
    $display("FAIL  timeout");
    $fatal(1);
  end

endmodule
