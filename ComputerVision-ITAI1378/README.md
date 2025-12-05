# Computer Vision Projects – CNNs, VLMs, and Object Detection

## Overview

This section contains three core computer vision labs covering Convolutional Neural Networks (CNNs), Visual Language Models (VLMs), and Object Detection. These projects apply deep learning techniques for image classification, multimodal reasoning, and bounding box detection.

## Objectives

- Understand how CNNs extract and learn visual features
- Explore multimodal AI through CLIP and BLIP
- Perform object detection using transfer learning
- Learn how deep learning models can be evaluated and improved

## Technologies Used

- Python
- Jupyter Notebook / Google Colab
- TensorFlow / TensorFlow Hub
- PyTorch (for CLIP / BLIP)
- OpenCV
- Matplotlib / Seaborn

## How to Run

1. Open any notebook in Google Colab or Jupyter Notebook.
2. Install required libraries (if needed), for example:

   !pip install tensorflow opencv-python matplotlib seaborn torch torchvision
   
3. For Object Detection labs, enable GPU in Colab:

- Runtime → Change runtime type → GPU

4. Run all cells in sequence from top to bottom.

5. Review the outputs, visualizations, and evaluation metrics.

## Results 
- Lab 05 – CNN (Chihuahua vs Muffin)
Achieved image classification performance on a “Chihuahua vs Muffin” dataset and visualized filters, feature maps, and misclassifications.

- Lab 08 – Visual Language Models (CLIP / BLIP)
Performed zero-shot classification, generated captions, executed visual question answering (VQA), and analyzed embedding similarities between images and text prompts.

- Object Detection – Transfer Learning
Fine-tuned an SSD MobileNet–style model and produced bounding boxes on Pascal VOC–style images, evaluating detection performance qualitatively and quantitatively.

## Key Learnings

- How convolutional layers detect patterns across spatial dimensions

- How VLMs integrate text and image embeddings for joint reasoning

- How transfer learning accelerates object detection performance

- Practical challenges such as dataset handling, GPU usage, and model evaluation

## My Role in These Computer Vision Projects

Across these labs, I was responsible for:

- Designing and implementing CNN and vision-language model notebooks end to end

- Preparing image datasets and performing preprocessing such as resizing, normalization, and augmentations

- Training, validating, and evaluating CNNs, object detection models, and VLMs (CLIP / BLIP)

- Running transfer learning workflows with TensorFlow Hub and Pascal VOC–style datasets

- Visualizing detection outputs, attention maps, similarity matrices, and classification results

- Documenting findings, interpreting accuracy and loss curves, bounding-box metrics, and explaining model limitations

## Note: Standard public datasets are referenced in the notebooks rather than uploaded directly to this repository. Dataset names and loading methods are documented inside each notebook.
