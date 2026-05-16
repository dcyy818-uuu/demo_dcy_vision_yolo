from pathlib import Path
import shutil

from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
PT_MODEL = ROOT / "runs" / "detect" / "rm_armor_yolo11s" / "weights" / "best.pt"
ROOT_ENGINE_MODEL = ROOT / "rm_armor_yolo11s_best.engine"


def main():
    model = YOLO(str(PT_MODEL))

    engine_path = Path(
        model.export(
            format="engine",
            imgsz=640,
            device=0,
            dynamic=False,
            half=False,
        )
    )

    shutil.copy2(engine_path, ROOT_ENGINE_MODEL)

    print(f"TensorRT engine exported to: {engine_path}")
    print(f"Copied to: {ROOT_ENGINE_MODEL}")


if __name__ == "__main__":
    main()
