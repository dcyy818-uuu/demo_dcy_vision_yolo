# RoboMaster 2027 视觉考核阶段二问题记录

这份 README 用来记录我在阶段二到目前为止遇到的问题、排查过程、解决办法和当前结论。它不是最终验收用的完整运行说明；最终的 C++ 工程复现说明后续会继续整理到 `detect/README.md`。

## 1. 当前任务理解

阶段二的重点不是继续训练模型，而是把阶段一训练得到的 YOLO 模型部署到 C++ 工程中，完成 RoboMaster 装甲板检测，并输出画面中所有可靠装甲板中心点。

当前主线任务可以理解为：

```text
阶段一模型训练与导出
    ↓
创建 detect 分支
    ↓
加入 detect/ C++ 工程模板
    ↓
配置 C++ / CMake / OpenCV 环境
    ↓
加载 ONNX 模型
    ↓
完成推理
    ↓
解析 YOLO 输出
    ↓
计算并可视化所有装甲板中心点
```

目前进度：已经完成环境配置、模板编译、OpenCV 基础 demo、ONNX 加载和 OpenCV DNN 排查；还没有完成真正的推理后处理和中心点可视化。

## 2. CMake 找不到的问题

### 问题现象

一开始在 PowerShell 中执行：

```powershell
cmake --version
```

报错：

```text
无法将“cmake”项识别为 cmdlet、函数、脚本文件或可运行程序的名称
```

### 原因

CMake 实际已经安装在：

```text
D:\CMake
```

但系统环境变量 `PATH` 中没有加入：

```text
D:\CMake\bin
```

所以 PowerShell 找不到 `cmake.exe`。

### 解决办法

将 `D:\CMake\bin` 加入系统环境变量，或者临时执行：

```powershell
$env:Path = "D:\CMake\bin;" + $env:Path
```

之后再执行：

```powershell
cmake --version
```

可以正常输出版本号。

## 3. 为什么改用 WSL / Ubuntu

### 问题

我之前只安装了 Python 里的 OpenCV，也就是 Python 中可以：

```python
import cv2
```

但阶段二是 C++ 工程，C++ 需要的是 OpenCV 的开发环境，包括：

```text
头文件
库文件
OpenCVConfig.cmake
```

Python 的 `opencv-python` 不能直接给 C++ 项目链接使用。

### 选择 WSL 的原因

考核文档推荐 Linux / WSL / macOS，因为 RoboMaster 后续实车部署环境更接近 Linux。Ubuntu 中安装 C++ OpenCV 比 Windows 下配置 MinGW / MSVC / OpenCV 库更直接。

在 WSL Ubuntu 中安装：

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config libopencv-dev
```

当前验证到的环境：

```text
CMake: 3.28.3
g++: 13.3.0
OpenCV: 4.6.0
```

## 4. CMake 构建流程理解

阶段二模板工程使用 CMake 构建。

在 `detect/` 目录下执行：

```bash
cd /mnt/d/RM_YOLO/detect
cmake -S . -B build
cmake --build build
./build/armor_detect
```

含义：

```text
cmake -S . -B build
读取当前目录的 CMakeLists.txt，在 build/ 中生成 Makefile 等构建文件。

cmake --build build
根据 build/ 中的构建文件调用 make / g++，编译并链接程序。

./build/armor_detect
运行生成的可执行文件。
```

`CMakeLists.txt` 中几个关键语句的作用：

```cmake
find_package(OpenCV 4.5 REQUIRED)
```

查找系统中的 OpenCV。如果找不到，就停止配置。

```cmake
include_directories(...)
```

告诉编译器头文件搜索路径，例如项目的 `include/` 和 OpenCV 头文件目录。

```cmake
target_link_libraries(...)
```

把 OpenCV 库链接到最终可执行程序中，否则可能出现 OpenCV 函数找不到实现的问题。

## 5. OpenCV 最小 demo

在正式进行 ONNX 推理之前，先做了一个最小 OpenCV C++ demo，验证：

```text
cv::imread() 读取图片
cv::circle() 绘制圆
cv::putText() 绘制文字
cv::imwrite() 保存结果图
```

这个 demo 已经成功，说明 C++ 工程中的 OpenCV 基础读图、绘制和保存功能可用。

## 6. 图片路径问题

### 问题现象

读取测试图片时，曾经出现：

```text
can't open/read file: check file path/integrity
```

### 原因

路径写错。

如果当前运行目录是：

```text
/mnt/d/RM_YOLO/detect
```

那么：

```text
assets/test.jpg
```

表示：

```text
/mnt/d/RM_YOLO/detect/assets/test.jpg
```

而：

```text
../assets/test.jpg
```

表示：

```text
/mnt/d/RM_YOLO/assets/test.jpg
```

如果写成：

```text
/assets/test.jpg
```

则表示 Linux 根目录下的：

```text
/assets/test.jpg
```

这通常不是项目中的图片路径。

### 解决办法

测试图片实际放在：

```text
detect/assets/opencv_test.jpg
```

所以代码中使用：

```cpp
cv::Mat test_image = cv::imread("assets/opencv_test.jpg");
```

并添加检查：

```cpp
if (test_image.empty()) {
    std::cerr << "Failed to read test image: assets/opencv_test.jpg" << std::endl;
    return 1;
}
```

## 7. OpenCV DNN 基本流程

考核推荐初学者先了解 OpenCV DNN。当前已经尝试并理解了基本流程：

```text
1. cv::dnn::readNetFromONNX() 加载 ONNX 模型
2. cv::dnn::blobFromImage() 将图片转成模型输入 blob
3. net.setInput(blob) 设置输入
4. net.forward() 执行推理
5. 打印输出张量维度
6. 根据输出格式写后处理
```

当前已经能够使用 OpenCV DNN 加载模型，并打印输入 blob。

## 8. ONNX 模型加载与输入 blob 验证

使用模型：

```text
rm_armor_yolo11s_best.onnx
```

程序能够输出：

```text
Loaded ONNX model
Input size: 640x640
Class count: 6
```

说明模型可以被 OpenCV DNN 加载。

测试图片经过 `blobFromImage()` 后，打印得到：

```text
Frame size: 1920x1192
Blob dims: 4
Blob size[0]: 1
Blob size[1]: 3
Blob size[2]: 640
Blob size[3]: 640
```

这说明输入已经变成模型需要的：

```text
NCHW = 1 x 3 x 640 x 640
```

因此目前前处理输入尺寸没有明显问题。

## 9. 模型输出格式理解

使用 Ultralytics 导出 ONNX 时，输出信息显示：

```text
output shape(s): (1, 10, 8400)
```

这就是当前 YOLO11s ONNX 模型的输出格式。

含义：

```text
1      batch size，一次输入 1 张图
10     每个候选框的输出通道数
8400   候选框数量
```

本模型类别为 6 类：

```text
0: blue3
1: blue1
2: bluesb
3: red3
4: red1
5: redsb
```

所以：

```text
10 = 4 个 bbox 参数 + 6 个类别分数
```

对第 `j` 个候选框，大概率对应：

```text
output[0][0][j] = x_center
output[0][1][j] = y_center
output[0][2][j] = width
output[0][3][j] = height
output[0][4][j] = blue3 score
output[0][5][j] = blue1 score
output[0][6][j] = bluesb score
output[0][7][j] = red3 score
output[0][8][j] = red1 score
output[0][9][j] = redsb score
```

后处理时应从 6 个类别分数中取最大值：

```text
class_id = argmax(class_scores)
confidence = max(class_scores)
```

然后根据 `x_center, y_center, width, height` 还原检测框，并计算中心点。

## 10. objectness 的理解

不同 YOLO 版本导出的 ONNX 输出格式可能不同。

例如 YOLOv5 常见输出可能是：

```text
x, y, w, h, objectness, class0_score, class1_score, ...
```

其中 `objectness` 表示这个候选框中是否存在任意目标。最终置信度一般为：

```text
confidence = objectness * class_score
```

但当前 YOLO11s 输出为：

```text
(1, 10, 8400)
```

类别数是 6，符合：

```text
10 = 4 + 6
```

因此它大概率没有单独的 objectness，不能直接照搬 YOLOv5 的后处理逻辑。

## 11. OpenCV DNN forward 失败

### 问题现象

原始 ONNX：

```text
rm_armor_yolo11s_best.onnx
```

可以被 OpenCV DNN 加载，输入 blob 也正确，但执行：

```cpp
net_.forward()
```

时报错：

```text
OpenCV(4.6.0) ... shape_utils.hpp:170:
(-215:Assertion failed) start <= shape.size() && end <= shape.size()
```

### 判断

由于输入 blob 已经确认是：

```text
1 x 3 x 640 x 640
```

所以问题不在图片读取，也不在基本前处理，而更可能是 OpenCV 4.6.0 DNN 对当前 YOLO11s ONNX 图结构兼容性不足。

## 12. 重新导出 ONNX 的尝试

### 尝试 1：opset=12, simplify=False

导出命令：

```powershell
python -c "from ultralytics import YOLO; model=YOLO(r'runs\detect\rm_armor_yolo11s\weights\best.pt'); model.export(format='onnx', imgsz=640, opset=12, simplify=False, dynamic=False)"
```

复制为：

```text
rm_armor_yolo11s_best_opencv.onnx
```

结果：

```text
OpenCV DNN 在加载阶段失败
```

错误核心：

```text
Node [Add] parse error
blob_0.size == blob_1.size
```

说明该导出方式并不适合当前 OpenCV 4.6.0 DNN。

### 尝试 2：opset=11, simplify=True

导出命令：

```powershell
python -c "from ultralytics import YOLO; model=YOLO(r'runs\detect\rm_armor_yolo11s\weights\best.pt'); model.export(format='onnx', imgsz=640, opset=11, simplify=True, dynamic=False)"
```

复制为：

```text
rm_armor_yolo11s_best_opencv_opset11.onnx
```

结果：

```text
OpenCV DNN 可以加载模型
输入 blob 正确
net.forward() 仍然失败
```

错误核心仍然是：

```text
OpenCV(4.6.0) ... shape_utils.hpp:170:
(-215:Assertion failed) start <= shape.size() && end <= shape.size()
```

说明降低到 `opset=11` 仍没有解决当前 OpenCV DNN 的兼容问题。

## 13. opset 的理解

`opset` 是 ONNX Operator Set Version，也就是 ONNX 算子集版本。

ONNX 模型由很多算子组成，例如：

```text
Conv
Add
Mul
Concat
Reshape
Transpose
Sigmoid
```

`opset` 决定这些算子按照哪一版规则保存和解释。推理框架需要支持对应版本的算子和 shape 推导规则。

尝试降低 `opset` 的原因是：

```text
OpenCV 4.6.0 较旧，YOLO11 较新；
使用更保守的 ONNX 算子版本可能提高兼容性。
```

实际结果：

```text
opset=11 仍无法让 OpenCV 4.6.0 DNN 成功 forward。
```

## 14. 当前结论

目前可以确认：

```text
1. WSL 下 C++ / CMake / OpenCV 基础环境可用。
2. detect 模板工程可以成功编译运行。
3. OpenCV C++ 的读图、绘制、保存功能可用。
4. OpenCV DNN 的基本调用流程已经掌握。
5. ONNX 模型可以被 OpenCV DNN 加载。
6. 输入 blob 维度正确，为 1 x 3 x 640 x 640。
7. Ultralytics 导出显示模型输出 shape 为 1 x 10 x 8400。
8. OpenCV 4.6.0 DNN 在 forward 当前 YOLO11s ONNX 时失败。
9. 尝试 opset=12 simplify=False 和 opset=11 simplify=True 后，问题仍未解决。
```

目前主要问题是：

```text
OpenCV 4.6.0 DNN 对当前 YOLO11s ONNX 模型图结构兼容性不足。
```

## 15. 下一步计划

后续有两条路线：

```text
路线 A：升级 OpenCV 到较新版本，例如 4.10 / 4.11 / 4.12，再继续尝试 OpenCV DNN。
路线 B：切换到 ONNX Runtime 完成模型推理，OpenCV 继续负责图像读取、绘制和可视化。
```

考虑到阶段二的核心目标是完成模型部署、后处理、中心点输出和可视化，当前更倾向于：

```text
使用 ONNX Runtime 完成模型推理。
```

之后继续推进：

```text
ONNX Runtime 推理
打印 C++ 输出张量
按 (1, 10, 8400) 编写 YOLO 后处理
执行 NMS
输出 bbox / class_id / confidence / center
可视化所有装甲板中心点
保存 results
```
