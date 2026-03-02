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

        self.cameras_state = {}

        self.count = 1

    def process(self, detection: dict) -> list[dict]:
        self.count += 1
        print(self.count)

        timestamp_ms = detection["timestamp_ms"]
        camera_id = detection["camera_id"]
        classification = detection["class"]
        confidence = detection["confidence"] 
        
        events = []

        # Verify class and confidence
        if classification not in self.classes_of_interest or confidence < self.min_confidence:
            return events

        # Create state instance
        if camera_id not in self.cameras_state:
            self.cameras_state[camera_id] = {
                "active": False,
                "initial_time": None,
                "last_time": 0,
                "cooldown": 0, 
                "peak_confidence": 0,
                "detection_count": 0
            }

        state = self.cameras_state[camera_id]

        # Wait until cooldown finishes
        if timestamp_ms < state["cooldown"]:
            print("cooling")
            return events
        

        gap = timestamp_ms-state["last_time"]

        # ---------NOT ACTIVE
        if not state["active"]:

            # -----SET INITIAL TIME
            if state["initial_time"] is None:
                state["initial_time"] = timestamp_ms
                state["last_time"] = timestamp_ms
                print("initial")
                return events
            
            

            
            print("GAP", state["last_time"]-timestamp_ms)
            # ----- SMALL GAP
            if abs(gap) < self.gap_tolerance_ms:
                state["last_time"] = timestamp_ms
                state["peak_confidence"] = max(state["peak_confidence"], confidence)
                state["detection_count"] += 1


                # ----- MIN DURATION ACCOMPLISHED
                print("DURATION", timestamp_ms-state["initial_time"])
                if (timestamp_ms-state["initial_time"]) > self.min_duration_ms:
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
                state["initial_time"] = timestamp_ms
                state["last_time"] = timestamp_ms
                state["peak_confidence"] = 0
                state["detection_count"] = 0

        # ---------ACTIVE
        else:

            print("GAP", state["last_time"]-timestamp_ms)

            if gap < self.gap_tolerance_ms:
                state["last_time"] = timestamp_ms
                state["peak_confidence"] = max(state["peak_confidence"], confidence)
                state["detection_count"] += 1

            else:
                events.append({
                        "type": "closed",
                        "camera_id": camera_id,
                        "class": classification,
                        "opened_at_ms": state["initial_time"],
                        "closed_at_ms": state["last_time"],
                        "peak_confidence": state["peak_confidence"], 
                        "detection_count": state["detection_count"],
                    })
                
                state["initial_time"] = None
                state["cooldown"] = state["last_time"] + self.cooldown_ms
                state["last_time"] = timestamp_ms # debería de ser 0??
                state["active"] = False
                state["peak_confidence"] = 0
                state["detection_count"] = 0




        return events

        
        

        """
        Feed one detection record at a time (Done).
        Returns a list of zero or more event dicts triggered by this detection.
        Usually returns an empty list.

        detection format:
        {
            "timestamp_ms": int,
            "camera_id": str,
            "class": str,
            "confidence": float,
            "x1": int, "y1": int, "x2": int, "y2": int
        }
        """

    def flush(self, current_time_ms: int) -> list[dict]:
        """
        Call this after the last detection (or periodically in production).
        Closes any open events that have timed out.
        Returns any newly closed events.
        """
        ...