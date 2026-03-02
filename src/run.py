from event_engine import EventEngine
import csv

def main():
    engine = EventEngine("../covenant/data/config.yaml")

    with open("../covenant/data/detections.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile) 
        for row in reader:
            detection = {
                "timestamp_ms": int(row["timestamp_ms"]),
                "camera_id": row["camera_id"],
                "class": row["class"],
                "confidence": float(row["confidence"]),
                "x1": int(row["x1"]),
                "y1": int(row["y1"]),
                "x2": int(row["x2"]),
                "y2": int(row["y2"]),
            }

            print(engine.process(detection))


if __name__ == "__main__":
    main()