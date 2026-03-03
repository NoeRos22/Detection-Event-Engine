import yaml

class EventEngine:
    def __init__(self, config_path: str):
        
        # Open yaml file and load contents
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
        
        self.sustain_ms = config_data["sustain_ms"]
        self.out_of_order_ms = config_data["out_of_order_ms"]
        self.min_confidence = config_data["min_confidence"]
        self.min_duration_ms = config_data["min_duration_ms"]
        self.gap_tolerance_ms = config_data["gap_tolerance_ms"]
        self.cooldown_ms = config_data["cooldown_ms"]
        self.classes_of_interest = config_data["classes_of_interest"]
        self.zones = config_data["zones"]

        print(self.zones)

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
        
        x_centroid = (detection["x1"]+detection["x2"])/2
        y_centroid = (detection["y1"]+detection["y2"])/2

        inside = (self.zones[0] <= x_centroid <= self.zones[2]) and (self.zones[1] <= y_centroid <= self.zones[3])
        
        if not inside:
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
                "last_sustain": 0,
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
            if (gap <= self.gap_tolerance_ms) and gap >= (-self.out_of_order_ms):
                self.update_state(state, detection)

                # ----- MIN DURATION ACCOMPLISHED
                if (timestamp_ms-state["initial_time"]) >= self.min_duration_ms:
                    state["active"] = True
                    state["last_sustain"] = timestamp_ms
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

            if (gap <= self.gap_tolerance_ms) and gap >= (-self.out_of_order_ms):
                if (timestamp_ms - state["last_sustain"]) >= self.sustain_ms:
                    events.append({
                        "type": "sustained",
                        "camera_id": camera_id,
                        "class": classification,
                        "opened_at_ms": state["initial_time"],
                        "closed_at_ms": None,
                        "peak_confidence": state["peak_confidence"], 
                        "detection_count": state["detection_count"],
                    })
                    state["last_sustain"] = timestamp_ms
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
                
                self.clear_state(state)

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
                    
                    self.clear_state(state)

        return events
    
    def update_state(self, state, detection):
        state["last_time"] = max(state["last_time"], detection["timestamp_ms"])
        state["peak_confidence"] = max(state["peak_confidence"], detection["confidence"])
        state["detection_count"] += 1

    def reset_state(self, state, detection):
        state["initial_time"] = detection["timestamp_ms"]
        state["last_time"] = detection["timestamp_ms"]
        state["last_sustain"] = detection["timestamp_ms"]
        state["peak_confidence"] = detection["confidence"]
        state["detection_count"] = 1

    def clear_state(self, state):
        state["cooldown"] = state["last_time"] + self.cooldown_ms
        state["active"] = False
        state["initial_time"] = None
        state["last_time"] = 0
        state["peak_confidence"] = 0.0
        state["detection_count"] = 0
