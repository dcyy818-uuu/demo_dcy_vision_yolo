from pathlib import Path

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
PT_MODEL = ROOT / "runs" / "detect" / "rm_armor_yolo11s" / "weights" / "best.pt"


def main():
    model = YOLO(str(PT_MODEL))

    onnx_path = model.export(
        format="onnx",
        imgsz=640,
        opset=12,
        simplify=True,
        dynamic=False,
    )

    print(f"ONNX exported to: {onnx_path}")


if __name__ == "__main__":
    main()