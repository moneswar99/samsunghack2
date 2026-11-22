# Samsung XR Hackathon 2026 – Track 01
## Video Demonstration Script & Storyboard

**Project:** Synthetic Eye Movement & Virtual Camera Rendering
**Track:** Track 01
**Target Duration:** 3 Minutes
**Video Files:**
- `video/demo_gaze_sequence.webp` (High-definition 24-bit RGB animated demonstration)
- `video/demo_gaze_sequence.gif` (Universal animation demonstration)
- Interactive Dashboard demonstration at `http://localhost:8000`

---

### Storyboard & Narration Outline

#### Segment 1: Introduction & Problem Context (0:00 – 0:35)
* **Visual Cue:** Title card and high-resolution 3D face model in Blender with studio lighting. Camera zoomed to eye level.
* **Speaker Script:**
  > "Hello evaluators! Welcome to our submission for the Samsung R&D Institute India XR Hackathon 2026, Track 01: Synthetic Eye Movement and Virtual Camera Rendering.
  > In next-generation XR headsets, high-precision gaze tracking is vital for foveated rendering, spatial avatar interaction, and near-eye optics calibration.
  > However, training computer vision gaze estimators requires millimeter-accurate ground-truth data with authentic 3D eyeball rotation and realistic binocular vergence.
  > Today, we present a complete, mathematically calibrated, and fully automated solution built in Blender and Python."

---

#### Segment 2: Anatomy, Rigging & Physical 3D Eyeball Rotation (0:35 – 1:15)
* **Visual Cue:** Transition into Blender viewport showing the Armature `EyeRig` with bones `Eye_L` and `Eye_R` at physical eyeball centers.
* **Speaker Script:**
  > "Our system features an anatomically proportioned human head model with realistic facial contours and orbital sockets.
  > Crucially, we strictly avoid the artificial 2D pupil translation shortcuts common in basic simulations.
  > Instead, we modeled two separate 24-millimeter spherical eyeballs with photorealistic hazel irises, dark limbal rings, deep black pupils, and glossy refractive corneas.
  > Both eyeballs are skinned to dedicated bones—Eye_L and Eye_R—whose rotation pivots are precisely pinned to the physical eyeball centers at plus and minus 32 millimeters from the eye midpoint, matching standard human interpupillary distance."

---

#### Segment 3: Calibrated Binocular Convergence & Camera Calibration (1:15 – 1:55)
* **Visual Cue:** Show 3D target ray lines converging on the 35 cm fixation plane. Display the camera calibration matrix $K$ and 40 cm fixed camera position.
* **Speaker Script:**
  > "To satisfy official challenge specifications, we mathematically formulated human binocular convergence.
  > When a human fixates on an object at near distance, both eyes converge inward. Our fixation target is calibrated at exactly 35 centimeters forward from the eye midpoint, producing a natural 5.23-degree inward vergence angle at rest.
  > When horizontal and vertical gaze inputs shift, both eyes rotate synchronously toward the target point while remaining constrained around their sphere centers.
  > Our virtual camera remains fixed at exactly 40 centimeters forward from the eye midpoint with a 50-millimeter lens on a 36-millimeter sensor, generating 1024 by 1024 pixel renders with an exact intrinsic calibration matrix."

---

#### Segment 4: Ten Clockwise Gaze Renders & Ground Truth (1:55 – 2:30)
* **Visual Cue:** Play the 10-frame clockwise circular gaze sequence (`frame_00.png` through `frame_09.png`) with pupil crosshair overlays, and show the $5 \times 2$ contact sheet.
* **Speaker Script:**
  > "We executed the official 10-sample clockwise circular gaze trajectory: theta equals 2 pi k over 10, with h equals sine theta and v equals cosine theta.
  > Frame zero begins at the top, rotating clockwise across all quadrants.
  > For every frame, our pipeline automatically captures the exact 3D world Euler rotations, projects the 2D pupil centers down to sub-pixel coordinates, and exports ground-truth metadata in metadata.json.
  > We also compiled all 10 renders into this clean 5-by-2 annotated contact sheet."

---

#### Segment 5: Live Interactive Dashboard, Testing & Conclusion (2:30 – 3:00)
* **Visual Cue:** Screen capture of the interactive localhost web dashboard (`http://localhost:8000`), moving the 2D gaze joystick, viewing the 3D WebGL simulator, and highlighting the 9/9 passing tests.
* **Speaker Script:**
  > "Beyond the core requirements, we built an interactive web dashboard running on localhost:8000 with a real-time 2D gaze touchpad, a live 3D WebGL Three.js simulator, and automated test reporting.
  > Our test suite validates scene integrity, bone pivots, camera calibration, five-direction pupil displacements, and zero-drift reset—passing all 9 tests in under 0.1 seconds.
  > Thank you for your time, and we look forward to powering the future of Samsung XR eye tracking!"
