#!/usr/bin/env python3
"""Generate tinydie.kicad_sch from the stock KiCad symbol libraries.

Run:  python3 hardware/scripts/gen_sch.py
Writes hardware/tinydie.kicad_sch and hardware/scripts/netlist.json (used by gen_pcb.py).
"""
import copy
import json
import math
import os
import uuid

from sexp import Q, dump, find, find1, parse

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
SYMDIR = "/usr/share/kicad/symbols"
PROJECT = "tinydie"
def _v4(name):
    # stable across rebuilds, but in the random (v4) format KiCad writes
    return str(uuid.UUID(bytes=uuid.uuid5(uuid.NAMESPACE_URL, name).bytes, version=4))


ROOT_UUID = _v4("tinydie-root")


def uid(tag):
    return _v4("tinydie/" + tag)


# ---------------------------------------------------------------- libraries
_libs = {}


def lib_symbol(lib, name):
    """Return a flattened copy of lib:name, renamed to 'lib:name'."""
    if lib not in _libs:
        _libs[lib] = parse(open(f"{SYMDIR}/{lib}.kicad_sym").read())
    syms = {s[1]: s for s in find(_libs[lib], "symbol")}
    sym = copy.deepcopy(syms[name])
    ext = find1(sym, "extends")
    if ext:
        base = copy.deepcopy(syms[ext[1]])
        props = {p[1]: p for p in find(sym, "property")}
        out = [base[0], Q(name)]
        for item in base[2:]:
            if isinstance(item, list) and item[0] == "property" and item[1] in props:
                out.append(props.pop(item[1]))
            elif isinstance(item, list) and item[0] == "symbol":
                item[1] = Q(item[1].replace(ext[1], name))
                out.append(item)
            else:
                out.append(item)
        sym = out
    pins = {}
    for sub in find(sym, "symbol"):
        for p in find(sub, "pin"):
            at = find1(p, "at")
            pins[find1(p, "number")[1]] = (float(at[1]), float(at[2]), float(at[3]))
    sym[1] = Q(f"{lib}:{name}")
    return sym, pins


# ---------------------------------------------------------------- design
# (ref, lib, symbol, value, footprint, x, y, rot, {pin: net})
FP_R = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
FP_D = "LED_SMD:LED_0805_2012Metric_Pad1.15x1.40mm_HandSolder"
FP_C = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"

parts = [
    ("U1", "MCU_Microchip_ATtiny", "ATtiny412-SS", "ATtiny412-SS",
     "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 99.06, 76.2, 0,
     {"1": "+3V0", "8": "GND", "2": "LED_D", "3": "BTN", "4": "LED_A",
      "5": "LED_B", "6": "UPDI", "7": "LED_C"}),
    ("BT1", "Device", "Battery_Cell", "CR2032",
     "Battery:BatteryHolder_MYOUNG_BS-07-A1BJ001_CR2032", 35.56, 76.2, 0,
     {"1": "+3V0", "2": "GND"}),
    ("C1", "Device", "C", "100nF", FP_C, 55.88, 76.2, 0,
     {"1": "+3V0", "2": "GND"}),
    ("SW1", "Switch", "SW_Push", "ROLL", "Button_Switch_THT:SW_PUSH_6mm",
     71.12, 116.84, 0, {"1": "BTN", "2": "GND"}),
    ("J1", "Connector", "Conn_01x03_Pin", "UPDI",
     "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
     35.56, 116.84, 0, {"1": "UPDI", "2": "+3V0", "3": "GND"}),
]

# Die pips: D1 TL, D2 TR, D3 ML, D4 centre, D5 MR, D6 BL, D7 BR
groups = ["LED_A", "LED_B", "LED_C", "LED_D", "LED_C", "LED_B", "LED_A"]
for i, g in enumerate(groups, 1):
    x = 139.7 + (i - 1) * 12.7
    y = 71.12
    parts.append((f"R{i}", "Device", "R", "330", FP_R, x, y, 0,
                  {"1": g, "2": f"Net-(D{i}-A)"}))
    parts.append((f"D{i}", "Device", "LED", "RED", FP_D, x, y + 7.62, 90,
                  {"2": f"Net-(D{i}-A)", "1": "GND"}))

POWER = {"+3V0", "GND"}

MPN = {
    "U1": "Microchip ATTINY412-SSNR",
    "BT1": "MYOUNG BS-07-A1BJ001",
    "C1": "0805 100nF X7R 16V (generic)",
    "D": "0805 red LED, Vf~2.0V (generic)",
    "R": "0805 330R 1% (generic)",
    "SW1": "6x6mm THT tactile switch, 4-pin (generic)",
    "J1": "1x3 2.54mm pin header (generic)",
}


def mpn_for(ref):
    return MPN.get(ref) or MPN.get(ref.rstrip("0123456789"), "")


def pin_xy(x, y, rot, px, py, *_):
    a = math.radians(rot)
    rx = px * math.cos(a) - py * math.sin(a)
    ry = px * math.sin(a) + py * math.cos(a)
    return round(x + rx, 2), round(y - ry, 2)


def prop(name, value, x, y, hide=False, rot=0):
    p = ["property", Q(name), Q(value), ["at", x, y, rot],
         ["effects", ["font", ["size", 1.27, 1.27]]]]
    if hide:
        p[-1].append(["hide", "yes"])
    return p


def lib_prop(libsym, name, value, x, y, rot, hide=False):
    """Field placed where the library puts it, transformed like the symbol."""
    lp = [p for p in find(libsym, "property") if p[1] == name][0]
    at = find1(lp, "at")
    fx, fy = pin_xy(x, y, rot, float(at[1]), float(at[2]))
    eff = copy.deepcopy(find1(lp, "effects"))
    eff = [e for e in eff if not (isinstance(e, list) and e[0] == "hide")]
    if hide:
        eff.append(["hide", "yes"])
    return ["property", Q(name), Q(value), ["at", fx, fy, float(at[3]) if len(at) > 3 else 0], eff]


def sym_instance(lib_id, ref, value, fp, x, y, rot, pins, tag, in_bom=True, libsym=None,
                 hide_value=False):
    node = ["symbol", ["lib_id", Q(lib_id)], ["at", x, y, rot], ["unit", 1],
            ["exclude_from_sim", "no"], ["in_bom", "yes" if in_bom else "no"],
            ["on_board", "yes" if in_bom else "no"], ["dnp", "no"],
            ["uuid", Q(uid(tag))],
            lib_prop(libsym, "Reference", ref, x, y, rot, hide=not in_bom),
            lib_prop(libsym, "Value", value, x, y, rot, hide=hide_value),
            prop("Footprint", fp, x, y, hide=True),
            prop("Datasheet", "", x, y, hide=True)]
    if in_bom:
        node.append(prop("MPN", mpn_for(ref), x, y, hide=True))
    for n in pins:
        node.append(["pin", Q(n), ["uuid", Q(uid(f"{tag}/pin{n}"))]])
    node.append(["instances", ["project", Q(PROJECT),
                 ["path", Q("/" + ROOT_UUID), ["reference", Q(ref)], ["unit", 1]]]])
    return node


def outward(rot, ang):
    """Unit vector (sheet coords) pointing away from the symbol body at a pin."""
    a = math.radians(ang + 180 + rot)
    return round(math.cos(a)), -round(math.sin(a))


# power symbol rotation so its graphic points along `d` (sheet coords)
GND_ROT = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}
VCC_ROT = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}
LBL = {(1, 0): (0, ["left", "bottom"]), (-1, 0): (180, ["right", "bottom"]),
       (0, -1): (90, ["left", "bottom"]), (0, 1): (270, ["right", "bottom"])}
STUB = 2.54
# J1: pins are 2.54 apart, so walk the +3V0 rail clear of the UPDI label
STUB_OVERRIDE = {("J1", "2"): 12.7}
PWR_DIR = {("J1", "2"): (0, -1), ("J1", "3"): (0, 1)}


def main():
    lib_syms, body = {}, []
    netlist = {}
    n_pwr = [0]

    def need(lib, name):
        key = f"{lib}:{name}"
        if key not in lib_syms:
            lib_syms[key] = lib_symbol(lib, name)
        return lib_syms[key]

    def wire(a, b, tag):
        body.append(["wire", ["pts", ["xy", a[0], a[1]], ["xy", b[0], b[1]]],
                     ["stroke", ["width", 0], ["type", "default"]], ["uuid", Q(uid(tag))]])

    def power_at(net, x, y, d=None):
        n_pwr[0] += 1
        lsym, _ = need("power", net)
        if d is None:
            d = (0, 1) if net == "GND" else (0, -1)
        rot = (GND_ROT if net == "GND" else VCC_ROT)[d]
        body.append(sym_instance(f"power:{net}", f"#PWR0{n_pwr[0]:02d}", net, "",
                                 x, y, rot, ["1"], f"pwr{n_pwr[0]}", in_bom=False, libsym=lsym))

    def flag_at(x, y, rot, i):
        lsym, _ = need("power", "PWR_FLAG")
        body.append(sym_instance("power:PWR_FLAG", f"#FLG0{i}", "PWR_FLAG", "",
                                 x, y, rot, ["1"], f"flag{i}", in_bom=False, libsym=lsym,
                                 hide_value=True))

    for ref, lib, name, value, fp, x, y, rot, nets in parts:
        lsym, pins = need(lib, name)
        body.append(sym_instance(f"{lib}:{name}", ref, value, fp, x, y, rot,
                                 list(pins), ref, libsym=lsym))
        netlist[ref] = {"footprint": fp, "value": value, "uuid": uid(ref), "pads": nets,
                        "mpn": mpn_for(ref)}
        for num, net in nets.items():
            px, py, pang = pins[num]
            ex, ey = pin_xy(x, y, rot, px, py)
            if net.startswith("Net-("):
                continue  # R/LED pins touch directly
            d = outward(rot, pang)
            stub = 0 if (net in POWER and d == ((0, 1) if net == "GND" else (0, -1))) else STUB
            stub = STUB_OVERRIDE.get((ref, num), stub)
            tx, ty = round(ex + d[0] * stub, 2), round(ey + d[1] * stub, 2)
            if stub:
                wire((ex, ey), (tx, ty), f"w/{ref}/{num}")
            if ref == "BT1":
                flag_at(ex, ey, 90, int(num))  # PWR_FLAG right on the battery pins
            if net in POWER:
                power_at(net, tx, ty, PWR_DIR.get((ref, num), d))
            else:
                ang, just = LBL[d]
                body.append(["label", Q(net), ["at", tx, ty, ang],
                             ["effects", ["font", ["size", 1.27, 1.27]], ["justify"] + just],
                             ["uuid", Q(uid(f"lbl/{ref}/{num}"))]])

    texts = [
        ("TinyDie - ATtiny412 electronic die, CR2032 powered", 30.48, 45.72),
        ("Pips: D1 TL  D2 TR  D3 ML  D4 C  D5 MR  D6 BL  D7 BR", 139.7, 99.06),
        ("A=PA1 (2-6)  B=PA2 (4-6)  C=PA3 (6)  D=PA6 (odd)", 139.7, 104.14),
        ("Remove the battery before powering from the UPDI header", 30.48, 132.08),
    ]
    for i, (t, x, y) in enumerate(texts):
        body.append(["text", Q(t), ["exclude_from_sim", "no"], ["at", x, y, 0],
                     ["effects", ["font", ["size", 1.524, 1.524]],
                      ["justify", "left", "bottom"]],
                     ["uuid", Q(uid(f"text{i}"))]])

    sch = ["kicad_sch", ["version", "20250114"], ["generator", Q("eeschema")],
           ["generator_version", Q("10.0")], ["uuid", Q(ROOT_UUID)],
           ["paper", Q("A4")],
           ["title_block", ["title", Q("TinyDie")], ["date", Q("2026-11-06")],
            ["rev", Q("1.0")], ["comment", 1, Q("ATtiny412 electronic die")]],
           ["lib_symbols"] + [s for s, _ in lib_syms.values()]]
    sch += body
    sch += [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]],
            ["embedded_fonts", "no"]]
    with open(os.path.join(HW, f"{PROJECT}.kicad_sch"), "w") as f:
        f.write(dump(sch) + "\n")
    with open(os.path.join(HERE, "netlist.json"), "w") as f:
        json.dump(netlist, f, indent=1)
    print("wrote schematic with", len(parts), "parts")


if __name__ == "__main__":
    main()
