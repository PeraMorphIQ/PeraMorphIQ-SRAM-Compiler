// OpenRAM SRAM Multi-Bank Top Module (MIXED / 2-D BANKING)
// An array of NUM_V_BANKS vertical groups x NUM_H_BANKS horizontal slices.
// One physical macro is (word_size / NUM_H_BANKS) bits x (num_words / NUM_V_BANKS) words.
//   - the top log2(NUM_V_BANKS) address bits select the vertical group
//   - within the selected group all horizontal slices fire in parallel
//   - non-selected vertical groups have csb deasserted
//   - dout is muxed across vertical groups using the REGISTERED address,
//     giving the same 1-cycle read as the vertical template
//
// NOTE ON POWER: deasserting csb on non-selected groups is correct RTL but buys
// nothing in OpenRAM's Liberty, which has no deselected state -- clk0 bills the
// same internal energy for write, read and deselect alike. A H x V split also
// multiplies the sub-array count from H to H*V, so reported memory power can be
// V times WORSE than a purely horizontal split of the same array.
//
// This file is a template for compiler/modules/template.py, NOT Jinja2.
// Constraints that engine imposes, all load-bearing here:
//   - loop vars must be globally unique (an inner loop reusing an outer name
//     deletes it, and later references then render as literal text)
//   - a for-directive's collection must be a literal dict key, not an expression
//   - a substitution is evaluated with NO builtins: plain + - * ( ) only
//   - the substitution delimiter is a doubled brace, so this file emits no
//     Verilog concatenation braces at all -- horizontal slices assemble via
//     part-select assigns instead
// Note: this comment deliberately spells out no template token verbatim;
// sram_multibank.verilog_write rejects any that survive into the output.

module {{ module_name }}  (
`ifdef USE_POWER_PINS
    {{ vdd }},
    {{ gnd }},
`endif
{% for port in rw_ports %}
    clk{{ port }},
    addr{{ port }},
    din{{ port }},
    csb{{ port }},
{% if top_num_wmask > 1 %}
    wmask{{ port }},
{% endif %}
    web{{ port }},
    dout{{ port }},
{% endfor %}
{% for port in r_ports %}
    clk{{ port }},
    addr{{ port }},
    csb{{ port }},
    dout{{ port }},
{% endfor %}
{% for port in w_ports %}
    clk{{ port }},
    addr{{ port }},
    din{{ port }},
    csb{{ port }},
{% if top_num_wmask > 1 %}
    wmask{{ port }},
{% endif %}
    web{{ port }},
{% endfor %}
  );

  parameter DATA_WIDTH      = {{ data_width }};
  parameter ADDR_WIDTH      = {{ addr_width }};
  parameter BANK_DATA_WIDTH = {{ bank_data_width }};
  parameter BANK_ADDR_WIDTH = {{ bank_addr_width }};
  parameter NUM_H_BANKS     = {{ num_h_banks }};
  parameter NUM_V_BANKS     = {{ num_v_banks }};
  parameter BANK_SEL        = {{ bank_sel }};
  parameter NUM_WMASK       = {{ top_num_wmask }};
  parameter BANK_NUM_WMASK  = {{ bank_num_wmask }};

`ifdef USE_POWER_PINS
  inout {{ vdd }};
  inout {{ gnd }};
`endif
{% for port in rw_ports %}
  input clk{{ port }};
  input [ADDR_WIDTH - 1 : 0] addr{{ port }};
  input [DATA_WIDTH - 1 : 0] din{{ port }};
  input csb{{ port }};
  input web{{ port }};
{% if top_num_wmask > 1 %}
  input [NUM_WMASK - 1 : 0] wmask{{ port }};
{% endif %}
  output reg [DATA_WIDTH - 1 : 0] dout{{ port }};
{% endfor %}
{% for port in r_ports %}
  input clk{{ port }};
  input [ADDR_WIDTH - 1 : 0] addr{{ port }};
  input csb{{ port }};
  output reg [DATA_WIDTH - 1 : 0] dout{{ port }};
{% endfor %}
{% for port in w_ports %}
  input clk{{ port }};
  input [ADDR_WIDTH - 1 : 0] addr{{ port }};
  input [DATA_WIDTH - 1 : 0] din{{ port }};
  input csb{{ port }};
  input web{{ port }};
{% if top_num_wmask > 1 %}
  input [NUM_WMASK - 1 : 0] wmask{{ port }};
{% endif %}
{% endfor %}

  // ---------------------------------------------------------------------------
  // Nets
  // ---------------------------------------------------------------------------
{% for port in ports %}
{% if bank_sel > 0 %}
  reg [BANK_SEL - 1 : 0] addr{{ port }}_reg;
{% endif %}
{% for vb in v_groups %}
  wire [DATA_WIDTH - 1 : 0] dout{{ port }}_group{{ vb }};
  reg csb{{ port }}_v{{ vb }};
  reg web{{ port }}_v{{ vb }};
{% for hb in h_slices %}
  wire [BANK_DATA_WIDTH - 1 : 0] dout{{ port }}_v{{ vb }}_h{{ hb }};
{% endfor %}
{% endfor %}
{% endfor %}

  // ---------------------------------------------------------------------------
  // Macro array: NUM_V_BANKS groups x NUM_H_BANKS slices
  // ---------------------------------------------------------------------------
{% for vb in v_groups %}
{% for hb in h_slices %}
  {{ bank_module_name }} bank_v{{ vb }}_h{{ hb }} (
`ifdef USE_POWER_PINS
    .{{ vdd }}({{ vdd }}),
    .{{ gnd }}({{ gnd }}),
`endif
{% for port in rw_ports %}
    .clk{{ port }}(clk{{ port }}),
    .addr{{ port }}(addr{{ port }}[BANK_ADDR_WIDTH - 1 : 0]),
    .din{{ port }}(din{{ port }}[{{ bank_data_width * (hb + 1) - 1 }} : {{ bank_data_width * hb }}]),
    .csb{{ port }}(csb{{ port }}_v{{ vb }}),
    .web{{ port }}(web{{ port }}_v{{ vb }}),
{% if top_num_wmask > 1 %}
    .wmask{{ port }}(wmask{{ port }}[{{ bank_num_wmask * (hb + 1) - 1 }} : {{ bank_num_wmask * hb }}]),
{% endif %}
    .dout{{ port }}(dout{{ port }}_v{{ vb }}_h{{ hb }}),
{% endfor %}
{% for port in r_ports %}
    .clk{{ port }}(clk{{ port }}),
    .addr{{ port }}(addr{{ port }}[BANK_ADDR_WIDTH - 1 : 0]),
    .csb{{ port }}(csb{{ port }}_v{{ vb }}),
    .dout{{ port }}(dout{{ port }}_v{{ vb }}_h{{ hb }}),
{% endfor %}
{% for port in w_ports %}
    .clk{{ port }}(clk{{ port }}),
    .addr{{ port }}(addr{{ port }}[BANK_ADDR_WIDTH - 1 : 0]),
    .din{{ port }}(din{{ port }}[{{ bank_data_width * (hb + 1) - 1 }} : {{ bank_data_width * hb }}]),
    .csb{{ port }}(csb{{ port }}_v{{ vb }}),
{% if top_num_wmask > 1 %}
    .wmask{{ port }}(wmask{{ port }}[{{ bank_num_wmask * (hb + 1) - 1 }} : {{ bank_num_wmask * hb }}]),
{% endif %}
    .web{{ port }}(web{{ port }}_v{{ vb }}),
{% endfor %}
  );
{% endfor %}
{% endfor %}

  // ---------------------------------------------------------------------------
  // Horizontal assembly: slice hb drives bits [BDW*(hb+1)-1 : BDW*hb]
  // ---------------------------------------------------------------------------
{% for port in ports %}
{% for vb in v_groups %}
{% for hb in h_slices %}
  assign dout{{ port }}_group{{ vb }}[{{ bank_data_width * (hb + 1) - 1 }} : {{ bank_data_width * hb }}] = dout{{ port }}_v{{ vb }}_h{{ hb }};
{% endfor %}
{% endfor %}
{% endfor %}

  // ---------------------------------------------------------------------------
  // Registered vertical-group select.
  // The macro presents data for the address captured at posedge N on posedge
  // N+1, so the mux select must be registered exactly once: unregistered picks
  // the new group's wires while the data is still the old group's, and
  // double-registered makes every read one cycle late.
  // ---------------------------------------------------------------------------
{% if bank_sel > 0 %}
{% for port in ports %}
  always @(posedge clk{{ port }}) begin
    addr{{ port }}_reg <= addr{{ port }}[ADDR_WIDTH - 1 : BANK_ADDR_WIDTH];
  end
{% endfor %}
{% endif %}

  // ---------------------------------------------------------------------------
  // Read data mux across vertical groups
  // ---------------------------------------------------------------------------
{% for port in ports %}
  always @(*) begin
{% if bank_sel > 0 %}
    case (addr{{ port }}_reg)
{% for vb in v_groups %}
      {{ vb }}: dout{{ port }} = dout{{ port }}_group{{ vb }};
{% endfor %}
    endcase
{% endif %}
{% if bank_sel == 0 %}
    dout{{ port }} = dout{{ port }}_group0;
{% endif %}
  end
{% endfor %}

  // ---------------------------------------------------------------------------
  // Chip-select / write-enable decode. Every group defaults to deasserted, so
  // only the addressed group can be written -- this is the write-isolation
  // property between vertical groups.
  // ---------------------------------------------------------------------------
{% for port in rw_ports %}
  always @(*) begin
{% for vb in v_groups %}
    csb{{ port }}_v{{ vb }} = 1'b1;
    web{{ port }}_v{{ vb }} = 1'b1;
{% endfor %}
{% if bank_sel > 0 %}
    case (addr{{ port }}[ADDR_WIDTH - 1 : BANK_ADDR_WIDTH])
{% for vb in v_groups %}
      {{ vb }}: begin
        csb{{ port }}_v{{ vb }} = csb{{ port }};
        web{{ port }}_v{{ vb }} = web{{ port }};
      end
{% endfor %}
    endcase
{% endif %}
{% if bank_sel == 0 %}
    csb{{ port }}_v0 = csb{{ port }};
    web{{ port }}_v0 = web{{ port }};
{% endif %}
  end
{% endfor %}
{% for port in w_ports %}
  always @(*) begin
{% for vb in v_groups %}
    csb{{ port }}_v{{ vb }} = 1'b1;
    web{{ port }}_v{{ vb }} = 1'b1;
{% endfor %}
{% if bank_sel > 0 %}
    case (addr{{ port }}[ADDR_WIDTH - 1 : BANK_ADDR_WIDTH])
{% for vb in v_groups %}
      {{ vb }}: begin
        csb{{ port }}_v{{ vb }} = csb{{ port }};
        web{{ port }}_v{{ vb }} = web{{ port }};
      end
{% endfor %}
    endcase
{% endif %}
{% if bank_sel == 0 %}
    csb{{ port }}_v0 = csb{{ port }};
    web{{ port }}_v0 = web{{ port }};
{% endif %}
  end
{% endfor %}
{% for port in r_ports %}
  always @(*) begin
{% for vb in v_groups %}
    csb{{ port }}_v{{ vb }} = 1'b1;
{% endfor %}
{% if bank_sel > 0 %}
    case (addr{{ port }}[ADDR_WIDTH - 1 : BANK_ADDR_WIDTH])
{% for vb in v_groups %}
      {{ vb }}: csb{{ port }}_v{{ vb }} = csb{{ port }};
{% endfor %}
    endcase
{% endif %}
{% if bank_sel == 0 %}
    csb{{ port }}_v0 = csb{{ port }};
{% endif %}
  end
{% endfor %}
endmodule
