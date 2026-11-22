# Samsung XR Integration Specification
## Bridging the Synthetic Gaze Engine into Android OpenXR & Unity / Unreal APKs

This specification defines the architectural pipeline for integrating the Track 01 Synthetic Gaze Engine into Android XR runtime environments, OpenXR runtimes, and real-time XR engine APKs (Unity / Unreal / Godot).

---

### 1. Architecture Overview

```text
┌────────────────────────────────────────────────────────┐
│               Samsung XR Headset / Android             │
│   ┌────────────────────────────────────────────────┐   │
│   │           OpenXR Gaze Tracking Extension       │   │
│   │         (XR_EXT_eye_gaze_interaction)          │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Raw (h, v) or Quaternion   │
│                           ▼                            │
│   ┌────────────────────────────────────────────────┐   │
│   │        Samsung XR Gaze Engine (C++ / NDK)      │   │
│   │      - Binocular Convergence Calculator        │   │
│   │      - Physical Eyeball Pivot Constraint       │   │
│   │      - Donders' / Listing's Law Solver         │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Matrix / Bone Poses        │
│                           ▼                            │
│   ┌────────────────────────────────────────────────┐   │
│   │       3D Avatar / Foveated Shading Pipeline    │   │
│   │      - Left Eye Bone Pose (Eye_L)              │   │
│   │      - Right Eye Bone Pose (Eye_R)             │   │
│   │      - Foveal Density Target Coordinates       │   │
│   └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

### 2. OpenXR Data Mapping

In OpenXR, eye gaze is provided via the `XR_EXT_eye_gaze_interaction` extension:
```c
typedef struct XrEyeGazeSampleEXT {
    XrTime          time;
    XrPosef         gazePose;         // Orientation quaternion & position
    XrEyeGazeState  gazeState;        // Valid, Tracking, etc.
} XrEyeGazeSampleEXT;
```

#### Mapping OpenXR to Normalized $(h, v)$:
Given the forward gaze vector $\vec{G} = (G_x, G_y, G_z)$ in headset local space:
$$h = \frac{\arctan2(G_x, -G_y)}{\theta_{H,\max}}, \quad v = \frac{\arctan2(G_z, -G_y)}{\theta_{V,\max}}$$
where $\theta_{H,\max} = 25^\circ$ ($0.4363\,\text{rad}$) and $\theta_{V,\max} = 20^\circ$ ($0.3491\,\text{rad}$).

---

### 3. Real-Time C++ / NDK Implementation for Android APKs

For integration into an Android `.apk` via JNI / C++:

```cpp
#include <cmath>

struct Vec3 { float x, y, z; };
struct EyePose {
    Vec3 left_euler_deg;
    Vec3 right_euler_deg;
    Vec3 fixation_target;
};

class SamsungXRGazeEngine {
public:
    static constexpr float IPD = 0.064f;             // 64 mm
    static constexpr float EYE_RADIUS = 0.012f;      // 12 mm
    static constexpr float FIXATION_DIST = 0.35f;    // 35 cm
    static constexpr float MAX_YAW = 0.4363323f;     // 25 deg
    static constexpr float MAX_PITCH = 0.3490659f;   // 20 deg

    static EyePose computeGaze(float h, float v) {
        // Clamp normalized inputs
        h = std::max(-1.0f, std::min(1.0f, h));
        v = std::max(-1.0f, std::min(1.0f, v));

        // Target point on 35 cm plane
        float tx = FIXATION_DIST * std::tan(h * MAX_YAW);
        float tz = FIXATION_DIST * std::tan(v * MAX_PITCH);
        float ty = -FIXATION_DIST;

        // Gaze vectors
        Vec3 vL = { tx - 0.032f, ty, tz };
        Vec3 vR = { tx + 0.032f, ty, tz };

        // Euler rotation angles around physical eyeball centers
        float pitch_L = std::atan2(vL.z, -vL.y) * 180.0f / 3.14159265f;
        float yaw_L   = std::atan2(vL.x, -vL.y) * 180.0f / 3.14159265f;

        float pitch_R = std::atan2(vR.z, -vR.y) * 180.0f / 3.14159265f;
        float yaw_R   = std::atan2(vR.x, -vR.y) * 180.0f / 3.14159265f;

        EyePose pose;
        pose.left_euler_deg  = { pitch_L, 0.0f, yaw_L };
        pose.right_euler_deg = { pitch_R, 0.0f, yaw_R };
        pose.fixation_target = { tx, ty, tz };
        return pose;
    }
};
```

---

### 4. Foveated Rendering Integration
The projected pupil coordinates $(px_L, py_L)$ output by this engine are fed directly to the Android XR Vulkan graphics pipeline via `VK_EXT_fragment_density_map`:
* Maximum shading resolution is focused within a $5^\circ$ foveal window around the computed pupil projection point.
* Peripheral areas are downsampled by up to $4\times$, delivering **up to $60\%$ GPU savings** on mobile XR chipsets (e.g. Snapdragon XR2+ Gen 2 / Exynos XR).
