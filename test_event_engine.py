import pytest
import yaml
from event_engine import EventEngine

config_path = "../data/config_tests.yaml"

def test_event_opens_correctly():
    engine = EventEngine(config_path)
    
    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection gap tolerance acceptable
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Min duration accomplished
    events = engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.95, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    assert len(events) == 1
    assert events[0]["type"] == "opened"
    assert events[0]["peak_confidence"] == 0.95
    assert events[0]["detection_count"] == 3



def test_event_not_opens_correctly():
    engine = EventEngine(config_path)
    
    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection gap smaller than tolerance acceptable
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Third detection gap greater than tolerance  
    events = engine.process({"timestamp_ms": 2100, "camera_id": "c1", "class": "person", "confidence": 0.95, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    assert len(events) == 0



def test_ignore_wrong_class():
    engine = EventEngine(config_path)

    # Class not of interest
    events = engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "dog", "confidence": 1.0, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    assert len(events) == 0
    assert ("c1", "dog") not in engine.cameras



def test_ignore_wrong_confidence():
    engine = EventEngine(config_path)

    # Detection below confidence threshold
    events = engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.5, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    assert len(events) == 0
    assert ("c1", "person") not in engine.cameras



def test_exact_confidence():
    engine = EventEngine(config_path)

    # Detection exactly on confidence threshold
    events = engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.6, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    assert len(events) == 0
    assert ("c1", "person") in engine.cameras



def test_low_confidence_does_not_reset_count():
    engine = EventEngine(config_path)

    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection below confidence threshold 
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.5, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    state = engine.cameras[("c1", "person")]
    assert state["last_time"] == 1000
    assert state["detection_count"] == 1



def test_peak_conf_count():
    engine = EventEngine(config_path)

    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection below confidence threshold 
    engine.process({"timestamp_ms": 1300, "camera_id": "c1", "class": "person", "confidence": 0.8, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    # Third detection below confidence threshold 
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.95, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Third detection below confidence threshold 
    engine.process({"timestamp_ms": 1800, "camera_id": "c1", "class": "person", "confidence": 0.65, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    

    state = engine.cameras[("c1", "person")]
    assert state["peak_confidence"] == 0.95
    assert state["detection_count"] == 4



def test_close_event_after_big_gap():
    engine = EventEngine(config_path)
    
    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection gap tolerance acceptable
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Min duration accomplished
    engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.95, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Gap exceeded
    events = engine.process({"timestamp_ms": 2600, "camera_id": "c1", "class": "person", "confidence": 0.97, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    assert len(events) == 1
    assert events[0]["type"] == "closed"
    assert events[0]["peak_confidence"] == 0.95
    assert events[0]["detection_count"] == 3



def test_cooldown():
    engine = EventEngine(config_path)
    
    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection gap tolerance acceptable
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Min duration accomplished
    engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.95, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    state = engine.cameras[("c1", "person")]
    assert state["active"] == True
    assert state["initial_time"] == 1000
    assert state["last_time"] == 2000
    assert state["peak_confidence"] == 0.95
    assert state["detection_count"] == 3

    # Gap exceeded event closed
    engine.process({"timestamp_ms": 2600, "camera_id": "c1", "class": "person", "confidence": 0.97, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    # Detection during cooldown 1 ms before cooldown finishes
    engine.process({"timestamp_ms": 3999, "camera_id": "c1", "class": "person", "confidence": 0.92, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    state = engine.cameras[("c1", "person")]
    assert state["active"] == False
    assert state["initial_time"] == None
    assert state["last_time"] == 0
    assert state["peak_confidence"] == 0.0
    assert state["detection_count"] == 0

    # Detection during cooldown
    engine.process({"timestamp_ms": 4000, "camera_id": "c1", "class": "person", "confidence": 0.92, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    state = engine.cameras[("c1", "person")]
    assert state["active"] == False
    assert state["initial_time"] == 4000
    assert state["last_time"] == 4000
    assert state["peak_confidence"] == 0.92
    assert state["detection_count"] == 1



def test_multiclass():
    engine = EventEngine(config_path)

    # First detection class person
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # First detection class car
    engine.process({"timestamp_ms": 1100, "camera_id": "c1", "class": "car", "confidence": 0.8, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection class person
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Third detection class person 
    events = engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    assert len(events) == 1
    assert events[0]["camera_id"] == "c1"
    assert events[0]["class"] == "person"
    assert events[0]["type"] == "opened"

    # Second detection class car
    events = engine.process({"timestamp_ms": 1600, "camera_id": "c1", "class": "car", "confidence": 0.8, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    # Third detection class car 
    events = engine.process({"timestamp_ms": 2100, "camera_id": "c1", "class": "car", "confidence": 0.85, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    assert len(events) == 1
    assert events[0]["camera_id"] == "c1"
    assert events[0]["class"] == "car"
    assert events[0]["type"] == "opened"


def test_multicam():
    engine = EventEngine(config_path)

    # First detection class person
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # First detection class car
    engine.process({"timestamp_ms": 1100, "camera_id": "c2", "class": "person", "confidence": 0.8, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection class person
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Third detection class person 
    events = engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    assert len(events) == 1
    assert events[0]["camera_id"] == "c1"
    assert events[0]["class"] == "person"
    assert events[0]["type"] == "opened"

    # Second detection class car
    events = engine.process({"timestamp_ms": 1600, "camera_id": "c2", "class": "person", "confidence": 0.8, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    # Third detection class car 
    events = engine.process({"timestamp_ms": 2100, "camera_id": "c2", "class": "person", "confidence": 0.85, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    assert len(events) == 1
    assert events[0]["camera_id"] == "c2"
    assert events[0]["class"] == "person"
    assert events[0]["type"] == "opened"



def test_flush():
    engine = EventEngine(config_path)

    # Cam 1 person opened
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.8, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    # Cam 1 person opened
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "car", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "car", "confidence": 0.8, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "car", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    # Cam 2 person opened
    engine.process({"timestamp_ms": 1000, "camera_id": "c2", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    engine.process({"timestamp_ms": 1500, "camera_id": "c2", "class": "person", "confidence": 0.8, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    engine.process({"timestamp_ms": 2000, "camera_id": "c2", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    events = engine.flush(3000)

    assert len(events) == 3
    assert events[0]["camera_id"] == "c1"
    assert events[0]["class"] == "person"
    assert events[0]["type"] == "closed"
    assert events[1]["camera_id"] == "c1"
    assert events[1]["class"] == "car"
    assert events[1]["type"] == "closed"
    assert events[2]["camera_id"] == "c2"
    assert events[2]["class"] == "person"
    assert events[2]["type"] == "closed"


def test_out_of_order():
    engine = EventEngine(config_path)
    
    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection gap tolerance acceptable
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Out of order
    engine.process({"timestamp_ms": 1300, "camera_id": "c1", "class": "person", "confidence": 0.95, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Min duration
    engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.91, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    # Out of order
    engine.process({"timestamp_ms": 1900, "camera_id": "c1", "class": "person", "confidence": 0.98, "x1": 0, "y1": 0, "x2": 10, "y2": 10})


    state = engine.cameras[("c1", "person")]

    assert state["active"] == True
    assert state["initial_time"] == 1000
    assert state["last_time"] == 2000
    assert state["peak_confidence"] == 0.98
    assert state["detection_count"] == 5

def test_duplicates():
    engine = EventEngine(config_path)
    
    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection gap tolerance acceptable
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Duplicate
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.95, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Min duration
    engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    state = engine.cameras[("c1", "person")]

    assert state["active"] == True
    assert state["initial_time"] == 1000
    assert state["last_time"] == 2000
    assert state["peak_confidence"] == 0.95
    assert state["detection_count"] == 4

def test_bounding_box():
    engine = EventEngine(config_path)

    # First detection
    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Second detection gap tolerance acceptable
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Duplicate
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.95, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    
    # Min duration
    engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})

    state = engine.cameras[("c1", "person")]

    assert state["active"] == True
    assert state["initial_time"] == 1000
    assert state["last_time"] == 2000
    assert state["peak_confidence"] == 0.95
    assert state["detection_count"] == 4

def test_sustain():
    engine = EventEngine(config_path)

    engine.process({"timestamp_ms": 1000, "camera_id": "c1", "class": "person", "confidence": 0.9, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    engine.process({"timestamp_ms": 1500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    events = engine.process({"timestamp_ms": 2000, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    assert len(events) == 1
    assert events[0]["type"] == "opened"
    events = engine.process({"timestamp_ms": 2500, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    assert len(events) == 0
    events = engine.process({"timestamp_ms": 3000, "camera_id": "c1", "class": "person", "confidence": 0.93, "x1": 0, "y1": 0, "x2": 10, "y2": 10})
    assert len(events) == 1
    assert events[0]["type"] == "sustained"
    