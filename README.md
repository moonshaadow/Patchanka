# Patchanka

A patchbay for **PipeWire**, based on
[HoustonPatchbay](https://codeberg.org/houston4444/HoustonPatchbay)
by **Houston4444 / Mathieu Picot**.

Patchanka connects to PipeWire natively (via the PipeWire C API
through a small C wrapper and ctypes), and uses HoustonPatchbay
as its graphical patchbay interface.

## Features

- Native PipeWire backend (no JACK dependency)
- Audio, MIDI and Video port support
- Create and remove links between ports
- Hide monitoring ports (automatically created by PipeWire)
- Custom node names via WirePlumber Lua rules
- Automatic reconnection when PipeWire restarts

## Requirements

- Python 3.10 or later
- PipeWire 1.0 or later
- PyQt6
- libpipewire-0.3
- HoustonPatchbay (as a git submodule)

## Installation

Clone the repository with its submodule:

    git clone --recurse-submodules <repository-url>
    cd Patchanka

Build the C wrapper:

    cd native
    make
    cd ..

Build HoustonPatchbay resources:

    cd HoustonPatchbay
    make
    cd ..

## Usage

    python3 run.py

## Acknowledgements

Patchanka uses [HoustonPatchbay](https://codeberg.org/houston4444/HoustonPatchbay),
the graphical patchbay library created by **Houston4444 / Mathieu Picot**.
Many thanks to the author for making it available as a reusable component.

## License

GPL v2 or later. See the LICENSE file for details.
