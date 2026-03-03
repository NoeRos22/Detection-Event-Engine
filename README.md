# Event Engine

### What state does your engine track per camera?

- "active": bool                     // True if min_duration_ms has been met and event is currently open.
- "camera_id": str                   // Identifier for the camera
- "class": str                       // Target class
- "initial_time": int                // Timestamp of the first detection
- "last_time": int                   // Timestamp of the last detection
- "last_sustain": int                // Heartbeat timestamp
- "cooldown": int                    // Expiration timestamp where the camera can create events again
- "peak_confidence": float           // Maximum confidence score
- "detection_count": int             // Number of valid detections in an event

### What would break in a real deployment that your tests do not cover?

- The dictionary accumulates keys for every unique camera/class pair. In a long-running deployment with high traffic, this could lead to high memory costs.
- When an event closes it applies a cooldown to especific pair (id, class), however it allows to the same camera to detect other classes that belong to the classes of interest.
- The engine tracks classes, not individuals. If two different instances of the same class appear simultaneously, the engine cannot distinguish between them.
- It cannot handle duplicate detections, it will increase the detection_count either way.
- Microcontrollers have an inner clock that resets, the code is not ready to receive such a negative gap.
- It is not thread safety, in a real deployment, flush may be activated by another thread, meaning that process and flush can access to the dictionary at the same time, this could be solved with a mutex for example.
