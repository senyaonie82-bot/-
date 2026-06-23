# Wastewater Treatment Plant CAD

This repository contains the CAD drawing scaffold for the wastewater treatment
plant course design.

Current stage: elevation layout drawing framework only. The generated DXF
contains a drawing frame, coordinate axes, title block, notes, and a reserved
legend area; no treatment structures have been drawn yet.

Model-space units are millimetres. The drawing is intended to be plotted at
1:1 on an A1 landscape sheet. Elevation drawing scales are applied by coordinate
conversion: horizontal scale 1:500 and vertical scale 1:50.

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Generate the DXF frame:

```bash
python src/create_blank_dxf.py
```

Generate the PNG preview:

```bash
python src/render_preview.py
```

Generate elevation layout V1:

```bash
python src/draw_elevation_layout_v1.py
```
