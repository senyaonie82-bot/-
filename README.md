# Wastewater Treatment Plant CAD

This repository contains the CAD drawing scaffold for the wastewater treatment
plant course design.

Current stage: elevation layout drawing framework only. The generated DXF
contains a drawing frame, coordinate axes, title block, notes, and an empty
legend area; no treatment structures have been drawn yet.

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
