// OpenRAM SRAM Multi-Bank Top Module (HORIZONTAL BANKING)
// Word width is divided across banks (bit-slicing)
// Each bank stores a portion of bits for ALL words
// All banks accessed simultaneously - no bank mux latency

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
{% if num_wmask > 1 %}
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
{% if num_wmask > 1 %}
    wmask{{ port }},
{% endif %}
    web{{ port }},
{% endfor %}
  );

  parameter DATA_WIDTH = {{ data_width }};
  parameter ADDR_WIDTH = {{ addr_width }};
  parameter NUM_BANKS = {{ num_banks }};
  parameter BANK_DATA_WIDTH = DATA_WIDTH / NUM_BANKS;
  parameter NUM_WMASK = {{ num_wmask }};

`ifdef USE_POWER_PINS
  inout {{ vdd }};
  inout {{ gnd }};
`endif
{% for port in rw_ports %}
  input clk{{ port }};
  input [ADDR_WIDTH - 1 : 0] addr{{ port }};
  input [DATA_WIDTH - 1: 0] din{{ port }};
  input csb{{ port }};
  input web{{ port }};
{% if num_wmask > 1 %}
  input [NUM_WMASK - 1 : 0] wmask{{ port }};
{% endif %}
  output [DATA_WIDTH - 1 : 0] dout{{ port }};
{% endfor %}
{% for port in r_ports %}
  input clk{{ port }};
  input [ADDR_WIDTH - 1 : 0] addr{{ port }};
  input csb{{ port }};
  output [DATA_WIDTH - 1 : 0] dout{{ port }};
{% endfor %}
{% for port in w_ports %}
  input clk{{ port }};
  input [ADDR_WIDTH - 1 : 0] addr{{ port }};
  input [DATA_WIDTH - 1: 0] din{{ port }};
  input csb{{ port }};
  input web{{ port }};
{% if num_wmask > 1 %}
  input [NUM_WMASK - 1 : 0] wmask{{ port }};
{% endif %}
{% endfor %}

  // Bank outputs (each bank has BANK_DATA_WIDTH bits)
{% for port in ports %}
{% for bank in banks %}
  wire [BANK_DATA_WIDTH - 1 : 0] dout{{ port }}_bank{{ bank }};
{% endfor %}
{% endfor %}

  // Instantiate banks - each handles a horizontal slice of the word
{% for bank in banks %}
  {{ bank_module_name }}_slice bank{{ bank }} (
`ifdef USE_POWER_PINS
    .{{ vdd }}({{ vdd }}),
    .{{ gnd }}({{ gnd }}),
`endif
{% for port in rw_ports %}
    .clk{{ port }}(clk{{ port }}),
    .addr{{ port }}(addr{{ port }}),  // Same address for all banks
    .din{{ port }}(din{{ port }}[{{ bank_data_width * (bank + 1) - 1 }} : {{ bank_data_width * bank }}]),
    .csb{{ port }}(csb{{ port }}),    // Same chip select for all banks
    .web{{ port }}(web{{ port }}),    // Same write enable for all banks
{% if num_wmask > 1 %}
    .wmask{{ port }}(wmask{{ port }}[{{ bank }}]),
{% endif %}
    .dout{{ port }}(dout{{ port }}_bank{{ bank }}),
{% endfor %}
{% for port in r_ports %}
    .clk{{ port }}(clk{{ port }}),
    .addr{{ port }}(addr{{ port }}),
    .csb{{ port }}(csb{{ port }}),
    .dout{{ port }}(dout{{ port }}_bank{{ bank }}),
{% endfor %}
{% for port in w_ports %}
    .clk{{ port }}(clk{{ port }}),
    .addr{{ port }}(addr{{ port }}),
    .din{{ port }}(din{{ port }}[{{ bank_data_width * (bank + 1) - 1 }} : {{ bank_data_width * bank }}]),
    .csb{{ port }}(csb{{ port }}),
    .web{{ port }}(web{{ port }}),
{% if num_wmask > 1 %}
    .wmask{{ port }}(wmask{{ port }}[{{ bank }}]),
{% endif %}
{% endfor %}
  );
{% endfor %}

  // Concatenate bank outputs to form full word (no mux needed!)
{% for port in ports %}
  assign dout{{ port }} = {
{% for bank in banks | reverse %}
    dout{{ port }}_bank{{ bank }}{{ "," if not loop.last else "" }}
{% endfor %}
  };
{% endfor %}

endmodule
