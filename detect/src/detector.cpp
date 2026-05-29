#include "detector.h"
#include <iostream>
using namespace std;
//这个init函数作用是初始化检测器  1.加载ONNX模型 2.设置置信度阈值和NMS阈值 3.设置输入图像尺寸 4.初始化类别名称列表 5.设置推理后端
bool ArmorDetector::init(const std::string& model_path,
                         float conf_threshold,
                         float nms_threshold,
                         const cv::Size& input_size) {
    conf_threshold_ = conf_threshold;
    nms_threshold_ = nms_threshold;
    input_size_ = input_size;

    class_names_={
        "blue3",
        "blue1",
        "bluesb",
        "red3",
        "red1",
        "redsb"
    };
    try{
        net_=cv::dnn::readNetFromONNX(model_path);
    }catch (const cv::Exception& e){

        cerr<< "Failed to load ONNX model: " << model_path << endl;
        cerr << e.what() <<endl;
        return false;
    }
    if(net_.empty()){
        cerr << "Loaded network is empty: " << model_path << endl;
        return false;
    }
    net_.setPreferableBackend(cv::dnn::DNN_BACKEND_OPENCV);
    net_.setPreferableTarget(cv::dnn::DNN_TARGET_CPU);
    cout << "Loaded ONNX model: " << model_path << endl;
    cout << "Input size: " << input_size_.width << "x" << input_size_.height << endl;
    cout << "Class count: " << class_names_.size() << endl;

    return true;
}

bool ArmorDetector::detect(const cv::Mat& frame, std::vector<ArmorObject>& results) {
    results.clear();
    if (frame.empty()) return false;

    // TODO: 调用前处理 -> 送入网络推理 -> 调用后处理 -> 填充每个结果的 center 字段
    //送入网络推理
    
    cv::Mat blob=cv::dnn::blobFromImage(frame,1.0/255.0,input_size_,cv::Scalar(),true,false); //Scalar代表不减均值，也就是mean是()  第一个true是交换RB通道，第二个false是指不进行中心裁剪，直接按目标尺度缩放
    //frame是输入图像 [H,W,C]  blob是输出的四维张量 [N,C,H,W]  N是批次大小，C是通道数，H和W是输入图像的高度和宽度
    net_.setInput(blob);

    // cv::Mat output=net_.forward();
    // std::cout << "Output dims: " << output.dims << std::endl;
    //std::cout << "Output dims: " << output.dims << std::endl;
std::cout << "Frame size: " << frame.cols << "x" << frame.rows << std::endl;
std::cout << "Blob dims: " << blob.dims << std::endl;
for (int i = 0; i < blob.dims; ++i) {
    std::cout << "Blob size[" << i << "]: " << blob.size[i] << std::endl;
}

net_.setInput(blob);

cv::Mat output;
try {
    output = net_.forward();
} catch (const cv::Exception& e) {
    std::cerr << "DNN forward failed." << std::endl;
    std::cerr << e.what() << std::endl;
    return false;
}




    for(int i=0;i<output.dims;i++)
    {
        std::cout<<"Output size[" << i << "]: " << output.size[i] << std::endl;
    }


    return true;
}

cv::Mat ArmorDetector::preprocess(const cv::Mat& frame) {
    // TODO: 将原图转换为模型所需的输入格式



    (void)frame;
    return cv::Mat();
}

void ArmorDetector::postprocess(const cv::Mat& output,
                                const cv::Size& frame_size,
                                std::vector<ArmorObject>& results) {
    // TODO: 解析网络输出张量，筛选置信度，还原坐标到原图尺寸，执行 NMS



    (void)output;
    (void)frame_size;
    (void)results;
}
