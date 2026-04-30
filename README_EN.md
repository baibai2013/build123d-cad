English | [中文](README.md)

<div align="center">

# build123d-cad.skill

> *"Think like a machinist, not a programmer." — Dave Cowden*

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![build123d](https://img.shields.io/badge/build123d-CAD-green)](https://github.com/gumyr/build123d)
[![Nuwa](https://img.shields.io/badge/Made%20with-Nuwa.skill-orange)](https://github.com/alchaincyf/nuwa-skill)

<br>

**Natural Language → Part Design → Assembly → Motion Simulation → Industrial Output. One sentence, one complete CAD project.**

<br>

<img src="preview.png" alt="build123d Spur Gear Example — OCP CAD Viewer" width="720">

*Spur Gear — OCP CAD Viewer Live Preview*

<br>

<img src="enclosure_explode.gif" alt="Enclosure Exploded Animation — Assembly & Disassembly Demo" width="720">

*Enclosure Exploded Animation — Auto Assembly & Disassembly Demo*

<br>

Combines Dave Cowden's modeling philosophy "Think like a machinist" with Peter Corke's simulation philosophy "Learn by doing".<br>
Covers part modeling, assembly & exploded animation, surface/joint/mounting, manufacturing verification, FK/IK/gait/URDF/PyBullet — the full pipeline.<br>
25+ runnable examples, 8 categories of reference docs, 10 utility scripts.<br>
Describe the part you want in one sentence — from sketch to motion simulation, done.

[Examples](#examples) · [Installation](#installation) · [What's Included](#whats-included) · [Part Gallery](#part-gallery)

</div>

---

## Examples

### Prompt: Make a 100x80x50 mounting plate with M5 bolt holes at four corners

```python
# === Parameters ===
plate_l, plate_w, plate_h = 100, 80, 10
hole_r = 2.5          # M5 through hole
margin = 10           # hole offset from edge

# === Modeling ===
with BuildPart() as plate:
    Box(plate_l, plate_w, plate_h)
    with GridLocations(plate_l - 2*margin, plate_w - 2*margin, 2, 2):
        Hole(radius=hole_r)
    top = plate.faces().sort_by(Axis.Z)[-1]
    fillet(top.edges(), radius=3)

# === Export ===
export_step(plate.part, "mounting_plate.step")
```

### Prompt: Make a heat sink with 8 fins on a base plate

```python
# === Parameters ===
base_l, base_w, base_h = 80, 60, 5
fin_h, fin_t = 25, 1.5
fin_count = 8

# === Modeling ===
with BuildPart() as heatsink:
    Box(base_l, base_w, base_h)                    # base plate
    with BuildSketch(heatsink.faces().sort_by(Axis.Z)[-1]):
        with GridLocations(0, base_w / (fin_count + 1), 1, fin_count):
            Rectangle(base_l - 4, fin_t)
    extrude(amount=fin_h)                          # extrude fins

export_step(heatsink.part, "heat_sink.step")
```

### Prompt: I need a 90-degree pipe elbow

```python
# === Parameters ===
outer_r, wall_t = 15, 2
bend_r = 40

# === Modeling ===
path = Edge.make_circle(bend_r, start_angle=0, end_angle=90)
with BuildPart() as elbow:
    with BuildSketch(Plane(path @ 0, z_dir=path % 0)):
        Circle(outer_r)
        Circle(outer_r - wall_t, mode=Mode.SUBTRACT)
    sweep(path=path)

export_step(elbow.part, "pipe_elbow.step")
```

### Prompt: Make an enclosure with a lid, and generate an exploded animation

After part modeling is complete, the skill automatically offers to generate assembly preview and exploded animation:

```python
from build123d import *
from ocp_vscode import show, Animation

# ===== Explode Parameters =====
explode_dist = 30                              # total explode distance mm
half = explode_dist / 2

# ===== Show assembled state (animation start) =====
show(body, assembled_lid,
     names=["body", "lid"],
     colors=["steelblue", "orange"])

# ===== Explode animation: open 2s → hold 10s → close 2s → hold 2s (16s loop) =====
t = [0, 2, 12, 14, 16]

animation = Animation()
animation.add_track("/Group/body", "t", t,
                    [[0,0,0], [0,0,-half], [0,0,-half], [0,0,0], [0,0,0]])
animation.add_track("/Group/lid",  "t", t,
                    [[0,0,0], [0,0,half],  [0,0,half],  [0,0,0], [0,0,0]])
animation.animate(1)
```

> Full example in [`assets/assembly/`](assets/assembly/): [`13_enclosure_box.py`](assets/assembly/13_enclosure_box.py) (parts) + [`13_enclosure_assembly.py`](assets/assembly/13_enclosure_assembly.py) (assembly) + [`13_enclosure_exploded.py`](assets/assembly/13_enclosure_exploded.py) (exploded animation)

> Plus 20+ runnable examples covering parts, assembly preview, surface modeling, joint assemblies, and mounting templates.

This is not template-based code completion. Every piece of code applies Dave Cowden's modeling philosophy — "operation sequence thinking," "design intent first," "selectors over coordinates," "STEP first." It doesn't stitch APIs together; it models parts through a machinist's cognitive framework.

---

## Installation

```bash
npx skills add baibai2013/build123d-cad
```

Then in Claude Code:

```
> Build a flange with 6 evenly spaced bolt holes
> Make a PCB standoff with M3 threaded hole
> Generate a thin-wall enclosure, 2mm wall thickness
> Make a stepped shaft with a keyway
```

### Prerequisites

```bash
pip install build123d            # CAD kernel
pip install ocp-vscode           # VS Code 3D preview
code --install-extension bernhard-42.ocp-cad-viewer  # VS Code CAD viewer extension
```

---

## What's Included

### 5 Mental Models (from Dave Cowden's Modeling Philosophy)

| Model | One-liner | Source |
|-------|-----------|--------|
| **Operation Sequence Thinking** | CAD code describes machining steps (pick face → sketch → extrude), not coordinate math | CadQuery design philosophy |
| **Design Intent First** | Use `sort_by`/`filter_by` to capture "why it's here," not hard-code "where it is" | CadQuery selector system |
| **Python Ecosystem as Superpower** | Parts are Python objects — loops, functions, parametrics come free | CadQuery design philosophy |
| **Working > Pretty** | Running prototype code > elegant but broken code; ship the part first | Engineering practice |
| **STEP First** | STEP is the universal language of CAD; STL is only for 3D printing | Industry standard |

### 8 Code Quality Heuristics

1. **"Can you describe this to a machinist?"** — If you can't explain it clearly, the code has a problem
2. **"Does it still work if you change one dimension?"** — If not, you've hard-coded coordinates
3. **"Selector or coordinate?"** — Use `.sort_by()` wherever possible, never raw numbers
4. **"Is there a cleaner way?"** — Builder Mode context > intermediate variables
5. **"STEP or STL?"** — CNC/assembly always gets STEP
6. **"Working beats pretty"** — Ship the part first, optimize code later
7. **"Fewer lines = better design"** — Code volume is an inverse quality indicator
8. **"'Not yet' instead of 'impossible'"** — State the limitation, give a time estimate

### 11 Modeling Patterns

| Pattern | Typical Parts |
|---------|---------------|
| Flat plate + hole array | Mounting plates, panels |
| Revolution + polar array | Flanges, gears |
| Extrude + boolean subtract | Brackets, enclosures |
| Thin-wall shell | Boxes, housings |
| Stepped revolution + slot cut | Shafts, pins |
| Cylinder + thread/step | Standoffs, studs |
| Path sweep | Pipe elbows, rails |
| Multi-section loft | Transitional shapes |
| Root solid + per-feature fusion | Gears (complex polygons) |
| Hinge / multi-body | Assembly parts |
| Countersink / counterbore | Fastener mounting plates |

---

## Part Gallery

### Parts (`assets/parts/`)

| # | Part | Difficulty | Key Techniques |
|---|------|-----------|----------------|
| 01 | [Mounting Plate](assets/parts/01_mounting_plate.py) | ★ | Box + GridLocations + Hole |
| 02 | [Flange](assets/parts/02_flange.py) | ★★ | Cylinder + PolarLocations |
| 03 | [L-Bracket](assets/parts/03_l_bracket.py) | ★★ | Multi-extrude + Fillet |
| 04 | [Enclosure](assets/parts/04_enclosure.py) | ★★★ | Shell + wall thickness |
| 05 | [Stepped Shaft](assets/parts/05_shaft.py) | ★★★ | Revolve + keyway cut |
| 06 | [PCB Standoff](assets/parts/06_pcb_standoff.py) | ★★ | Concentric cylinders |
| 07 | [Pipe Elbow](assets/parts/07_pipe_elbow.py) | ★★★ | Sweep + hollow section |
| 08 | [Spur Gear](assets/parts/08_gear_spur_v2.py) | ★★★★★ | Root cylinder + per-tooth fusion |
| 09 | [Hinge](assets/parts/09_hinge.py) | ★★★★ | Multi-body assembly |
| 10 | [Heat Sink](assets/parts/10_heat_sink.py) | ★★★ | GridLocations + fin extrude |
| 11 | [Countersunk Plate](assets/parts/11_countersunk_plate.py) | ★★ | CounterSinkHole |
| 12 | [Snap-Fit Clip](assets/parts/12_snap_fit_clip.py) | ★★★★ | Complex profile extrude |
| 13 | [Enclosure Box](assets/assembly/13_enclosure_box.py) | ★★★ | Shell + snap-fit lid |

### Surface Modeling (`assets/surface/`)

| # | Part | Difficulty | Key Techniques |
|---|------|-----------|----------------|
| 14 | [Organic Shell](assets/surface/14_organic_shell.py) | ★★★★ | Multi-section Loft + Shell |
| 15 | [Loft Transition](assets/surface/15_loft_transition.py) | ★★★ | Circle→Square→Circle Loft |

### Joint Assembly (`assets/joints/`)

| # | Part | Difficulty | Key Techniques |
|---|------|-----------|----------------|
| 16 | [Revolute Hinge](assets/joints/16_revolute_hinge.py) | ★★★ | RevoluteJoint + connect_to |
| 17 | [Quadruped Leg](assets/joints/17_quadruped_leg.py) | ★★★★★ | Multi-joint chain hip→knee→ankle→foot |

### Mounting Templates (`assets/mounting/`)

| # | Part | Difficulty | Key Techniques |
|---|------|-----------|----------------|
| 18 | [Servo Mount SG90](assets/mounting/18_servo_mount_sg90.py) | ★★★ | Servo cavity + ear slots + cable exit |
| 19 | [PCB Enclosure](assets/mounting/19_pcb_enclosure.py) | ★★★★ | Standoffs + USB-C opening + snap lid |
| 20 | [Sensor Bracket](assets/mounting/20_sensor_bracket.py) | ★★★ | HC-SR04 ultrasonic twin windows |

### Assembly & Animation (`assets/assembly/`)

| File | Content |
|------|---------|
| [13_enclosure_assembly.py](assets/assembly/13_enclosure_assembly.py) | Enclosure assembly preview |
| [13_enclosure_exploded.py](assets/assembly/13_enclosure_exploded.py) | Enclosure exploded animation (16s loop) |

### Motion Simulation (`assets/simulation/`)

| # | Example | Difficulty | Key Techniques |
|---|---------|-----------|----------------|
| 21 | [FK Leg Chain](assets/simulation/21_fk_leg_chain.py) | ★★ | DH homogeneous transforms + OCP visualization |
| 22 | [IK Single Leg](assets/simulation/22_ik_single_leg.py) | ★★★ | Analytical IK + dual configuration comparison |
| 23 | [Workspace Cloud](assets/simulation/23_workspace_cloud.py) | ★★ | FK point cloud + reachability visualization |
| 24 | [Gait Generator](assets/simulation/24_gait_generator.py) | ★★★★ | Bezier trajectory + IK + OCP animation |
| 25 | [URDF Export](assets/simulation/25_urdf_export.py) | ★★★ | build123d → URDF + STL |

---

## Utility Scripts

The `scripts/` directory contains 10 utility tools organized by function:

### Validation (`scripts/validate/`)

| Script | Function |
|--------|----------|
| [`validate_part.py`](scripts/validate/validate_part.py) | BRep validation, volume/bounding box checks |
| [`assembly_check.py`](scripts/validate/assembly_check.py) | Assembly collision detection (multi-STEP interference) |

### Analysis (`scripts/analysis/`)

| Script | Function |
|--------|----------|
| [`extract_params.py`](scripts/analysis/extract_params.py) | Extract parametric variables from scripts |
| [`step_info.py`](scripts/analysis/step_info.py) | STEP file metadata inspection |
| [`mass_properties.py`](scripts/analysis/mass_properties.py) | Mass/inertia analysis (13 material presets) |

### Export (`scripts/export/`)

| Script | Function |
|--------|----------|
| [`batch_export.py`](scripts/export/batch_export.py) | Batch export all parts (multi-format) |
| [`print_export.py`](scripts/export/print_export.py) | Print export (STL/3MF + 4 quality presets) |

### Assembly (`scripts/assembly/`)

| Script | Function |
|--------|----------|
| [`explode_generator.py`](scripts/assembly/explode_generator.py) | Universal exploded animation code generator |

### Simulation (`scripts/simulation/`)

| Script | Function |
|--------|----------|
| [`export_urdf.py`](scripts/simulation/export_urdf.py) | STEP → URDF automatic export (traverse Compound) |
| [`pybullet_preview.py`](scripts/simulation/pybullet_preview.py) | PyBullet URDF loading + gait preview |

---

## Repository Structure

```
build123d-cad/
├── README.md / README_EN.md              # Chinese / English README
├── SKILL.md                              # Core skill definition (installable)
├── references/                           # 8 categories of reference docs
│   ├── parts/                            # Part modeling
│   │   ├── cheatsheet.md                 #   API quick reference
│   │   ├── patterns.md                   #   11 modeling patterns
│   │   └── surface-modeling.md           #   Surface modeling (Loft/Sweep/NURBS)
│   ├── assembly/                         # Assembly workflow
│   │   ├── joints-reference.md           #   Joints system (5 types + full params)
│   │   ├── assembly-patterns.md          #   8 assembly patterns
│   │   ├── mounting-experience.md        #   Mounting templates (servo/PCB/sensor)
│   │   └── exploded-animation.md         #   Exploded animation
│   ├── ocp/                              # OCP CAD Viewer
│   │   ├── show-reference.md             #   show() 100+ parameters
│   │   ├── animation-reference.md        #   Animation API
│   │   └── studio-materials.md           #   PBR materials/lighting
│   ├── process/                          # Manufacturing processes
│   │   ├── 3d-printing.md                #   3D printing design rules
│   │   ├── cnc-machining.md              #   CNC machining
│   │   ├── laser-cutting.md              #   Laser cutting
│   │   └── cross-domain.md              #   Cross-domain (FEA/kinematics/PCB)
│   ├── dave-cowden/                      # Dave Cowden philosophy
│   │   └── assembly-philosophy.md        #   Assembly philosophy & honest boundaries
│   ├── verify/                           # Verification
│   │   ├── cadcodeverify.md              #   3-layer verification architecture
│   │   ├── manual-checklist.md           #   Manual verification checklist
│   │   └── visual-verification.md        #   OCP visual verification
│   ├── peter-corke/                      # Peter Corke simulation philosophy
│   │   └── simulation-philosophy.md      #   "Learn by doing" + DH standard
│   └── simulation/                       # Motion simulation
│       ├── forward-kinematics.md         #   FK: DH params + homogeneous transforms
│       ├── inverse-kinematics.md         #   IK: analytical/numerical + workspace
│       ├── gait-planning.md              #   Gait: Bezier trajectory + IK
│       ├── urdf-export.md                #   URDF: build123d → URDF end-to-end
│       └── pybullet-quickstart.md        #   PyBullet quick start
├── assets/                               # 25+ runnable examples
│   ├── parts/                            #   13 parts (01~13)
│   ├── assembly/                         #   Assembly preview + exploded animation
│   ├── surface/                          #   Surface modeling examples
│   ├── joints/                           #   Joint assembly examples
│   ├── mounting/                         #   Mounting template examples
│   └── simulation/                       #   Motion simulation (FK/IK/gait/URDF)
└── scripts/                              # 10 utility scripts
    ├── validate/                         #   Geometry validation + collision detection
    ├── analysis/                         #   Param extraction + STEP info + mass analysis
    ├── export/                           #   Batch export + print export
    ├── assembly/                         #   Exploded animation generator
    └── simulation/                       #   URDF export + PyBullet preview
```

---

## How This Skill Was Built

Generated with assistance from [Nuwa.skill](https://github.com/alchaincyf/nuwa-skill).

Nuwa's workflow: input a name → multi-agent parallel research → cross-validate and distill mental models → build SKILL.md → quality verification.

Want to distill other domain expert skills? Install Nuwa:

```bash
npx skills add alchaincyf/nuwa-skill
```

---

## Disclaimer

This skill is intended for engineering exploration and learning. Reference documentation and examples are compiled from publicly available online resources. Design suggestions generated with AI assistance should be reviewed with professional tools; actual manufacturing tolerances should be adjusted based on your specific process. Upstream dependencies evolve; some example code may require adaptation. Provided as-is, without warranty of fitness for a particular purpose.

---

## License

Apache License 2.0 — Use it, modify it, model anything. Commercial use allowed, with explicit patent grant, consistent with upstream [build123d](https://github.com/gumyr/build123d) (Apache 2.0). See [LICENSE](LICENSE).

---

<div align="center">

*Think like a machinist, not a programmer.*

<br>

Apache License 2.0

Made with [Nuwa.skill](https://github.com/alchaincyf/nuwa-skill)

</div>
