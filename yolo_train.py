from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent
DATA_YAML = ROOT / "data.yaml"

def main():
    model = YOLO("yolo11s.pt")

    model.train(
        data=str(DATA_YAML),
        epochs=200,
        imgsz=640,
        batch=16,
        device=0,
        workers=0,
        project=str(ROOT / "runs" / "detect"),
        name="rm_armor_yolo11s",
        pretrained=True,
        patience=50,
        seed=42,
        close_mosaic=10,
    )


if __name__ == "__main__":
    main()