# Samsung XR Eyes SDK (`samsung-xr-eyes`)
## Official SDK for Track 01: Synthetic Eye Movement & Virtual Camera

`samsung-xr-eyes` is a lightweight, high-performance Python SDK providing programmatic control of 3D eyeball rotation, realistic binocular convergence, and camera ground-truth data generation in Blender and XR rendering pipelines.

---

### Installation

From local wheel or package directory:
```bash
pip install dist/samsung_xr_eyes-1.0.0-py3-none-any.whl
```
Or from source:
```bash
pip install .
```

---

### Quick Start

```python
import os
from samsung_xr_eyes import Eyes

# 1. Initialize controller
eyes = Eyes(scene_path="scene.blend")

# 2. Command calibrated 3D gaze movement (h in [-1, 1], v in [-1, 1])
eyes.move(h=0.75, v=0.50)

# 3. Retrieve ground-truth projected pupil coordinates (pixels, top-left origin)
pupil_l = eyes.get_pupil_center_2d('L')
pupil_r = eyes.get_pupil_center_2d('R')
print(f"Pupil L: {pupil_l}, Pupil R: {pupil_r}")

# 4. Retrieve 3D Euler rotations (degrees)
rot_l = eyes.get_eye_rotation_euler('L')
rot_r = eyes.get_eye_rotation_euler('R')

# 5. Render frame to 1024x1024 PNG
eyes.render("renders/frame_custom.png")

# 6. Reset to baseline converged center fixation (zero drift)
eyes.reset()
```

---

### API Highlights

* `eyes.move(h: float, v: float)`: Programs 3D eyeball rotation around physical sphere centers with realistic 35 cm binocular convergence. Clamps inputs to $[-1.0, 1.0]$.
* `eyes.reset()`: Restores calibrated baseline center gaze ($h=0.0, v=0.0$) with zero accumulated drift.
* `eyes.render(filepath: Optional[str]) -> str`: Renders through fixed virtual camera ($40\,\text{cm}$ distance) to $1024 \times 1024$ PNG.
* `eyes.get_pupil_center_2d(side: str) -> Tuple[float, float]`: Returns exact sub-pixel $(px, py)$ coordinates.
* `eyes.get_eye_rotation_euler(side: str) -> List[float]`: Returns 3D world rotation vector $[R_x, R_y, R_z]$ in degrees.
* `eyes.get_camera_calibration() -> dict`: Returns $3 \times 3$ intrinsic matrix $K$ and $4 \times 4$ extrinsic matrix.
