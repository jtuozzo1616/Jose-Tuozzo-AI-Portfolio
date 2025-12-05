# Chihuahua vs Muffin – CNN Classifier

## Overview
This project trains a Convolutional Neural Network (CNN) to classify images as either chihuahuas or muffins. It is a classic example of how computer vision can handle visually similar classes.

## Problem Statement
Chihuahuas and muffins can look surprisingly similar in certain images. The goal is to build a CNN that can learn the visual patterns and correctly classify them.

## Approach
- Collect or use a prepared dataset of chihuahua and muffin images.
- Preprocess images (resize, normalize, possibly augment).
- Train a CNN on the dataset.
- Evaluate accuracy and inspect misclassifications.

## Implementation
All code is in:

- `Chihuahua_vs_Muffin.ipynb`

The notebook includes:
- Data loading and preprocessing
- CNN model definition and training
- Evaluation on validation/test data
- Plots of training history

## Results
The `results/` folder can include:
- `accuracy_plot.png` – training vs validation accuracy  
- `confusion_matrix.png` – confusion matrix on test data  
- `predictions.png` – sample predictions with labels  

## Technologies Used
- Python
- TensorFlow / Keras (or another DL framework)
- NumPy, pandas
- Matplotlib / Seaborn

## How to Run
1. Open `Chihuahua_vs_Muffin.ipynb` in Google Colab.  
2. Make sure the dataset path or download cell is correct.  
3. Run all cells.  
4. Check the generated plots and results in the notebook and in the `results/` folder.
