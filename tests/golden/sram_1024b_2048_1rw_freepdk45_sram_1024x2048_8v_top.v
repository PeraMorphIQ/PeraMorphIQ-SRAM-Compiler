
module sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v_top  (
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
  parameter ADDR_WIDTH= 11;

  parameter BANK_SEL = 3;
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
  output reg [DATA_WIDTH - 1 : 0] dout0;

  reg [BANK_SEL - 1 : 0] addr0_reg;

  wire [DATA_WIDTH - 1 : 0] dout0_bank0;

  reg web0_bank0;

  reg csb0_bank0;

  wire [DATA_WIDTH - 1 : 0] dout0_bank1;

  reg web0_bank1;

  reg csb0_bank1;

  wire [DATA_WIDTH - 1 : 0] dout0_bank2;

  reg web0_bank2;

  reg csb0_bank2;

  wire [DATA_WIDTH - 1 : 0] dout0_bank3;

  reg web0_bank3;

  reg csb0_bank3;

  wire [DATA_WIDTH - 1 : 0] dout0_bank4;

  reg web0_bank4;

  reg csb0_bank4;

  wire [DATA_WIDTH - 1 : 0] dout0_bank5;

  reg web0_bank5;

  reg csb0_bank5;

  wire [DATA_WIDTH - 1 : 0] dout0_bank6;

  reg web0_bank6;

  reg csb0_bank6;

  wire [DATA_WIDTH - 1 : 0] dout0_bank7;

  reg web0_bank7;

  reg csb0_bank7;


  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v bank0 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0[ADDR_WIDTH - BANK_SEL - 1 : 0]),
    .din0(din0),
    .csb0(csb0_bank0),
    .web0(web0_bank0),
    .dout0(dout0_bank0)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v bank1 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0[ADDR_WIDTH - BANK_SEL - 1 : 0]),
    .din0(din0),
    .csb0(csb0_bank1),
    .web0(web0_bank1),
    .dout0(dout0_bank1)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v bank2 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0[ADDR_WIDTH - BANK_SEL - 1 : 0]),
    .din0(din0),
    .csb0(csb0_bank2),
    .web0(web0_bank2),
    .dout0(dout0_bank2)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v bank3 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0[ADDR_WIDTH - BANK_SEL - 1 : 0]),
    .din0(din0),
    .csb0(csb0_bank3),
    .web0(web0_bank3),
    .dout0(dout0_bank3)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v bank4 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0[ADDR_WIDTH - BANK_SEL - 1 : 0]),
    .din0(din0),
    .csb0(csb0_bank4),
    .web0(web0_bank4),
    .dout0(dout0_bank4)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v bank5 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0[ADDR_WIDTH - BANK_SEL - 1 : 0]),
    .din0(din0),
    .csb0(csb0_bank5),
    .web0(web0_bank5),
    .dout0(dout0_bank5)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v bank6 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0[ADDR_WIDTH - BANK_SEL - 1 : 0]),
    .din0(din0),
    .csb0(csb0_bank6),
    .web0(web0_bank6),
    .dout0(dout0_bank6)
  );
  sram_1024b_2048_1rw_freepdk45_sram_1024x2048_8v bank7 (
`ifdef USE_POWER_PINS
    .vdd(vdd),
    .gnd(gnd),
`endif
    .clk0(clk0),
    .addr0(addr0[ADDR_WIDTH - BANK_SEL - 1 : 0]),
    .din0(din0),
    .csb0(csb0_bank7),
    .web0(web0_bank7),
    .dout0(dout0_bank7)
  );

  always @(posedge clk0) begin
    addr0_reg <= addr0[ADDR_WIDTH - 1 : ADDR_WIDTH - BANK_SEL];
  end

  always @(*) begin
    case (addr0_reg)
      0: begin
        dout0 = dout0_bank0;
      end
      1: begin
        dout0 = dout0_bank1;
      end
      2: begin
        dout0 = dout0_bank2;
      end
      3: begin
        dout0 = dout0_bank3;
      end
      4: begin
        dout0 = dout0_bank4;
      end
      5: begin
        dout0 = dout0_bank5;
      end
      6: begin
        dout0 = dout0_bank6;
      end
      7: begin
        dout0 = dout0_bank7;
      end
    endcase
  end

  always @(*) begin
    csb0_bank0 = 1'b1;
    web0_bank0 = 1'b1;
    csb0_bank1 = 1'b1;
    web0_bank1 = 1'b1;
    csb0_bank2 = 1'b1;
    web0_bank2 = 1'b1;
    csb0_bank3 = 1'b1;
    web0_bank3 = 1'b1;
    csb0_bank4 = 1'b1;
    web0_bank4 = 1'b1;
    csb0_bank5 = 1'b1;
    web0_bank5 = 1'b1;
    csb0_bank6 = 1'b1;
    web0_bank6 = 1'b1;
    csb0_bank7 = 1'b1;
    web0_bank7 = 1'b1;
    case (addr0[ADDR_WIDTH - 1 : ADDR_WIDTH - BANK_SEL])
      0: begin
        web0_bank0 = web0;
        csb0_bank0 = csb0;
      end
      1: begin
        web0_bank1 = web0;
        csb0_bank1 = csb0;
      end
      2: begin
        web0_bank2 = web0;
        csb0_bank2 = csb0;
      end
      3: begin
        web0_bank3 = web0;
        csb0_bank3 = csb0;
      end
      4: begin
        web0_bank4 = web0;
        csb0_bank4 = csb0;
      end
      5: begin
        web0_bank5 = web0;
        csb0_bank5 = csb0;
      end
      6: begin
        web0_bank6 = web0;
        csb0_bank6 = csb0;
      end
      7: begin
        web0_bank7 = web0;
        csb0_bank7 = csb0;
      end
    endcase
  end


endmodule
