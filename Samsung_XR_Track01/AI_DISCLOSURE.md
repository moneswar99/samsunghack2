# Samsung R&D Institute India XR Hackathon 2026
## Artificial Intelligence (AI) Disclosure Statement

**Project Title:** Synthetic Eye Movement & Virtual Camera Rendering  
**Track:** Track 01  
**Team / Participant:** DSS Srikar / Track 01 Participant  
**Date:** November 22, 2026  

---

### 1. Disclosure of Generative AI Tools Used
In compliance with the Samsung XR Hackathon 2026 submission guidelines, the participants hereby disclose the use of Artificial Intelligence (AI) assistance during the conceptualization, development, and documentation of this project.

* **Primary AI System:** Antigravity (Powered by Google DeepMind Gemini models)
* **Usage Modalities:**
  * Architectural design & mathematical derivation assistance
  * Code scaffolding & Blender Python (`bpy`) API integration
  * Automated unit test script development
  * Documentation structuring and Markdown authoring

---

### 2. Extent and Nature of AI Assistance

| Project Component | Extent of AI Assistance | Description of Work |
| :--- | :---: | :--- |
| **Mathematical Formulation** | Assisted | Verification of binocular convergence trigonometry on a $35\,\text{cm}$ fixation plane, Donders' / Listing's law alignment, and pinhole camera intrinsic projection matrix derivation. |
| **Python API (`wrapper/eyes.py`)** | Assisted | Implementation of normalized input clamping, deterministic zero-drift `reset()`, bone rotation matrix assignment, and 2D pupil sub-pixel projection via Blender's dependency graph. |
| **Blender 3D Modeling & Shaders** | Assisted | Procedural head mesh cage generation, orbital socket indentation math, dual $24\,\text{mm}$ eyeball mesh creation, Armature rigging, and procedural material shader nodes. |
| **Automated Testing Suite** | Assisted | Development of the 9-point unit test framework (`tests/test_eye_movement.py`) validating physical bone pivots, camera distance, five-direction displacement vectors, and JSON schema. |
| **Web Dashboard** | Assisted | Building the localhost interactive dashboard (`dashboard/index.html` & `server.py`) with Three.js 3D WebGL simulator and 2D gaze joystick. |
| **Presentation & Documentation** | Assisted | Drafting presentation slides (`presentation/`), video demonstration script (`video/`), and comprehensive `README.md`. |

---

### 3. Human Authorship, Ownership & Verification
While generative AI was utilized as an engineering accelerator:
1. **Human Direction & Evaluation:** All project requirements, parameter specifications ($35\,\text{cm}$ fixation, $40\,\text{cm}$ camera distance, $1024 \times 1024$ resolution, 10 clockwise frames), and architectural design decisions were directed and validated by the human team.
2. **Local Hardware Execution:** All code, Blender scene generation scripts, rendering pipelines, and test suites were executed directly on the local physical machine.
3. **Rigorous Empirical Verification:** No simulated or fabricated data was accepted. Every rendered frame, projected pupil coordinate, and rotation angle was computed by Blender's physics/rendering engine and verified through automated test suites (9/9 passing tests).
4. **Originality & Intellectual Property:** The project does not infringe on third-party proprietary assets, paid cloud APIs, or copyrighted materials. All code is original, modular, and open-source under the Apache 2.0 license.

---

### 4. Affirmation
The team affirms that the technical understanding, mathematical calibration, and software architecture presented in this submission are fully understood and defendable by the team during technical evaluations and jury interviews.
