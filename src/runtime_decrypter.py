import subprocess
import os
import json
import tempfile
import re
import base64
from typing import Dict, Any, Optional

def _decode_b64_val(val: Any) -> Any:
    if isinstance(val, str) and val.startswith("B64:"):
        b64_data = val[4:]
        try:
            return base64.b64decode(b64_data).decode('utf-8', errors='ignore')
        except Exception:
            return val
    elif isinstance(val, list):
        return [_decode_b64_val(x) for x in val]
    elif isinstance(val, dict):
        return {k: _decode_b64_val(v) for k, v in val.items()}
    return val

def decrypt_sample_runtime(filepath: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return None

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()

    m = re.search(r'local\s+([a-zA-Z0-9_]+)\s*=\s*SynapseXen_[a-zA-Z0-9_]+\s*\(\s*SynapseXen_[a-zA-Z0-9_]+\s*\)', code)
    if not m:
        return None

    proto_var = m.group(1)
    insert_pos = m.end()

    hook_lua = f"""
local function to_json(val)
    local t = type(val)
    if t == "nil" then return "null"
    elseif t == "boolean" or t == "number" then return tostring(val)
    elseif t == "string" then 
        local b64_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        local b = {{}}
        for i = 1, #val, 3 do
            local a1, a2, a3 = val:byte(i, i+2)
            a2 = a2 or 0; a3 = a3 or 0
            local n = a1 * 65536 + a2 * 256 + a3
            local c1 = math.floor(n / 262144) % 64 + 1
            local c2 = math.floor(n / 4096) % 64 + 1
            local c3 = math.floor(n / 64) % 64 + 1
            local c4 = n % 64 + 1
            table.insert(b, b64_chars:sub(c1,c1)..b64_chars:sub(c2,c2)..(#val-i>=1 and b64_chars:sub(c3,c3) or '=')..(#val-i>=2 and b64_chars:sub(c4,c4) or '='))
        end
        return '"B64:' .. table.concat(b) .. '"'
    elseif t == "table" then
        local is_arr = (#val > 0)
        local parts = {{}}
        if is_arr then
            for _, v in ipairs(val) do
                table.insert(parts, to_json(v))
            end
            return "[" .. table.concat(parts, ",") .. "]"
        else
            for k, v in pairs(val) do
                table.insert(parts, string.format("%q:%s", tostring(k), to_json(v)))
            end
            return "{{" .. table.concat(parts, ",") .. "}}"
        end
    end
    return "null"
end

local function dump_table_proto(p)
    if type(p) ~= "table" then return nil end

    local consts = {{}}
    local insts = {{}}
    local children = {{}}
    local num_params = 0
    local upvalues = 0

    for k, v in pairs(p) do
        if type(v) == "number" then
            if k == 553820304 then num_params = v
            elseif k == 2052375458 then upvalues = v end
        elseif type(v) == "table" then
            if #v > 0 then
                local elem = v[1]
                if type(elem) == "string" or type(elem) == "number" or type(elem) == "boolean" then
                    for _, c_val in ipairs(v) do
                        table.insert(consts, c_val)
                    end
                elseif type(elem) == "table" then
                    local first_field = next(elem)
                    if type(first_field) == "number" and elem[first_field] and type(elem[first_field]) == "table" then
                        for _, child_p in ipairs(v) do
                            local cp = dump_table_proto(child_p)
                            if cp then table.insert(children, cp) end
                        end
                    else
                        for _, inst in ipairs(v) do
                            local iobj = {{}}
                            if type(inst) == "table" then
                                for ik, iv in pairs(inst) do
                                    iobj[tostring(ik)] = iv
                                end
                            end
                            table.insert(insts, iobj)
                        end
                    end
                end
            end
        end
    end

    return {{
        consts = consts,
        insts = insts,
        children = children,
        num_params = num_params,
        upvalues = upvalues
    }}
end

local target_proto = {proto_var}
if target_proto then
    local res = dump_table_proto(target_proto)
    print("[XEN_DUMP_START]")
    print(to_json(res))
    print("[XEN_DUMP_END]")
end
os.exit(0)
"""
    hooked_code = code[:insert_pos] + "\n" + hook_lua + "\n" + code[insert_pos:]

    with tempfile.NamedTemporaryFile('w', suffix='.lua', delete=False, encoding='utf-8') as tf:
        tf.write(hooked_code)
        tmp_name = tf.name

    try:
        res = subprocess.run(['lua', tmp_name], capture_output=True, text=True, timeout=10)
        out = res.stdout
        start_tag = "[XEN_DUMP_START]"
        end_tag = "[XEN_DUMP_END]"
        if start_tag in out and end_tag in out:
            json_str = out[out.find(start_tag) + len(start_tag):out.find(end_tag)].strip()
            if json_str:
                raw_json = json.loads(json_str)
                return _decode_b64_val(raw_json)
    except Exception:
        pass
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

    return None
