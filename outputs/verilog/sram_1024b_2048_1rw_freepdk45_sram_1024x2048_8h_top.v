// OpenRAM SRAM Multi-Bank Top Module (HORIZONTAL BANKING)
// Word width is divided across banks (bit-slicing)
// Each bank stores a portion of bits for ALL words
// All banks accessed simultaneously - no bank mux latency

module sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h_top  (
`ifdef USE_POWER_PINS
    vdd,
    gnd,
`endif
    clk0,
    addr0,
    din0,
    csb0,
    web0,
    dout0
  );

  parameter DATA_WIDTH = 1024;
  parameter ADDR_WIDTH = 11;
  parameter NUM_BANKS = 8;
  parameter BANK_DATA_WIDTH = DATA_WIDTH / NUM_BANKS;
  parameter NUM_WMASK = 0;

`ifdef USE_POWER_PINS
  inout vdd;
  inout gnd;
`endif
  input clk0;
  input [ADDR_WIDTH - 1 : 0] addr0;
  input [DATA_WIDTH - 1: 0] din0;
  input csb0;
  input web0;
  output [DATA_WIDTH - 1 : 0] dout0;

  // Bank outputs (each bank has BANK_DATA_WIDTH bits)
  wire [BANK_DATA_WIDTH - 1 : 0] dout0_bank0;
  wire [BANK_DATA_WIDTH - 1 : 0] dout0_bank1;
  wire [BANK_DATA_WIDTH - 1 : 0] dout0_bank2;
  wire [BANK_DATA_WIDTH - 1 : 0] dout0_bank3;
  wire [BANK_DATA_WIDTH - 1 : 0] dout0_bank4;
  wire [BANK_DATA_WIDTH - 1 : 0] dout0_bank5;
  wire [BANK_DATA_WIDTH - 1 : 0] dout0_bank6;
  wire [BANK_DATA_WIDTH - 1 : 0] dout0_bank7;

  // Instantiate banks - each handles a horizontal slice of the word
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h bank0 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0),  // Same address for all banks
    .din0(din0[127 : 0]),
    .csb0(csb0),    // Same chip select for all banks
    .web0(web0),    // Same write enable for all banks
    .dout0(dout0_bank0)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h bank1 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0),  // Same address for all banks
    .din0(din0[255 : 128]),
    .csb0(csb0),    // Same chip select for all banks
    .web0(web0),    // Same write enable for all banks
    .dout0(dout0_bank1)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h bank2 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0),  // Same address for all banks
    .din0(din0[383 : 256]),
    .csb0(csb0),    // Same chip select for all banks
    .web0(web0),    // Same write enable for all banks
    .dout0(dout0_bank2)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h bank3 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0),  // Same address for all banks
    .din0(din0[511 : 384]),
    .csb0(csb0),    // Same chip select for all banks
    .web0(web0),    // Same write enable for all banks
    .dout0(dout0_bank3)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h bank4 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0),  // Same address for all banks
    .din0(din0[639 : 512]),
    .csb0(csb0),    // Same chip select for all banks
    .web0(web0),    // Same write enable for all banks
    .dout0(dout0_bank4)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h bank5 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0),  // Same address for all banks
    .din0(din0[767 : 640]),
    .csb0(csb0),    // Same chip select for all banks
    .web0(web0),    // Same write enable for all banks
    .dout0(dout0_bank5)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h bank6 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0),  // Same address for all banks
    .din0(din0[895 : 768]),
    .csb0(csb0),    // Same chip select for all banks
    .web0(web0),    // Same write enable for all banks
    .dout0(dout0_bank6)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8h bank7 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0),  // Same address for all banks
    .din0(din0[1023 : 896]),
    .csb0(csb0),    // Same chip select for all banks
    .web0(web0),    // Same write enable for all banks
    .dout0(dout0_bank7)
  );

  // Concatenate bank outputs to form full word (no mux needed!)
  // Note: banks are concatenated in reverse order (MSB first)
  assign dout0 = { dout0_bank7, dout0_bank6, dout0_bank5, dout0_bank4, dout0_bank3, dout0_bank2, dout0_bank1, dout0_bank0 };

endmodule
