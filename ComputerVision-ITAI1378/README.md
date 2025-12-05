# Computer Vision Projects

This folder includes three core Computer Vision labs from the Applied AI program:

- **Lab 05 — CNN Classification (Chihuahua vs Muffin)**
- **Lab 08 — Visual Language Models (CLIP / BLIP / BLIP-2)**
- **Object Detection — TensorFlow + Pascal VOC (Transfer Learning)**

---

# 📌 Lab 05 — CNN Classification: Chihuahua vs Muffin

## Overview
This lab introduces Convolutional Neural Networks (CNNs) through a fun image classification task: distinguishing chihuahuas from muffins. You learn how convolutional layers extract spatial features and why CNNs outperform traditional neural networks in vision tasks.

## Setup
**Google Colab:**  
File → Open Notebook → GitHub → `patitimoner/workshop-chihuahua-vs-muffin`  
Open **CNN_1 Chihuahua or Muffin.ipynb**

## WHAT YOU DO
- Run all cells in the notebook  
- Fix missing imports or placeholders (“?”)  
- Verify that training outputs, plots, and evaluation results appear correctly  

## EXPERIMENTS
Adjust:
- EPOCHS  
- LEARNING RATE  
- MODEL DEPTH  
- OPTIMIZER  

Document how each change affects performance.

## REFLECTION
Include:
- CNN ARCHITECTURE SUMMARY  
- ACCURACY & MISCLASSIFICATION BEHAVIOR  
- COMPARISON: CNN VS TRADITIONAL NN  
- CHALLENGES & SOLUTIONS  
- REAL-WORLD APPLICATIONS  
- ETHICAL CONSIDERATIONS  

---

# 📌 LAB 08 — VISUAL LANGUAGE MODELS (CLIP / BLIP / BLIP-2)

## OVERVIEW
This lab explores Visual Language Models (VLMs), which combine image and text understanding using shared embeddings. You complete either **CLIP (Path A)** or **BLIP/BLIP-2 (Path B)** based on GPU availability.

## SETUP
Download **VLM_Lab_Exercise.ipynb**, upload to Colab, and rename:  
`L08_LastName_FirstName_ITAI1378.ipynb`  
Run the setup cell to install dependencies.

## PATH A — CLIP (CPU-FRIENDLY)
You perform:
- ZERO-SHOT IMAGE CLASSIFICATION  
- IMAGE SEARCH USING TEXT PROMPTS  
- EMBEDDING SIMILARITY INTERPRETATION  

## PATH B — BLIP / BLIP-2 (GPU REQUIRED)
You perform:
- IMAGE CAPTIONING  
- VISUAL QUESTION ANSWERING (VQA)  
- CONDITIONAL CAPTIONING (PROMPT-GUIDED)  

## REQUIRED ANALYSIS
All students must complete:
- FINE-TUNING & CONTRASTIVE LEARNING CONCEPTS  
- EVALUATION METRICS (RECALL@K OR BLEU)  
- APPLICATION TRADE-OFFS (COST, SCALABILITY, DEPLOYMENT)  
- ETHICAL CONSIDERATIONS (BIAS, HALLUCINATION, ENVIRONMENTAL IMPACT)  
- FINAL REFLECTIONS  

---

# 📌 OBJECT DETECTION — TENSORFLOW + PASCAL VOC (TRANSFER LEARNING)

## OVERVIEW
This lab expands from classification to object detection, where the model identifies objects **and localizes them with bounding boxes** using a pretrained SSD MobileNet model.

## SETUP
Download the notebook:  
**Student_Notebook_LAB_Object_Detection_transfer_learning.ipynb**  
Run in Google Colab or Amazon SageMaker Studio Lab.

Enable GPU in Colab:  
**Runtime → Change runtime type → GPU**

## WHAT YOU DO
- LOAD SSD MOBILENET FROM TENSORFLOW HUB  
- APPLY TRANSFER LEARNING TO PASCAL VOC–STYLE DATA  
- RUN INFERENCE BEFORE AND AFTER TRAINING  
- VISUALIZE BOUNDING BOXES ON TEST IMAGES  

## REFLECTION
Include:
- DIFFERENCE BETWEEN CLASSIFICATION AND DETECTION  
- TRANSFER LEARNING ADVANTAGES  
- MODEL STRENGTHS & LIMITATIONS  
- ETHICAL ISSUES (FALSE POSITIVES, DATASET BIAS)  
- TECHNICAL CHALLENGES & SOLUTIONS  


