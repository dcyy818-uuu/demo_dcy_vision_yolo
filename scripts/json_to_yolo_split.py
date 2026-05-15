import json
import random
import shutil
from pathlib import Path

ROOT = Path(r"D:\RM_YOLO")
SRC = ROOT / "label_work"
OUT = ROOT / "dataset"

VAL_RATIO = 0.2
RANDOM_SEED = 42

IMG_EXTS = [".jpg", ".jpeg", ".png", ".bmp"]

CLASS_NAMES = ["blue3", "blue1", "bluesb", "red3", "red1", "redsb"]
CLASS_TO_ID = {name: i for i, name in enumerate(CLASS_NAMES)}
def find_image(json_path, data):
    image_path = data.get("imagePath", "")

    if image_path:
        img = SRC / image_path
        if img.exists():
            return img

    for ext in IMG_EXTS:
        img = SRC / f"{json_path.stem}{ext}"
        if img.exists():
            return img

    return None

def convert_one_json_to_yolo(data, txt_path, class_to_id):
    image_w = data["imageWidth"]
    image_h = data["imageHeight"]

    lines = []

    for shape in data.get("shapes", []):
        if shape.get("shape_type") != "rectangle":
            continue

        label = shape["label"]
        class_id = class_to_id[label]

        points = shape["points"]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        x1 = max(0, min(xs))
        y1 = max(0, min(ys))
        x2 = min(image_w, max(xs))
        y2 = min(image_h, max(ys))

        box_w = x2 - x1
        box_h = y2 - y1

        if box_w <= 0 or box_h <= 0:
            continue

        x_center = (x1 + x2) / 2 / image_w
        y_center = (y1 + y2) / 2 / image_h
        norm_w = box_w / image_w
        norm_h = box_h / image_h

        lines.append(
            f"{class_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}"
        )

    txt_path.write_text("\n".join(lines), encoding="utf-8")

def main():
    image_files = sorted(
        p for p in SRC.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    )

    if not image_files:
        raise RuntimeError(f"没有在 {SRC} 找到图片文件")

    samples = []

    for img_path in image_files:
        json_path = SRC / f"{img_path.stem}.json"

        if json_path.exists():
            data = json.loads(json_path.read_text(encoding="utf-8"))
            samples.append((json_path, img_path, data))
        else:
            print(f"跳过未标注图片：{img_path.name}")

    if not samples:
        raise RuntimeError("没有找到有效的图片和 JSON 标注")

    print("使用固定类别：")
    for idx, name in enumerate(CLASS_NAMES):
        print(f"{idx}: {name}")

    if OUT.exists():
        shutil.rmtree(OUT)

    for split in ["train", "val"]:
        (OUT / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT / "labels" / split).mkdir(parents=True, exist_ok=True)

    random.seed(RANDOM_SEED)
    random.shuffle(samples)

    val_count = max(1, int(len(samples) * VAL_RATIO))
    val_samples = samples[:val_count]
    train_samples = samples[val_count:]

    def process(samples, split):
        for json_path, img_path, data in samples:
            dst_img = OUT / "images" / split / img_path.name
            dst_txt = OUT / "labels" / split / f"{img_path.stem}.txt"

            shutil.copy2(img_path, dst_img)

            if data is None:
                dst_txt.write_text("", encoding="utf-8")
            else:
                convert_one_json_to_yolo(data, dst_txt, CLASS_TO_ID)

    process(train_samples, "train")
    process(val_samples, "val")

    yaml_text = f"""path: {OUT.as_posix()}
train: images/train
val: images/val

names:
"""

    for i, name in enumerate(CLASS_NAMES):
        yaml_text += f"  {i}: {name}\n"

    (OUT / "data.yaml").write_text(yaml_text, encoding="utf-8")

    class_map_text = json.dumps(CLASS_TO_ID, ensure_ascii=False, indent=2)
    (OUT / "class_map.json").write_text(class_map_text, encoding="utf-8")

    print()
    print("转换完成！")
    print(f"训练集数量: {len(train_samples)}")
    print(f"验证集数量: {len(val_samples)}")
    print(f"输出位置: {OUT}")
    print(f"配置文件: {OUT / 'data.yaml'}")

if __name__ == "__main__":
    main()