#!/usr/bin/env python3
"""Place, route and pour tinydie.kicad_pcb.

Run with KiCad's Python:  /usr/bin/python3 hardware/scripts/gen_pcb.py
Needs scripts/netlist.json from gen_sch.py.  Routing uses a small 2-layer
A* grid router (router.py); KiCad DRC is the final judge.
"""
import json
import math
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from router import Router  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.dirname(HERE)
FPDIR = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM

# Board outline
X0, Y0, W, H, RAD = 100.0, 100.0, 45.0, 45.0, 3.0
CX, CY = X0 + W / 2, Y0 + H / 2
PITCH = 12.0

# Net names as KiCad's schematic netlist spells them
NETNAME = {"LED_A": "/LED_A", "LED_B": "/LED_B", "LED_C": "/LED_C",
           "LED_D": "/LED_D", "BTN": "/BTN", "UPDI": "/UPDI"}


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def main():
    netlist = json.load(open(os.path.join(HERE, "netlist.json")))
    board = pcbnew.BOARD()
    nets = {}

    def net(name):
        name = NETNAME.get(name, name)
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    # ---------------------------------------------------- footprints
    fps = {}
    for ref, d in netlist.items():
        lib, name = d["footprint"].split(":")
        fp = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(d["value"])
        if d.get("mpn"):
            f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldOrdinal(), "MPN")
            f.SetText(d["mpn"])
            f.SetVisible(False)
            f.SetLayer(pcbnew.F_Fab)
            fp.Add(f)
        fp.SetPath(pcbnew.KIID_PATH("/" + d["uuid"]))
        fp.SetSheetname("/")
        fp.SetSheetfile("tinydie.kicad_sch")
        board.Add(fp)
        for pad in fp.Pads():
            n = d["pads"].get(pad.GetNumber())
            if n:
                pad.SetNet(net(n))
        fps[ref] = fp

    def place(ref, x, y, rot=0.0, back=False):
        fp = fps[ref]
        fp.SetPosition(V(x, y))
        if back:
            fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)

    def pad_xy(ref, num):
        p = [p for p in fps[ref].Pads() if p.GetNumber() == num][0].GetPosition()
        return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)

    def move_pad_to(ref, num, x, y):
        px, py = pad_xy(ref, num)
        fp = fps[ref]
        pos = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(pos.x + MM(x - px), pos.y + MM(y - py)))

    pips = {"D1": (-1, -1), "D2": (1, -1), "D3": (-1, 0), "D4": (0, 0),
            "D5": (1, 0), "D6": (-1, 1), "D7": (1, 1)}
    for d, (i, j) in pips.items():
        x, y = CX + i * PITCH, CY + j * PITCH
        place(d, x, y, 0)                    # K left, A right
        place("R" + d[1:], x + 4.5, y, 180)  # pad2 faces the LED anode

    place("U1", CX, CY - 5.7, 0)
    place("C1", CX - 4.9, CY - 7.0, 90)

    # CR2032 holder on the back, pins in the free middle-column gaps
    place("BT1", CX, CY, 0, back=True)
    fps["BT1"].SetOrientationDegrees(270)
    move_pad_to("BT1", "1", CX, CY - 11.4)

    place("SW1", 0, 0, 0)
    move_pad_to("SW1", "1", CX - 3.25, CY + 15.3)
    place("J1", 0, 0, 90)
    move_pad_to("J1", "2", CX, Y0 + 4.0)

    for ref in fps:
        print(f"{ref:4s}", " ".join(f"{p.GetNumber()}@({pcbnew.ToMM(p.GetPosition().x):.2f},"
                                    f"{pcbnew.ToMM(p.GetPosition().y):.2f})"
                                    for p in fps[ref].Pads()))

    # ---------------------------------------------------- outline
    def edge_line(a, b):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(*a))
        s.SetEnd(V(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        board.Add(s)

    def edge_arc(start, mid, end):
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(V(*start), V(*mid), V(*end))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        board.Add(s)

    x1, y1 = X0 + W, Y0 + H
    r, k = RAD, RAD * (1 - math.sqrt(0.5))
    edge_line((X0 + r, Y0), (x1 - r, Y0))
    edge_line((x1, Y0 + r), (x1, y1 - r))
    edge_line((x1 - r, y1), (X0 + r, y1))
    edge_line((X0, y1 - r), (X0, Y0 + r))
    edge_arc((x1 - r, Y0), (x1 - k, Y0 + k), (x1, Y0 + r))
    edge_arc((x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1))
    edge_arc((X0 + r, y1), (X0 + k, y1 - k), (X0, y1 - r))
    edge_arc((X0, Y0 + r), (X0 + k, Y0 + k), (X0 + r, Y0))

    # ---------------------------------------------------- routing
    rt = Router(X0, Y0, W, H, grid=0.2, clearance=0.2, edge_clear=0.5)
    for fp in fps.values():
        for p in fp.Pads():
            rt.add_pad(p)

    gnd = net("GND")
    tracks = []  # (layer, (x1,y1), (x2,y2), width, net)
    vias = []    # ((x,y), net)

    def gnd_via(pad_ref, pad_num, dx, dy):
        px, py = pad_xy(pad_ref, pad_num)
        vx, vy = px + dx, py + dy
        tracks.append(("F", (px, py), (vx, vy), 0.4, "GND"))
        vias.append(((vx, vy), "GND"))
        rt.add_track("F", (px, py), (vx, vy), 0.4, "GND")
        rt.add_via((vx, vy), "GND")

    for d in pips:
        gnd_via(d, "1", -1.6, 0)          # LED cathode -> back pour
    gnd_via("U1", "8", 2.0, -1.0)

    # LED anode <-> its resistor: a straight 2 mm hop
    for d in pips:
        r = "R" + d[1:]
        a, b = pad_xy(d, "2"), pad_xy(r, "2")
        n = f"Net-({d}-A)"
        tracks.append(("F", a, b, 0.3, n))
        rt.add_track("F", a, b, 0.3, n)
    gnd_via("C1", "2", -1.6, 0)

    def pads_of(name):
        name = NETNAME.get(name, name)
        return [(ref, p.GetNumber()) for ref, fp in fps.items()
                for p in fp.Pads() if p.GetNetname() == name]

    order = [("+3V0", 0.4), ("LED_D", 0.3), ("LED_C", 0.3), ("LED_A", 0.3),
             ("LED_B", 0.3), ("UPDI", 0.3), ("BTN", 0.3)]
    for name, width in order:
        full = NETNAME.get(name, name)
        pads = [p for fp in fps.values() for p in fp.Pads() if p.GetNetname() == full]
        ok, t, v = rt.route_net(full, pads, width)
        print(f"route {name:6s}: {'ok' if ok else 'FAILED'}  {len(t)} segs {len(v)} vias")
        if not ok:
            sys.exit(1)
        tracks += t
        vias += v

    for layer, a, b, w, n in tracks:
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(V(*a))
        t.SetEnd(V(*b))
        t.SetWidth(MM(w))
        t.SetLayer(pcbnew.F_Cu if layer == "F" else pcbnew.B_Cu)
        t.SetNet(net(n))
        board.Add(t)
    for (x, y), n in vias:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(V(x, y))
        v.SetDrill(MM(0.3))
        v.SetWidth(MM(0.6))
        v.SetNet(net(n))
        board.Add(v)

    # ---------------------------------------------------- GND pours
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetLocalClearance(MM(0.25))
        z.SetMinThickness(MM(0.25))
        z.SetThermalReliefGap(MM(0.3))
        z.SetThermalReliefSpokeWidth(MM(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in [(X0, Y0), (X0 + W, Y0), (X0 + W, Y0 + H), (X0, Y0 + H)]:
            ol.Append(MM(x), MM(y))
        board.Add(z)

    # A few stitching vias tie the two pours together
    for x, y in [(X0 + 4, Y0 + 4), (X0 + W - 4, Y0 + 4), (X0 + 4, Y0 + H - 4),
                 (X0 + W - 4, Y0 + H - 4)]:
        if rt.via_ok((x, y), "GND"):
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(V(x, y))
            v.SetDrill(MM(0.3))
            v.SetWidth(MM(0.6))
            v.SetNet(gnd)
            board.Add(v)

    # ---------------------------------------------------- silkscreen
    def text(s, x, y, layer=pcbnew.F_SilkS, size=1.0, bold=False, rot=0):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s)
        t.SetPosition(V(x, y))
        t.SetLayer(layer)
        t.SetTextSize(V(size, size))
        t.SetTextThickness(MM(size * (0.2 if bold else 0.15)))
        t.SetTextAngleDegrees(rot)
        if layer == pcbnew.B_SilkS:
            t.SetMirrored(True)
        board.Add(t)

    jx = [pad_xy("J1", n)[0] for n in ("1", "2", "3")]
    jy = pad_xy("J1", "1")[1]
    for lbl, x in zip(("U", "V", "G"), jx):
        text(lbl, x, jy + 2.0, size=0.8)
    text("UPDI", jx[0] - 4.2, jy, size=0.8)
    text("TinyDie", X0 + 9.0, Y0 + 3.2, size=1.2, bold=True)
    text("ROLL", CX + 7.6, CY + 17.5, size=0.8)
    text("TinyDie v1.0 · 2026-11", X0 + 3.0, CY, pcbnew.B_SilkS, size=1.0, bold=True, rot=90)
    text("ATtiny412 · CR2032 (+ up)", X0 + W - 3.0, CY, pcbnew.B_SilkS, size=1.0, rot=90)

    # Tidy reference designators: small, out of the way
    for ref, fp in fps.items():
        rt_ = fp.Reference()
        rt_.SetTextSize(V(0.8, 0.8))
        rt_.SetTextThickness(MM(0.12))
        fx, fy = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
        if ref.startswith(("D", "R")):
            rt_.SetPosition(V(fx, fy + 1.6))
            rt_.SetTextAngleDegrees(0)
        elif ref == "U1":
            rt_.SetPosition(V(fx, fy))
        elif ref == "C1":
            rt_.SetPosition(V(fx - 1.7, fy))
            rt_.SetTextAngleDegrees(90)
        elif ref == "SW1":
            rt_.SetVisible(False)
        elif ref == "J1":
            rt_.SetPosition(V(jx[2] + 2.6, jy))
            rt_.SetTextAngleDegrees(0)
        elif ref == "BT1":
            rt_.SetPosition(V(CX, CY - 4))
        fp.Value().SetVisible(False)

    ds = board.GetDesignSettings()
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(MM(0.2))
    nc.SetTrackWidth(MM(0.3))
    nc.SetViaDiameter(MM(0.6))
    nc.SetViaDrill(MM(0.3))

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    out = os.path.join(HW, "tinydie.kicad_pcb")
    board.Save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
