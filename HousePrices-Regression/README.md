# House Prices Regression – Machine Learning Project

## Overview
This project uses supervised machine learning to predict house prices based on features such as size, number of rooms, and other property attributes.

## Approach

1. **Dataset**
   - Dataset: [Kaggle House Prices dataset or similar]
   - Target: Sale price
   - Features: Numeric and categorical features (area, rooms, etc.)

2. **Data Preparation**
   - Handle missing values
   - Encode categorical features
   - Split into train/validation/test sets

3. **Models**
   - Linear Regression
   - Decision Tree Regressor
   - Random Forest Regressor
   - Gradient Boosting Regressor (e.g., XGBoost or similar, if used)

4. **Evaluation**
   - Metrics: MAE, MSE, R²
   - Compare models and select the best-performing one

## Implementation
All code is in:

- `HousePrices_Regression.ipynb`

## Results
The `results/` folder can include:
- `predictions_vs_actuals.png` – plot comparing predicted vs real prices  
- `loss_curve.png` – training/validation error over epochs or iterations  
- `metrics.txt` – summary of metrics for each model  

## Technologies Used
- Python
- pandas, NumPy
- scikit-learn
- Matplotlib / Seaborn

## How to Run
1. Open `HousePrices_Regression.ipynb` in Google Colab.  
2. Ensure the dataset path or loading code is correct.  
3. Run all cells and review the metrics and plots.
