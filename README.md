# PeraMorphIQ SRAM Compiler

A streamlined, production-ready OpenRAM-based SRAM compiler with automated output organization and Synopsys tool integration.

**Maintained by:** PeraCom Neuromorphic Research Group  
**Based on:** [OpenRAM](https://github.com/VLSIDA/OpenRAM)  
**License:** BSD-3-Clause

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
  - [Basic Parameters](#basic-parameters)
  - [Banking Modes](#banking-modes)
  - [Advanced Options](#advanced-options)
- [Usage Examples](#usage-examples)
- [Output Structure](#output-structure)
- [Post-Processing](#post-processing)
- [Supported Technologies](#supported-technologies)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)
- [Contact](#contact)

---

## Overview

PeraMorphIQ SRAM Compiler is a production-ready tool for generating custom SRAM macros. It provides a simplified workflow on top of OpenRAM with enhanced stability, automated output organization, and integrated post-processing for industry-standard design flows.

### Key Improvements Over Base OpenRAM

- **Stability Fixes**: Resolved circular imports in `sram_factory` and `globals.py`
- **Modern Compatibility**: Works with NumPy >= 1.20
- **Automated Organization**: Intelligent file management and directory structure
- **Dual Banking Modes**: Support for both vertical and horizontal banking architectures
- **Synopsys Integration**: Built-in scripts for .db and NDM library generation
- **Enhanced Documentation**: Comprehensive guides and examples

---

## Features

- **Simple Configuration**: Single configuration file with clear parameter documentation
- **Organized Outputs**: Automatic directory structure for all generated files (GDS, LEF, Liberty, Verilog, SPICE)
- **Dual Banking Modes**: 
  - Vertical banking (address space division)
  - Horizontal banking (bit-slicing for wide words)
- **Multi-Technology Support**: FreePDK45, Sky130, GF180MCU, and more
- **Complete Output Suite**: Physical design, timing libraries, behavioral models, and documentation
- **Synopsys Tool Integration**: Automated .lib to .db compilation and NDM generation
- **Performance Optimization**: Optional fast-mode generation with analytical models

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- (Optional) Synopsys tools for post-processing:
  - Library Compiler (`lc_shell`)
  - ICC2 Library Manager (`icc2_lm_shell`)

### Setup

```bash
# Clone the repository
git clone https://github.com/YourOrg/PeraMorphIQ-SRAM-Compiler.git
cd PeraMorphIQ-SRAM-Compiler

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r OpenRAM/requirements.txt
```

---

## Quick Start

### 1. Configure Your SRAM

Edit `config.py` with your desired parameters:

```python
# SRAM Architecture Parameters
word_size = 64        # Bit width per word
num_words = 256       # Number of words (must be power of 2)
num_banks = 1         # Number of banks (1, 2, 4, 8, etc.)
banking_mode = "vertical"  # "vertical" or "horizontal"

# Technology Configuration
tech_name = "freepdk45"
```

### 2. Generate SRAM

```bash
python generate_sram.py
```

Generated files will be organized in the `outputs/` directory:
- `outputs/designs/` - GDS and LEF files
- `outputs/libs/` - Liberty timing files
- `outputs/verilog/` - Verilog models
- `outputs/spice/` - SPICE netlists
- `outputs/reports/` - HTML datasheets

### 3. (Optional) Generate Synopsys Libraries

If you have Synopsys tools installed:

```bash
chmod +x run_post_process.sh
./run_post_process.sh --all
```

This generates:
- Compiled .db files in `outputs/db/`
- NDM libraries in `outputs/ndm/`

---

## Configuration

### Basic Parameters

Edit `config.py` to customize your SRAM:

| Parameter | Description | Constraints | Example |
|-----------|-------------|-------------|---------|
| `word_size` | Bits per word (data width) | Power of 2 recommended | 32, 64, 128, 256 |
| `num_words` | SRAM depth | Must be power of 2 | 128, 256, 512, 1024 |
| `num_banks` | Number of banks | Must be power of 2 | 1, 2, 4, 8 |
| `banking_mode` | Banking architecture | "vertical" or "horizontal" | "vertical" |
| `tech_name` | Technology node | See supported list | "freepdk45" |
| `num_threads` | Parallel generation threads | 1-16 | 4 |

### Banking Modes

The compiler supports two banking architectures for multi-bank SRAMs:

#### Vertical Banking (Default)

**Address space is divided across banks**

- Each bank stores different words
- Bank selection via upper address bits
- Only one bank active per access
- Lower power consumption
- Standard SRAM architecture

**Configuration:**
```python
word_size = 128
num_words = 2048
num_banks = 4
banking_mode = "vertical"
```

**Architecture:**
```
Bank 0: Words    0 -  511  [128 bits each]
Bank 1: Words  512 - 1023  [128 bits each]
Bank 2: Words 1024 - 1535  [128 bits each]
Bank 3: Words 1536 - 2047  [128 bits each]
```

**Best For:**
- Standard SRAMs
- Power-sensitive designs
- Word sizes < 512 bits
- Flexible physical placement

#### Horizontal Banking

**Word width is divided across banks (bit-slicing)**

- All banks store all words
- Each bank stores subset of bits
- All banks accessed in parallel
- No bank selection mux latency
- Higher power, better performance

**Configuration:**
```python
word_size = 1024
num_words = 2048
num_banks = 8
banking_mode = "horizontal"
```

**Architecture:**
```
ALL words (0-2047) exist in ALL banks:
Bank 0: bits [  0: 127]  of all words
Bank 1: bits [128: 255]  of all words
Bank 2: bits [256: 383]  of all words
...
Bank 7: bits [896:1023]  of all words
```

**Best For:**
- Very wide words (512-1024+ bits)
- Cache line storage
- Vector processors
- High-performance designs
- Uniform timing requirements

**Performance Comparison:**

| Metric | Vertical | Horizontal |
|--------|----------|------------|
| Bank mux latency | Yes (15-20%) | None |
| Active banks per access | 1 | All |
| Power per access | Lower | Higher |
| Timing uniformity | Moderate | High |
| Physical complexity | Lower | Higher |

### Advanced Options

Add these to `config.py` for optimization:

```python
# Performance optimizations (faster, less accurate)
analytical_delay = True     # Use analytical delay models
use_pex = False            # Disable parasitic extraction
check_lvsdrc = False       # Skip DRC/LVS checks
trim_netlist = True        # Remove unused subcircuits

# Post-processing configuration
tech_lib_path = "/path/to/tech/lib/NangateOpenCellLibrary.ndm"
pvt_corners = "TT_1p0V_25C FF_1p1V_125C SS_0p9V_m40C"
```

---

## Usage Examples

### Small Register File

```python
word_size = 32
num_words = 32
num_banks = 1
tech_name = "freepdk45"
```

### Standard SRAM

```python
word_size = 64
num_words = 256
num_banks = 1
tech_name = "freepdk45"
```

### Multi-Bank SRAM

```python
word_size = 128
num_words = 2048
num_banks = 4
banking_mode = "vertical"
tech_name = "freepdk45"
```

### Wide-Word Cache Memory

```python
word_size = 1024
num_words = 2048
num_banks = 8
banking_mode = "horizontal"  # No bank mux latency
tech_name = "freepdk45"
```

### Neural Network Weight Storage

```python
word_size = 256
num_words = 4096
num_banks = 8
banking_mode = "vertical"
tech_name = "sky130"
```

---

## Output Structure

All generated files are organized in the `outputs/` directory:

```
outputs/
├── designs/        # Physical design files
│   ├── *.gds      # GDSII layout (for fabrication)
│   └── *.lef      # Library Exchange Format (for P&R)
│
├── libs/          # Timing libraries
│   └── *.lib      # Liberty format (multiple PVT corners)
│
├── verilog/       # Behavioral models
│   └── *.v        # Verilog RTL (for simulation)
│
├── spice/         # Circuit netlists
│   ├── *.sp       # SPICE netlist
│   └── *.lvs.sp   # Layout vs. Schematic netlist
│
├── reports/       # Documentation
│   └── *.html     # Interactive datasheet with specifications
│
├── db/            # Synopsys compiled libraries (post-process)
│   └── *.db       # Generated by run_post_process.sh
│
└── ndm/           # ICC2 NDM libraries (post-process)
    └── *.ndm/     # Generated by run_post_process.sh
```

### File Naming Convention

Generated files include a banking mode suffix:

```
Vertical banking:   sram_128x2048_4v.gds
Horizontal banking: sram_1024x2048_8h.gds
```

Where:
- `v` = Vertical banking (address division)
- `h` = Horizontal banking (bit-slicing)

### Integration with Design Tools

**Synthesis (Design Compiler, Genus):**
```tcl
read_lib outputs/libs/sram_64x256_1v_TT_1p0V_25C.lib
# or
read_db outputs/db/sram_64x256_1v_TT_1p0V_25C.db
```

**Place & Route (ICC2, Innovus):**
```tcl
read_lef outputs/designs/sram_64x256_1v.lef
```

**Simulation (ModelSim, VCS):**
```bash
vlog outputs/verilog/sram_64x256_1v.v
```

**Layout Viewing (Klayout):**
```bash
klayout outputs/designs/sram_64x256_1v.gds
```

---

## Post-Processing

The `run_post_process.sh` script automates Synopsys tool workflows.

### Options

```bash
./run_post_process.sh --help          # Show help
./run_post_process.sh --config        # Show current configuration
./run_post_process.sh --compile-libs  # Compile .lib to .db
./run_post_process.sh --build-ndm     # Build NDM libraries
./run_post_process.sh --fix-lef       # Fix LEF layer names
./run_post_process.sh --all           # Run all steps (default)
```

### What It Does

1. **LEF Layer Normalization**: Fixes layer naming for tool compatibility
2. **Liberty Compilation**: Converts `.lib` to `.db` using `lc_shell`
3. **NDM Generation**: Creates ICC2 NDM libraries using `icc2_lm_shell`

### Requirements

- Synopsys Library Compiler (`lc_shell`)
- Synopsys ICC2 Library Manager (`icc2_lm_shell`)

**Note:** Post-processing is optional. Generated `.lib` and `.lef` files work with most EDA tools directly.

---

## Supported Technologies

| Technology | Node | Status | Description |
|------------|------|--------|-------------|
| FreePDK45 | 45nm | Stable | Predictive PDK, widely used for research |
| Sky130 | 130nm | Stable | SkyWater open-source PDK |
| GF180MCU | 180nm | Stable | GlobalFoundries mixed-signal PDK |
| scn4m_subm | 0.5µm | Stable | MOSIS scalable CMOS (4-metal) |
| scn3me_subm | 0.8µm | Stable | MOSIS scalable CMOS (3-metal) |

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'openram'`

**Solution:** Ensure virtual environment is activated and you're in the repo root:
```bash
cd PeraMorphIQ-SRAM-Compiler
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Slow Generation

**Problem:** SRAM generation takes too long

**Solution:** Enable fast mode in `config.py`:
```python
analytical_delay = True
use_pex = False
check_lvsdrc = False
```

### Tool Not Found Errors

**Problem:** `lc_shell: command not found` during post-processing

**Solution:** Post-processing tools are optional. The generated `.lib` files can be used directly. If you need `.db` or NDM, ensure Synopsys tools are in your `PATH`.

### NumPy Compatibility

**Problem:** `AttributeError` related to NumPy arrays

**Solution:** This fork includes NumPy compatibility patches. Ensure you're using the OpenRAM included in this repo, not an external installation.

### Memory Issues

**Problem:** Out of memory during generation

**Solution:** Reduce thread count or use analytical delay mode:
```python
num_threads = 2
analytical_delay = True
```

---

## Technical Details

### Banking Mode Technical Comparison

**Vertical Banking:**
- Address decoding: `[Bank Select | Local Address]`
- Example (11-bit address): `[2-bit bank | 9-bit local]`
- Area: Slightly smaller (less inter-bank routing)
- Power: ~25% less dynamic power

**Horizontal Banking:**
- Address decoding: Same address to all banks
- Output: Concatenated `[Bank7 | Bank6 | ... | Bank0]`
- Area: May be larger (more inter-bank routing)
- Power: Higher (all banks always active)

### Typical File Sizes

For a 64x256 (1 bank) SRAM:

| File Type | Approximate Size |
|-----------|------------------|
| GDS | 1-5 MB |
| LEF | 100-500 KB |
| Liberty (.lib) | 500 KB - 2 MB per corner |
| DB | 200-800 KB per corner |
| Verilog | 10-50 KB |
| SPICE | 500 KB - 5 MB |
| HTML Report | 100-300 KB |
| NDM | 1-3 MB |

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

### Code Style

- Follow existing code structure
- Add comments for complex logic
- Update documentation for new features
- Include examples where applicable

---

## License

This project is licensed under the BSD-3-Clause License. See [LICENSE](LICENSE) for details.

**OpenRAM** is licensed under the BSD-3-Clause License.  
Copyright (c) 2016-2023 Regents of the University of California, Santa Cruz

---

## Acknowledgments

- **OpenRAM Team**: For the excellent open-source SRAM compiler
- **PeraCom Research Group**: For stability patches and workflow enhancements
- **FreePDK Team**: For the open-source 45nm PDK
- **SkyWater & Google**: For the open-source Sky130 PDK
- **GlobalFoundries**: For the GF180MCU PDK

---

## Contact

**PeraCom Neuromorphic Research Group**

- GitHub: [YourGitHubOrg](https://github.com/YourOrg)
- Website: [Your Website](https://yourwebsite.com)
- Issues: [GitHub Issues](https://github.com/YourOrg/PeraMorphIQ-SRAM-Compiler/issues)

---

## References

- [OpenRAM Documentation](https://openram.org/)
- [FreePDK45 Documentation](https://eda.ncsu.edu/freepdk/)
- [SkyWater PDK](https://github.com/google/skywater-pdk)
- [Liberty Format Specification](https://people.eecs.berkeley.edu/~alanmi/publications/other/liberty07_03.pdf)

---

**Copyright (c) 2026 PeraMorphIQ**  
Developed by the PeraCom Neuromorphic Research Group
