import yaml

class EventEngine:
    def __init__(self, config_path: str):
        
        # Open yaml file and load contents
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
        
        self.min_confidence = config_data["min_confidence"]
        self.min_duration_ms = config_data["min_duration_ms"]
        self.gap_tolerance_ms = config_data["gap_tolerance_ms"]
        self.cooldown_ms = config_data["cooldown_ms"]
        self.classes_of_interest = []
        for classification in config_data["classes_of_interest"]:
            self.classes_of_interest.append(classification)

        self.cameras = {}

    def process(self, detection: dict) -> list[dict]:

        timestamp_ms = detection["timestamp_ms"]
        camera_id = detection["camera_id"]
        classification = detection["class"]
        confidence = detection["confidence"] 
        
        events = []

        # Verify class and confidence
        if classification not in self.classes_of_interest or confidence < self.min_confidence:
            return events
        
        key = (camera_id, classification)

        # Create state instance
        if key not in self.cameras:
            self.cameras[key] = {
                "active": False,
                "camera_id": camera_id,
                "class": classification,
                "initial_time": None,
                "last_time": 0,
                "cooldown": 0, 
                "peak_confidence": 0.0,
                "detection_count": 0
            }

        state = self.cameras[key]

        # Wait until cooldown finishes
        if timestamp_ms < state["cooldown"]:
            return events
        

        gap = timestamp_ms-state["last_time"]

        # ---------NOT ACTIVE
        if not state["active"]:

            # -----SET INITIAL TIME
            if state["initial_time"] is None:
                self.reset_state(state, detection)
                return events
            
            # ----- SMALL GAP
            if abs(gap) <= self.gap_tolerance_ms:
                self.update_state(state, detection)

                # ----- MIN DURATION ACCOMPLISHED
                if (timestamp_ms-state["initial_time"]) >= self.min_duration_ms:
                    state["active"] = True
                    events.append({
                        "type": "opened",
                        "camera_id": camera_id,
                        "class": classification,
                        "opened_at_ms": state["initial_time"],
                        "closed_at_ms": None,
                        "peak_confidence": state["peak_confidence"], 
                        "detection_count": state["detection_count"],
                    })

            # ------ BIG GAP
            else:
                self.reset_state(state, detection)

        # ---------ACTIVE
        else:

            if gap <= self.gap_tolerance_ms:
                self.update_state(state, detection)

            else:
                events.append({
                        "type": "closed",
                        "camera_id": state["camera_id"],
                        "class": state["class"],
                        "opened_at_ms": state["initial_time"],
                        "closed_at_ms": state["last_time"],
                        "peak_confidence": state["peak_confidence"], 
                        "detection_count": state["detection_count"],
                    })
                
                
                state["cooldown"] = state["last_time"] + self.cooldown_ms

                state["active"] = False
                state["initial_time"] = None
                state["last_time"] = 0
                state["peak_confidence"] = 0.0
                state["detection_count"] = 0

        return events


    def flush(self, current_time_ms: int) -> list[dict]:

        events = []

        for key in self.cameras:
            state = self.cameras[key]
            if state["active"]:
                gap = current_time_ms-state["last_time"]
                if gap > self.gap_tolerance_ms:
                    events.append({
                        "type": "closed",
                        "camera_id": state["camera_id"],
                        "class": state["class"],
                        "opened_at_ms": state["initial_time"],
                        "closed_at_ms": state["last_time"],
                        "peak_confidence": state["peak_confidence"], 
                        "detection_count": state["detection_count"],
                    })
                    
                    state["cooldown"] = state["last_time"] + self.cooldown_ms

                    state["active"] = False
                    state["initial_time"] = None
                    state["last_time"] = 0
                    state["peak_confidence"] = 0.0
                    state["detection_count"] = 0

        return events
    
    def update_state(self, state, detection):
        state["last_time"] = detection["timestamp_ms"]
        state["peak_confidence"] = max(state["peak_confidence"], detection["confidence"])
        state["detection_count"] += 1

    def reset_state(self, state, detection):
        state["initial_time"] = detection["timestamp_ms"]
        state["last_time"] = detection["timestamp_ms"]
        state["peak_confidence"] = detection["confidence"]
        state["detection_count"] = 1