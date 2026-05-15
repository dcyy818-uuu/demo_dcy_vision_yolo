import json
import random
import shutil
from pathlib import Path

ROOT = Path(r"D:\RM_YOLO")
SRC = ROOT / "label_work"
OUT = ROOT / "datasets" / "armor"

VAL_RATIO = 0.2
RANDOM_SEED = 42

IMG_EXTS = [".jpg", ".jpeg", ".png", ".bmp"]

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
    json_files = sorted(SRC.glob("*.json"))

    if not json_files:
        raise RuntimeError(f"没有在 {SRC} 找到 json 文件")

    samples = []
    label_set = set()

    for json_path in json_files:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        img_path = find_image(json_path, data)

        if img_path is None:
            print(f"跳过：找不到 {json_path.name} 对应的图片")
            continue

        for shape in data.get("shapes", []):
            if shape.get("shape_type") == "rectangle":
                label_set.add(shape["label"])

        samples.append((json_path, img_path, data))

    if not samples:
        raise RuntimeError("没有找到有效的图片和 JSON 标注")

    if not label_set:
        raise RuntimeError("JSON 里面没有找到任何 rectangle 标注")

    class_names = sorted(label_set)
    class_to_id = {name: i for i, name in enumerate(class_names)}

    print("检测到的类别：")
    for name, idx in class_to_id.items():
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
            convert_one_json_to_yolo(data, dst_txt, class_to_id)

    process(train_samples, "train")
    process(val_samples, "val")

    yaml_text = f"""path: {OUT.as_posix()}
train: images/train
val: images/val

names:
"""

    for i, name in enumerate(class_names):
        yaml_text += f"  {i}: {name}\n"

    (OUT / "armor.yaml").write_text(yaml_text, encoding="utf-8")

    class_map_text = json.dumps(class_to_id, ensure_ascii=False, indent=2)
    (OUT / "class_map.json").write_text(class_map_text, encoding="utf-8")

    print()
    print("转换完成！")
    print(f"训练集数量: {len(train_samples)}")
    print(f"验证集数量: {len(val_samples)}")
    print(f"输出位置: {OUT}")
    print(f"配置文件: {OUT / 'armor.yaml'}")

if __name__ == "__main__":
    main()