---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #090d16
color: #f8fafc
---

# Samsung XR Hackathon 2026
## Track 01: Synthetic Eye Movement & Virtual Camera Rendering

**Participant:** DSS Srikar / Track 01  
**Status:** All 9 Tests Passing (100%)  
**Repository:** `Samsung_XR_Track01`

---

## 1. Executive Summary & Problem Context

Next-generation Extended Reality (XR) headsets demand sub-degree accurate gaze tracking for:
* **Foveated Rendering:** Reducing compute power by concentrating detail on the fovea.
* **Spatial UI Interaction:** Precision hands-free gaze selection.
* **Realistic Digital Avatars:** Natural gaze contact in telepresence.

**The Challenge:**
Standard datasets often simulate gaze by simply translating pupil textures in 2D, causing severe projection, parallax, and depth errors. Track 01 demands **physically authentic 3D eyeball rotation**, **calibrated binocular convergence**, and **sub-pixel ground truth extraction**.

---

## 2. Anatomical Rigging & 3D Eyeball Pivots

* **Anatomical Proportioning:** Head model with realistic facial contours and orbital sockets.
* **Dual Spherical Eyeballs:** Two $24\,\text{mm}$ diameter spheres (radius $0.012\,\text{m}$) located at $X = \pm 0.032\,\text{m}$ (IPD = $64\,\text{mm}$).
* **Bone Rigging:** Bones `Eye_L` and `Eye_R` with rotation pivots pinned to the physical eyeball centers.
* **Photorealistic Materials:** High-resolution hazel iris with radial striations, dark limbal ring, and pupil. Glossy cornea surface producing realistic studio catchlights.

---

## 3. Calibrated Binocular Convergence Math

At fixation distance $D = 0.35\,\text{m}$ (35 cm forward from eye midpoint):
* Gaze target point:
  $$X_T(h) = 0.35 \cdot \tan(h \cdot 25^\circ), \quad Z_T(v) = 0.35 \cdot \tan(v \cdot 20^\circ), \quad Y_T = -0.35\,\text{m}$$
* Gaze direction vectors:
  $$\vec{V}_L = P_T - C_L, \quad \vec{V}_R = P_T - C_R$$
* Center rest inward vergence angle:
  $$\alpha = \arctan\left(\frac{0.032}{0.35}\right) \approx 5.23^\circ \text{ inward}$$

---

## 4. Virtual Camera & Calibration Matrix

* **Position:** Fixed at $(0.0, -0.40, 0.0)\,\text{m}$ (40 cm forward from eye midpoint).
* **Sensor & Lens:** $f = 50.0\,\text{mm}$, sensor size $36.0 \times 36.0\,\text{mm}$.
* **Resolution:** $1024 \times 1024$ pixels, 8-bit RGB PNG.
* **Intrinsic Matrix ($K$):**
  $$K = \begin{bmatrix} 1422.2222 & 0.0 & 512.0 \\ 0.0 & 1422.2222 & 512.0 \\ 0.0 & 0.0 & 1.0 \end{bmatrix}$$

---

## 5. Five-Direction Empirical Validation

| Direction | Input $(h, v)$ | Left Eye $(X, Y)$ | Right Eye $(X, Y)$ | $\Delta X_L$ | $\Delta X_R$ | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline** | $(0.0, 0.0)$ | $(625.28, 512.00)$ | $(398.72, 512.00)$ | $0.00$ | $0.00$ | **PASS** |
| **Left** | $(-1.0, 0.0)$ | $(607.50, 512.00)$ | $(379.52, 512.00)$ | $-17.78\,\text{px}$ | $-19.20\,\text{px}$ | **PASS** |
| **Right** | $(+1.0, 0.0)$ | $(644.48, 512.00)$ | $(416.50, 512.00)$ | $+19.20\,\text{px}$ | $+17.78\,\text{px}$ | **PASS** |
| **Up** | $(0.0, +1.0)$ | $(625.31, 497.04)$ | $(398.69, 497.04)$ | $\Delta Y = -14.96\,\text{px}$ | $\Delta Y = -14.96\,\text{px}$ | **PASS** |
| **Down** | $(0.0, -1.0)$ | $(625.31, 526.96)$ | $(398.69, 526.96)$ | $\Delta Y = +14.96\,\text{px}$ | $\Delta Y = +14.96\,\text{px}$ | **PASS** |
| **Reset** | $(0.0, 0.0)$ | $(625.28, 512.00)$ | $(398.72, 512.00)$ | $0.00\,\text{px}$ | $0.00\,\text{px}$ | **PASS** |

*Zero drift detected on repeated sequence resets.*

---

## 6. Ten Clockwise Gaze Samples

Circular trajectory formulation:
$$\theta_k = \frac{2\pi k}{10}, \quad h = \sin(\theta_k), \quad v = \cos(\theta_k) \quad \text{for } k = 0, \dots, 9$$

* Frame 0 starts at top ($h=0.0, v=+1.0$).
* Renders: `frame_00.png` through `frame_09.png` ($1024 \times 1024$).
* Ground-truth metadata: `metadata.json` (actual 3D rotations, pupil pixel projections, camera matrix).
* Overview: Clean 5 × 2 annotated `contact_sheet.png`.

---

## 7. Python SDK & Localhost Dashboard

* **Python SDK (`wrapper/eyes.py`):**
  * Object-oriented controller (`Eyes.move(h, v)`, `Eyes.reset()`, `Eyes.render()`).
  * Distributable Wheel package ready for pip installation.
* **Interactive Localhost Dashboard (`http://localhost:8000`):**
  * 2D gaze joystick with live binocular convergence calculation.
  * Real-time 3D WebGL (Three.js) eyeball rotation viewport.
  * Interactive 10-frame animation player with ground-truth pupil reticles.

---

## 8. Conclusion & Submission Deliverables

* ✅ **Complete Source Code & Rigged Scene:** `scene.blend`
* ✅ **Python SDK & Wheel:** `sdk/` and `wrapper/`
* ✅ **Ground-Truth Metadata:** `metadata.json`
* ✅ **10 Renders & Contact Sheet:** `renders/` + `contact_sheet.png`
* ✅ **Automated Test Suite:** 9/9 tests passing (0.087s)
* ✅ **Video & Presentation:** `video/` + `presentation/`
* ✅ **AI Disclosure:** `AI_DISCLOSURE.md` compliant
