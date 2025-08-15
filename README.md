# MacroPad

A customizable macro pad project featuring hardware design files, firmware, and a GUI for configuration.

## Features

- Custom PCB design files for a macro pad
- CircuitPython-based firmware for key handling and display
- Modular codebase for easy extension
- GUI software for configuration (see [Software/GUI](Software/GUI))
- Assembly and fabrication documentation

## Directory Structure

- **Firmware/**: CircuitPython firmware, including main logic (`main.py`), macro handling (`macroPad.py`), display support (`display/display.py`), and KMK keyboard modules.
- **PCB_FIles/**: Hardware design files, including schematic, PCB layout, and fabrication reports.
- **Software/GUI/**: GUI tools for configuring the macro pad.
- **Assembly/**, **Fabrication/**, **Schematic Prints/**: Documentation for building and assembling the macro pad.

## Getting Started

1. **Hardware**: Review PCB and schematic files in [PCB_FIles](PCB_FIles).
2. **Firmware**: Flash CircuitPython and copy files from [Firmware](Firmware) to your device.
3. **Configuration**: Use the GUI in [Software/GUI](Software/GUI) to set up macros.

## Requirements

- CircuitPython-compatible microcontroller
- KMK firmware (included in [Firmware/kmk](Firmware/kmk))
- Python 3.x for GUI tools

## License

This project is for personal and educational use.

---

For more details, see individual folders and documentation.