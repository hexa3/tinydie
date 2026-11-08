#!/usr/bin/env bash
# Regenerate schematic + PCB, run ERC/DRC, and export fab files.
# Usage: hardware/scripts/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
N="nice -n 19"
quiet() { grep -v 'assert "m_choices' || true; }

python3 scripts/gen_sch.py
$N /usr/bin/python3 scripts/gen_pcb.py 2>&1 | quiet | grep -E 'route|saved'

mkdir -p reports fab/gerbers docs
kicad-cli sch erc --exit-code-violations -o reports/erc.rpt tinydie.kicad_sch 2>&1 | quiet
kicad-cli pcb drc --schematic-parity --severity-all --exit-code-violations \
    -o reports/drc.rpt tinydie.kicad_pcb 2>&1 | quiet

rm -f fab/gerbers/*
kicad-cli pcb export gerbers -o fab/gerbers/ \
    -l F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
    tinydie.kicad_pcb 2>&1 | quiet >/dev/null
kicad-cli pcb export drill -o fab/gerbers/ tinydie.kicad_pcb 2>&1 | quiet >/dev/null
(cd fab && rm -f tinydie-gerbers.zip && zip -qj tinydie-gerbers.zip gerbers/*)
kicad-cli pcb export pos --format csv --units mm --side both \
    -o fab/tinydie-pos.csv tinydie.kicad_pcb 2>&1 | quiet >/dev/null
kicad-cli sch export bom --fields 'Reference,Value,MPN,Footprint,${QUANTITY}' \
    --group-by Value,Footprint --labels 'Refs,Value,MPN,Footprint,Qty' \
    -o fab/tinydie-bom.csv tinydie.kicad_sch 2>&1 | quiet >/dev/null

kicad-cli sch export pdf -o docs/tinydie-schematic.pdf tinydie.kicad_sch 2>&1 | quiet >/dev/null
kicad-cli sch export svg --exclude-drawing-sheet -o docs/ tinydie.kicad_sch 2>&1 | quiet >/dev/null
mv -f docs/tinydie.svg docs/schematic.svg
kicad-cli pcb export svg --mode-single --fit-page-to-board --exclude-drawing-sheet \
    -l F.Cu,F.Silkscreen,F.Mask,Edge.Cuts -o docs/pcb-front.svg tinydie.kicad_pcb 2>&1 | quiet >/dev/null
kicad-cli pcb export svg --mode-single --fit-page-to-board --exclude-drawing-sheet --mirror \
    -l B.Cu,B.Silkscreen,B.Mask,Edge.Cuts -o docs/pcb-back.svg tinydie.kicad_pcb 2>&1 | quiet >/dev/null
for side in top bottom; do
    $N kicad-cli pcb render --side $side --quality basic -w 1200 -h 1200 \
        -o docs/render-$side.png tinydie.kicad_pcb 2>&1 | quiet >/dev/null
done
echo "ERC: $(grep -c '^\[' reports/erc.rpt || true) issues, DRC: $(grep -c '^\[' reports/drc.rpt || true) issues"
ls fab
