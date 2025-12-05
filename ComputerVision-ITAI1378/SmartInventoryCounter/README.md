# SmartInventoryCounter – Object Detection for Inventory

## Overview
This project uses an object detection model to detect and count items in images as a way to support inventory tracking. It was developed as part of the ITAI 1378 Computer Vision course.

## Problem Statement
Manually counting items in shelves or storage areas is time-consuming and error-prone. This project explores how computer vision can help automate the process.

## Approach
- Use images of items on shelves or similar scenes.
- Apply an object detection workflow (YOLO-style or similar).
- Draw bounding boxes around detected objects.
- Count detections per class.

## Implementation
All code is in the notebook:

- `SmartInventoryCounter.ipynb`

The notebook includes:
- Data loading and preprocessing
- Model training or inference
- Visualization of detection results

## Results
The `results/` folder can include:
- `detections_sample.png` – example of detected items with bounding boxes  
- `training_history.png` – loss/metric curves (if the model was trained)  
- `metrics.txt` – summary of evaluation metrics (mAP, precision, recall, or a qualitative description)

## Technologies Used
- Python
- Jupyter Notebook / Google Colab
- NumPy, pandas
- OpenCV
- Deep learning framework (TensorFlow/Keras or PyTorch, depending on the implementation)
- Matplotlib for visualization

## How to Run
1. Open `SmartInventoryCounter.ipynb` in Google Colab or Jupyter Notebook.  
2. Install any required packages listed at the top of the notebook.  
3. Run all cells in order.  
4. Review the detection results and metrics in the notebook and the `results/` folder.
