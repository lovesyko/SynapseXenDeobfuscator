# SynapseXen v1.1.2 Deobfuscator

A small deobfuscation tool for Synapse Xen v1.1.2 payloads. It checks whether a Lua file looks like a Synapse Xen script, pulls out the embedded payload, reconstructs the runtime prototype data, and emits something closer to readable Luau source.

This project is mainly for research and reverse-engineering work.

# by @painnet on discord

---

## What it does

- Detects likely Synapse Xen v1.1.2 scripts.
- Extracts the Base64 payload and header metadata.
- Runs a Lua hook to dump the VM prototype data.
- Decodes the bytecode into a simpler intermediate representation.
- Rebuilds decompiled Lua output from the recovered structure.

---

## Requirements

- Python 3.8+
- Lua 5.1

---

## Quick start

From the project root:

```bash
python cli.py path/to/sample.lua -o decompiled.lua
```

Batch process a folder:

```bash
python cli.py path/to/folder --batch -o output_dir
```

Print basic payload metadata:

```bash
python cli.py path/to/sample.lua --inspect
```

---

## CLI options

```bash
python cli.py <input.lua|folder> [options]
```

- `-o, --output`: write output to a file or directory
- `--inspect`: print detection/extraction metadata
- `--decode`: print decoded constants and instruction info
- `--dump-ir`: dump the intermediate representation
- `--dump-cfg`: dump the control-flow graph
- `--batch`: process every `.lua` file in a directory
- `--force`: skip signature checks and continue anyway

---

## Project layout

- `cli.py` – command-line entry point
- `src/detector.py` – signature and detection logic
- `src/extractor.py` – Base64/header extraction
- `src/runtime_decrypter.py` – Lua runtime hook for prototype dumping
- `src/decoder.py` – bytecode decoding
- `src/vm_lifter.py` – VM to IR lifting
- `src/decompiler.py` – decompilation logic
- `src/codegen.py` – Lua source emission

---

## Notes

Educational Purposes only.

The Owner is not responsable of how u use it!