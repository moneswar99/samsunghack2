# Samsung XR Hackathon 2026 – Track 01
## Synthetic Eye Movement & Virtual Camera Rendering

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Blender](https://img.shields.io/badge/Blender-4.2%20%7C%204.5%20%7C%205.3-orange.svg)](https://www.blender.org/)
[![Tests](https://img.shields.io/badge/Tests-9%2F9%20Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)]()

---

## 1. Project Introduction & Problem Statement

This project provides a complete, mathematically calibrated, and fully automated implementation for **Samsung R&D Institute India XR Hackathon 2026 – Track 01: Synthetic Eye Movement & Virtual Camera Rendering**.

In Extended Reality (XR) headsets, accurate eye tracking and gaze estimation are essential for foveated rendering, virtual avatar interaction, and near-eye display calibration. Training and evaluating computer vision gaze estimation algorithms requires high-fidelity synthetic ground truth with authentic 3D eyeball rotation, realistic binocular vergence, and synchronized camera calibration.

### Core Objectives:
1. **Articulatable Textured Human Head**: Anatomically proportioned face model with realistic skin shader, orbital sockets, and two separate spherical eyeballs ($24\,\text{mm}$ diameter) containing sclera, iris, and pupil.
2. **True 3D Eyeball Rotation**: Programmatic rotation of both eyeballs around their physical centers (IPD $64\,\text{mm}$ at $X = \pm 0.032\,\text{m}$), strictly avoiding 2D pupil translation artifacts.
3. **Calibrated Binocular Convergence**: Dynamic vergence on a fixation plane located at $35\,\text{cm}$ ($0.35\,\text{m}$) forward from the eye midpoint.
4. **Fixed Virtual Camera**: Calibrated pinhole camera positioned exactly $40\,\text{cm}$ ($0.40\,\text{m}$) forward from the eye midpoint with $1024 \times 1024$ resolution.
5. **Standardized Python API**: Clean `Eyes` controller class exposing `eyes.move(h, v)`, `eyes.reset()`, and `eyes.render()`.
6. **Ground-Truth Validation Suite**: Automated five-direction validation (Left, Right, Up, Down, Reset), ten clockwise gaze samples ($\theta_k = 2\pi k / 10$), ground-truth `metadata.json`, and an annotated $5 \times 2$ `contact_sheet.png`.

---

## 2. Mathematical Calibration & System Architecture

### 2.1 Coordinate Conventions & World Geometry
Blender metric units ($1.0\,\text{unit} = 1.0\,\text{meter}$) are used throughout:
* **Eye Midpoint**: $M = (0.0, 0.0, 0.0)\,\text{m}$
* **Left Eye Center ($C_L$)**: $(+0.032, 0.0, 0.0)\,\text{m}$ ($32\,\text{mm}$ left)
* **Right Eye Center ($C_R$)**: $(-0.032, 0.0, 0.0)\,\text{m}$ ($32\,\text{mm}$ right)
* **Interpupillary Distance (IPD)**: $64\,\text{mm}$ ($0.064\,\text{m}$)
* **Eyeball Radius ($R_{eye}$)**: $12\,\text{mm}$ ($0.012\,\text{m}$, diameter $24\,\text{mm}$)
* **Forward Gaze Axis**: $-Y$ axis
* **Vertical Axis**: $+Z$ axis (Up)
* **Lateral Axis**: $+X$ axis (Subject's Left)

### 2.2 Fixation Plane & Binocular Convergence Math
Human eyes naturally converge inward when focusing on near targets ($35\,\text{cm}$).
Given normalized horizontal and vertical gaze inputs $h, v \in [-1.0, +1.0]$:

$$\theta_H = h \cdot \theta_{H,\max}, \quad \theta_V = v \cdot \theta_{V,\max}$$

where the voluntary oculomotor limits are $\theta_{H,\max} = 25^\circ$ ($0.4363\,\text{rad}$) and $\theta_{V,\max} = 20^\circ$ ($0.3491\,\text{rad}$).

At fixation distance $D = 0.35\,\text{m}$:
$$X_T(h) = D \cdot \tan(\theta_H), \quad Z_T(v) = D \cdot \tan(\theta_V), \quad Y_T = -D = -0.35\,\text{m}$$

The 3D fixation target point is $P_T = (X_T, -0.35, Z_T)$.

The gaze vectors for the Left and Right eyes are:
$$\vec{V}_L = P_T - C_L = (X_T - 0.032, -0.35, Z_T)$$
$$\vec{V}_R = P_T - C_R = (X_T + 0.032, -0.35, Z_T)$$

At center rest ($h = 0, v = 0$):
$$\vec{V}_L = (-0.032, -0.35, 0) \implies \text{inward vergence angle } \alpha = \arctan\left(\frac{0.032}{0.35}\right) \approx 5.23^\circ$$
$$\vec{V}_R = (+0.032, -0.35, 0) \implies \text{inward vergence angle } \alpha = \arctan\left(\frac{0.032}{0.35}\right) \approx 5.23^\circ$$

Both eyes point directly at the fixation target while rotating around their exact physical sphere centers $C_L$ and $C_R$.

### 2.3 Camera Calibration
* **Position**: $(0.0, -0.40, 0.0)\,\text{m}$ (exactly $40\,\text{cm}$ in front of eye midpoint)
* **Orientation**: Euler angles $(90^\circ, 0^\circ, 0^\circ)$, facing along $+Y$ directly into the eyes
* **Focal Length**: $f = 50.0\,\text{mm}$
* **Sensor Size**: $36.0 \times 36.0\,\text{mm}$ (1:1 square sensor)
* **Resolution**: $1024 \times 1024$ pixels
* **Intrinsic Camera Matrix ($K$)**:

$$K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix} = \begin{bmatrix} 1422.2222 & 0.0 & 512.0 \\ 0.0 & 1422.2222 & 512.0 \\ 0.0 & 0.0 & 1.0 \end{bmatrix}$$

where $f_x = f_y = 50.0 \times \frac{1024}{36.0} = 1422.2222\,\text{px}$, and principal point $(c_x, c_y) = (512.0, 512.0)$.

---

## 3. Project Architecture

```text
Samsung_XR_Track01/
│
├── scene.blend                  # Fully configured Blender 3D scene (head, eyes, rig, camera, lights)
│
├── wrapper/
│   ├── __init__.py              # Python package interface
│   └── eyes.py                  # Reusable Eyes automation controller (move, reset, render)
│
├── renders/
│   ├── frame_00.png             # Clockwise sample 00 (theta = 0.0000 rad | Up)
│   ├── frame_01.png             # Clockwise sample 01 (theta = 0.6283 rad | Up-Right)
│   ├── frame_02.png             # Clockwise sample 02 (theta = 1.2566 rad | Right-Up)
│   ├── frame_03.png             # Clockwise sample 03 (theta = 1.8850 rad | Right-Down)
│   ├── frame_04.png             # Clockwise sample 04 (theta = 2.5133 rad | Down-Right)
│   ├── frame_05.png             # Clockwise sample 05 (theta = 3.1416 rad | Down)
│   ├── frame_06.png             # Clockwise sample 06 (theta = 3.7699 rad | Down-Left)
│   ├── frame_07.png             # Clockwise sample 07 (theta = 4.3982 rad | Left-Down)
│   ├── frame_08.png             # Clockwise sample 08 (theta = 5.0265 rad | Left-Up)
│   └── frame_09.png             # Clockwise sample 09 (theta = 5.6549 rad | Up-Left)
│
├── metadata.json                # Complete ground-truth metadata per rendered frame
│
├── tests/
│   └── test_eye_movement.py     # 9-point automated test suite
│
├── scripts/
│   ├── build_scene.py           # Procedural scene generator
│   ├── validate_five_directions.py # 5-direction displacement validator
│   ├── generate_ten_renders.py  # 10 clockwise frames & metadata generator
│   └── create_contact_sheet.py  # Contact sheet generator
│
├── contact_sheet.png            # 5x2 labeled overview grid of all 10 renders
│
├── README.md                    # Project documentation
└── requirements.txt             # Python dependencies
```

---

## 4. Installation & Environment Setup

### 4.1 Prerequisites
* **Operating System**: Windows 10/11, Linux, or macOS.
* **Blender**: Version 4.2 LTS, 4.5 LTS, or 5.x (tested on Blender 5.3.0).
* **Python**: Version 3.10+ (tested on Python 3.13 & 3.14).

### 4.2 Install Python Dependencies
```bash
pip install -r requirements.txt
```

---

## 5. API Reference & Usage

The `wrapper/eyes.py` module exposes the `Eyes` class for programmatically controlling gaze and rendering.

### 5.1 Quick Start
```python
import os
from wrapper.eyes import Eyes

# Initialize controller and load the calibrated scene
scene_path = os.path.abspath("scene.blend")
eyes = Eyes(scene_path=scene_path)

# Move eyes: horizontal right (h=+0.8), vertical up (v=+0.5)
eyes.move(h=0.8, v=0.5)

# Query actual projected 2D pupil coordinates (pixels, top-left origin)
pupil_l = eyes.get_pupil_center_2d('L')
pupil_r = eyes.get_pupil_center_2d('R')
print(f"Left Pupil: {pupil_l}, Right Pupil: {pupil_r}")

# Render to 1024x1024 PNG
output_png = eyes.render("renders/my_render.png")

# Reset eyes back to baseline center fixation (zero drift)
eyes.reset()
```

### 5.2 Function Documentation

#### `eyes.move(h: float, v: float)`
* **Parameters**:
  * `h` (float): Normalized horizontal gaze input in $[-1.0, +1.0]$.
    * $h > 0$: Gaze shifts towards the subject's right ($+X$).
    * $h < 0$: Gaze shifts towards the subject's left ($-X$).
  * `v` (float): Normalized vertical gaze input in $[-1.0, +1.0]$.
    * $v > 0$: Gaze shifts upward ($+Z$).
    * $v < 0$: Gaze shifts downward ($-Z$).
* **Behavior**: Clamps inputs outside $[-1.0, 1.0]$. Calculates the 3D fixation point on the $35\,\text{cm}$ plane and computes the exact 3D orientation for bones `Eye_L` and `Eye_R` around their respective physical sphere centers.

#### `eyes.reset()`
* **Behavior**: Restores the baseline converged center fixation ($h = 0.0, v = 0.0$). Deterministic and drift-free regardless of how many intermediate movements were executed.

#### `eyes.render(filepath: Optional[str] = None) -> str`
* **Parameters**: `filepath` (str, optional): Target PNG output path.
* **Behavior**: Renders the scene through `GazeCamera` at $1024 \times 1024$ resolution and saves a PNG file.

#### `eyes.get_pupil_center_2d(side: str) -> Tuple[float, float]`
* **Parameters**: `side` ('L' or 'R').
* **Returns**: Actual projected 2D coordinates `(px, py)` in pixels with top-left origin $[0, 1024]$.

#### `eyes.get_eye_rotation_euler(side: str) -> List[float]`
* **Parameters**: `side` ('L' or 'R').
* **Returns**: 3D world Euler rotation angles `[rx, ry, rz]` in degrees.

#### `eyes.get_camera_calibration() -> dict`
* **Returns**: Dictionary with intrinsic $3 \times 3$ matrix $K$, extrinsic $4 \times 4$ matrix $[R | t]$, focal length, sensor dimensions, and resolution.

---

## 6. Execution Instructions

### 6.1 Run the Full Test Suite
Execute the 9-point verification suite from standard Python or Blender:

```bash
# Direct execution (automatically connects to Blender)
python tests/test_eye_movement.py
```
Or directly inside Blender:
```bash
blender --factory-startup --background scene.blend --python tests/test_eye_movement.py
```

### 6.2 Run Five-Direction Validation
```bash
blender --factory-startup --background scene.blend --python scripts/validate_five_directions.py
```

### 6.3 Generate All Ten Clockwise Renders and Metadata
```bash
blender --factory-startup --background scene.blend --python scripts/generate_ten_renders.py
```

### 6.4 Generate Contact Sheet
```bash
python scripts/create_contact_sheet.py
```

---

## 7. Five-Direction Validation Results

Executed on actual projected pupil positions:

| Direction | Input $(h, v)$ | Left Eye $(X, Y)$ | Right Eye $(X, Y)$ | $\Delta X_L$ | $\Delta X_R$ | $\Delta Y_L$ | $\Delta Y_R$ | Status |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline** | $(0.0, 0.0)$ | $(625.28, 512.00)$ | $(398.72, 512.00)$ | $0.00$ | $0.00$ | $0.00$ | $0.00$ | **PASS** |
| **Left** | $(-1.0, 0.0)$ | $(607.50, 512.00)$ | $(379.52, 512.00)$ | $-17.78\,\text{px}$ | $-19.20\,\text{px}$ | $0.00\,\text{px}$ | $0.00\,\text{px}$ | **PASS** |
| **Right** | $(+1.0, 0.0)$ | $(644.48, 512.00)$ | $(416.50, 512.00)$ | $+19.20\,\text{px}$ | $+17.78\,\text{px}$ | $0.00\,\text{px}$ | $0.00\,\text{px}$ | **PASS** |
| **Up** | $(0.0, +1.0)$ | $(625.31, 497.04)$ | $(398.69, 497.04)$ | $+0.03\,\text{px}$ | $-0.03\,\text{px}$ | $-14.96\,\text{px}$ | $-14.96\,\text{px}$ | **PASS** |
| **Down** | $(0.0, -1.0)$ | $(625.31, 526.96)$ | $(398.69, 526.96)$ | $+0.03\,\text{px}$ | $-0.03\,\text{px}$ | $+14.96\,\text{px}$ | $+14.96\,\text{px}$ | **PASS** |
| **Reset** | $(0.0, 0.0)$ | $(625.28, 512.00)$ | $(398.72, 512.00)$ | $0.00\,\text{px}$ | $0.00\,\text{px}$ | $0.00\,\text{px}$ | $0.00\,\text{px}$ | **PASS** |

> **Note on Vergence Asymmetry**: Notice that during horizontal gaze, the adducting (inward turning) eye rotates by a slightly different angle than the abducting (outward turning) eye. This is physical proof of true 3D binocular convergence at a finite distance ($35\,\text{cm}$).

---

## 8. Ten Clockwise Gaze Sequence & Metadata

Ten frames were generated along a circular trajectory:
$$\theta_k = \frac{2\pi k}{10}, \quad h = \sin(\theta_k), \quad v = \cos(\theta_k) \quad \text{for } k = 0, \dots, 9$$

![Contact Sheet](contact_sheet.png)

### Summary of Rendered Samples:
* **Frame 00** ($\theta = 0.000\,\text{rad}$): $h = 0.000, v = +1.000$ (Top / Up)
* **Frame 01** ($\theta = 0.628\,\text{rad}$): $h = +0.588, v = +0.809$ (Top-Right)
* **Frame 02** ($\theta = 1.257\,\text{rad}$): $h = +0.951, v = +0.309$ (Right-Up)
* **Frame 03** ($\theta = 1.885\,\text{rad}$): $h = +0.951, v = -0.309$ (Right-Down)
* **Frame 04** ($\theta = 2.513\,\text{rad}$): $h = +0.588, v = -0.809$ (Bottom-Right)
* **Frame 05** ($\theta = 3.142\,\text{rad}$): $h = 0.000, v = -1.000$ (Bottom / Down)
* **Frame 06** ($\theta = 3.770\,\text{rad}$): $h = -0.588, v = -0.809$ (Bottom-Left)
* **Frame 07** ($\theta = 4.398\,\text{rad}$): $h = -0.951, v = -0.309$ (Left-Down)
* **Frame 08** ($\theta = 5.027\,\text{rad}$): $h = -0.951, v = +0.309$ (Left-Up)
* **Frame 09** ($\theta = 5.655\,\text{rad}$): $h = -0.588, v = +0.809$ (Top-Left)

### Metadata Schema (`metadata.json`):
```json
{
  "frame": 3,
  "theta": 1.885,
  "input": {
    "h": 0.9511,
    "v": -0.309
  },
  "eye_rotation_L": [
    -5.8374,
    -0.0,
    -160.7543
  ],
  "eye_rotation_R": [
    -5.4609,
    0.0,
    -151.9875
  ],
  "pupil_center_2D_L": [
    643.473,
    516.465
  ],
  "pupil_center_2D_R": [
    415.629,
    516.17
  ],
  "camera_matrix": [
    [1422.2222, 0.0, 512.0],
    [0.0, 1422.2222, 512.0],
    [0.0, 0.0, 1.0]
  ]
}
```

---

## 9. Automated Testing & Reliability Summary

All 9 validation criteria passed with zero errors:

| Test ID | Test Name | Validation Criterion | Result |
|:---:|:---|:---|:---:|
| `test_01` | `test_blender_scene_exists` | File `scene.blend` exists and size $> 50\,\text{KB}$ | **PASS** |
| `test_02` | `test_eye_bones_and_pivots` | `Eye_L`, `Eye_R` bones present, pivots at $(\pm 0.032, 0, 0)$ | **PASS** |
| `test_03` | `test_camera_calibration_and_distance` | Camera at $0.40\,\text{m}$ forward, $f=50\,\text{mm}$ | **PASS** |
| `test_04` | `test_resolution_and_format` | Render output $1024 \times 1024$ PNG | **PASS** |
| `test_05` | `test_five_direction_gaze_movement` | Measured 2D pupil displacement for Left, Right, Up, Down, Reset | **PASS** |
| `test_06` | `test_reset_drift_free_reliability` | Zero drift ($< 0.005\,\text{px}$) after multi-movement sequence | **PASS** |
| `test_07` | `test_ten_rendered_frames_exist_and_valid` | `frame_00.png` through `frame_09.png` valid PNGs | **PASS** |
| `test_08` | `test_metadata_json_schema_and_values` | 10 valid JSON records matching required structure | **PASS** |
| `test_09` | `test_contact_sheet_exists` | `contact_sheet.png` exists and is a valid image | **PASS** |

---

## 10. Known Limitations & Future Work
1. **Dynamic Eyelid Deformation**: The current model keeps eyelids static during extreme vertical gaze; future iterations could couple bone vertical pitch to eyelid shape keys.
2. **Corneal Refraction**: Eyeball geometry uses direct surface projection; ray-traced refractive cornea modeling can be enabled via Cycles rendering for sub-millimeter refractive parallax studies.
3. **Head Motion Coupling**: Gaze movement currently isolates ocular rotation (vestibulo-ocular reflex / pure saccades); neck bone rotations can be added for combined head-eye coordination.

---

## 11. Author & Hackathon Submission
* **Event**: Samsung R&D Institute India XR Hackathon 2026
* **Track**: Track 01 – Synthetic Eye Movement & Virtual Camera Rendering
* **Repository**: `Samsung_XR_Track01`
* **Status**: Complete, Tested, and Verified
