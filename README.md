# RM 装甲板 YOLO 检测

这是 RoboMaster 视觉组一阶段考核项目。主要完成了装甲板数据标注、LabelMe 标注转 YOLO 格式、YOLO11s 训练，以及 `.pt` 模型到 `.onnx` 模型的导出。

## 类别

这次按考核文档要求标了 6 类装甲板：

| id | name |
|---:|---|
| 0 | blue3 |
| 1 | blue1 |
| 2 | bluesb |
| 3 | red3 |
| 4 | red1 |
| 5 | redsb |

标注时只标两侧灯条可见并且亮灯的装甲板。类别不确定、灯条缺失或者不适合后续解算的目标没有作为正样本标注。

## 数据处理

原始标注是 LabelMe 的 JSON 文件，训练前已经转换为 YOLO detection 格式。

转换后的数据集结构如下：

```text
dataset
├── images
│   ├── train
│   └── val
└── labels
    ├── train
    └── val
```

当前划分：

```text
train: 256 images
val: 64 images
```

训练使用的配置文件是：

```text
data.yaml
```

## 训练

正式训练使用的是 `yolo11s.pt`，没有用 nano 作为最终模型。nano 只用于前面测试流程能不能跑通。

训练脚本：

```text
yolo_train.py
```

主要参数：

```text
model: yolo11s.pt
epochs: 200
imgsz: 640
batch: 16
device: 0
workers: 0
patience: 50
close_mosaic: 10
```

训练命令：

```powershell
conda run -n rm_yolo python yolo_train.py
```

训练结果保存在：

```text
runs/detect/rm_armor_yolo11s
```

## 结果

本次训练的最佳指标如下：

```text
best epoch: 128
precision: 0.96058
recall: 0.98663
mAP50: 0.98432
mAP50-95: 0.96221
```

训练过程中生成的主要结果文件：

```text
runs/detect/rm_armor_yolo11s/results.csv
runs/detect/rm_armor_yolo11s/results.png
runs/detect/rm_armor_yolo11s/confusion_matrix.png
runs/detect/rm_armor_yolo11s/confusion_matrix_normalized.png
```

最好的 PyTorch 权重：

```text
runs/detect/rm_armor_yolo11s/weights/best.pt
```

## ONNX 导出

导出脚本：

```text
yolo_convert.py
```

导出命令：

```powershell
conda run -n rm_yolo python yolo_convert.py
```

导出的模型：

```text
runs/detect/rm_armor_yolo11s/weights/best.onnx
```

## 文件说明

```text
data.yaml                      数据集配置
yolo_train.py                  训练脚本
yolo_convert.py                ONNX 导出脚本
runs/detect/rm_armor_yolo11s   正式训练日志、图表和权重
```

数据集、原始图片、标注工作目录和下载的预训练权重没有放进仓库，避免仓库体积太大。最终提交主要保留代码、训练日志图表、训练得到的权重和导出的 ONNX 文件。
