import sys
import os
import argparse
import glob
from typing import List

from src.detector import detect_synapse_xen
from src.extractor import extract_payload
from src.runtime_decrypter import decrypt_sample_runtime
from src.decoder import BytecodeDecoder
from src.vm_lifter import VMLifter
from src.cfg import CFGBuilder
from src.dataflow import DataFlowAnalyzer
from src.decompiler import Decompiler
from src.codegen import CodeGenerator

def deobfuscate_file(input_path: str, options: argparse.Namespace) -> str:
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()

    det = detect_synapse_xen(code)
    if options.inspect:
        print(f"[*] Target: {os.path.basename(input_path)}")
        print(f"    SynapseXen: {det.is_synapse_xen} ({det.version})")
        print(f"    Confidence: {det.confidence:.2f}")

    if not det.is_synapse_xen and not options.force:
        print(f"[!] {input_path} is not a recognized SynapseXen v1.1.2 payload.")
        if not options.batch:
            return ""

    extracted = extract_payload(code)
    if options.inspect and extracted:
        print(f"[*] Payload key: {extracted.key_str}")

    runtime_data = decrypt_sample_runtime(input_path)
    if not runtime_data:
        print(f"[!] Failed to extract prototype payload from {input_path}")
        return ""

    decoder = BytecodeDecoder(runtime_data=runtime_data)
    raw_proto = decoder.decode()
    if options.decode:
        print(f"[*] Constants ({len(raw_proto.constants)}): {raw_proto.constants[:10]}")
        print(f"[*] Instructions ({len(raw_proto.instructions)})")

    lifter = VMLifter(raw_proto)
    ir_module = lifter.lift()

    if ir_module.main_function:
        cfg_builder = CFGBuilder(ir_module.main_function)
        cfg_builder.build_cfg()

    if ir_module.main_function:
        analyzer = DataFlowAnalyzer(ir_module.main_function)
        analyzer.analyze()

    decompiler = Decompiler(ir_module)
    ast_stmts = decompiler.decompile()

    codegen = CodeGenerator()
    return codegen.generate(ast_stmts)

def main():
    parser = argparse.ArgumentParser(description="SynapseXen v1.1.2 Deobfuscator")
    parser.add_argument("input", help="Input script or directory")
    parser.add_argument("-o", "--output", help="Output destination file")
    parser.add_argument("--inspect", action="store_true", help="Print payload metadata")
    parser.add_argument("--decode", action="store_true", help="Dump constants & bytecode")
    parser.add_argument("--dump-ir", action="store_true", help="Dump intermediate representation")
    parser.add_argument("--dump-cfg", action="store_true", help="Dump control flow graph")
    parser.add_argument("--batch", action="store_true", help="Batch process directory")
    parser.add_argument("--force", action="store_true", help="Skip signature verification")

    args = parser.parse_args()

    if os.path.isdir(args.input) or args.batch:
        sample_dir = args.input
        out_dir = args.output or os.path.join(sample_dir, "decompiled")
        os.makedirs(out_dir, exist_ok=True)

        lua_files = glob.glob(os.path.join(sample_dir, "*.lua"))
        print(f"Processing {len(lua_files)} files in {sample_dir}...")

        success = 0
        failed = 0
        for fpath in lua_files:
            fname = os.path.basename(fpath)
            out_path = os.path.join(out_dir, f"{os.path.splitext(fname)[0]}_deobf.lua")
            try:
                res = deobfuscate_file(fpath, args)
                with open(out_path, 'w', encoding='utf-8') as out_f:
                    out_f.write(res)
                success += 1
            except Exception as e:
                print(f"[!] Error on {fname}: {e}")
                failed += 1

        print(f"Done: {success} succeeded, {failed} failed.")
    else:
        result = deobfuscate_file(args.input, args)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"[+] Output written to {args.output}")
        else:
            print(result)

if __name__ == "__main__":
    main()
