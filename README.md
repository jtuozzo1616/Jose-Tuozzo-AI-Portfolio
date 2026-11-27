# José Tuozzo | Applied AI & Robotics Portfolio

**Houston Community College · Applied Artificial Intelligence · Academic project portfolio**

I develop practical AI systems that connect perception, data analysis, machine learning and human-centered interaction. My focus is on reproducible experiments, interpretable decisions, responsible deployment and integration with physical robotic platforms.

## Featured projects

| Project | Focus | Evidence / scope |
|---|---|---|
| [PiDog robotics — ITAI 2374](ITAI2374-PiDog/README.md) | Python, quadruped motion, sensor fusion, SSH | Recovered course source code, hardware-independent tests, documented physical observations; integration requires supervised hardware validation |
| [RoboGuide AI — ITAI 2377](ITAI2377-RoboGuide/README.md) | Evidence-grounded robotics troubleshooting | Development MRR@5 0.7742 → 0.8387; 8-question test slice tied at 1.000; exploratory 43-query benchmark |
| [NewsBot 2.0 — ITAI 2373](ITAI2373-NewsBot-Final/README.md) | NLP, multilingual retrieval, topic modeling, Streamlit | 90.8% accuracy and 0.9079 macro-F1 on 250 historical BBC articles (3-fold CV); 38 tests in latest canonical CI |
| [HealthLens AI — ITAI 2372](https://github.com/jtuozzo1616/HealthLens-AI-Explainable-Symptom-Analysis) | Explainable TF-IDF retrieval, abstention, safety rules | Fictional text only; 56 synthetic training examples and 26 evaluation cases; not clinical software |
| [NewsBot midterm — ITAI 2373](ITAI2373-NewsBot-Midterm/README.md) | Text normalization, sentiment, NER, classification | 96.18% accuracy and 0.9605 macro-F1 on separate 288-article historical holdout |
| [Computer vision — ITAI 1378](ComputerVision-ITAI1378/README.md) | CNNs, object detection, vision-language models | Runnable lab notebooks; dataset and compute requirements vary |
| [House price regression](MachineLearning-Projects/README.md) | Regression, feature engineering, EDA | Notebook, housing CSV and analysis; see saved outputs |
| [Data analysis foundations](Cybersecurity/README.md) | Pandas, Matplotlib, Seaborn | Python script and visualization notebooks |

## Robotics: from physical control to intelligent assistance

- **PiDog:** physical servo control, sequential actions, range/touch sensing, camera-marker navigation and sound-direction cues. [Source and test instructions](ITAI2374-PiDog/README.md).
- **RoboGuide:** separate software assistant that retrieves manufacturer guidance with version-aware safeguards. It does not control the robot. [Colab notebook](ITAI2377-RoboGuide/notebooks/RoboGuide_Colab.ipynb) · [Metrics](ITAI2377-RoboGuide/results/metrics.json) · [Architecture](ITAI2377-RoboGuide/docs/figures/00_architecture.png).

## NLP: research and working applications

- **NewsBot final:** [canonical repository](https://github.com/jtuozzo1616/Final-Jose-Group-NewsBot-Intelligence-System) · [executed master notebook](ITAI2373-NewsBot-Final/evidence/NewsBot_JoseT_2_0_Master_Colab.ipynb) · [live application](https://final-jose-group-newsbot-intelligence-system-al984gd7vc9uzqmek.streamlit.app/) · [evaluation evidence](ITAI2373-NewsBot-Final/evidence/README.md).
- **NewsBot midterm:** [notebook](ITAI2373-NewsBot-Midterm/Midterm_NewsBot_Intelligence_System.ipynb) · [technical results](ITAI2373-NewsBot-Midterm/docs/Technical_Results_Summary.md). Historical midterm and final measurements use different evaluation designs and are not directly comparable.
- **HealthLens:** [source, setup, tests and data](https://github.com/jtuozzo1616/HealthLens-AI-Explainable-Symptom-Analysis). Educational safety-conscious language classification; not for medical decisions.

## Computer vision and ML notebooks

- [Chihuahua vs. Muffin CNN](ComputerVision-ITAI1378/Lab05_CNN_Chihuahua_Muffin_JoseTuozzo.ipynb)
- [Pascal VOC object detection](ComputerVision-ITAI1378/Lab06_Orig_ITAI_1378_VOC2007__Dataset_JoseTuozzo_Notebook_LAB_Object_Detection_transfer_learning%282%29_fixed.ipynb)
- [CLIP / BLIP vision-language lab](ComputerVision-ITAI1378/Lab_08_2025_VLM_Lab_JoseTuozzo%281%29_fixed.ipynb)
- [Waste classification experiment](https://github.com/jtuozzo1616/Waste_Classification) — EfficientNet-B0 and Grad-CAM notebook; performance targets are not verified test results.
- [Housing regression notebook](MachineLearning-Projects/MidTerm_Group3.ipynb)
- [Pandas exercise](Cybersecurity/Jose_Tuozzo_Pandas101%281%29.py) · [Matplotlib](Cybersecurity/MatPlotLib_JoseTuozzo.ipynb) · [Seaborn](Cybersecurity/Seaborn_JoseTuozzoIzaguirre.ipynb)

## Reproduce and review

Each featured project links to its own README, source and available results. Follow the project-specific dependency instructions rather than installing a single global environment. Hardware projects require the appropriate calibrated Raspberry Pi / PiDog setup; offline logic tests do not establish real-world safety. For notebooks, use a clean Colab or Jupyter runtime and follow the data access instructions. Some older notebook environments may need version adjustments.

## Skills and technologies

Python · Raspberry Pi · PiDog / Robot HAT · SSH · sensor fusion · OpenCV · PyTorch · TensorFlow · scikit-learn · Pandas · NumPy · NLP · TF-IDF · computer vision · Grad-CAM · Jupyter / Colab · Gradio · Streamlit · GitHub Actions · evaluation and technical documentation.

## Academic ownership and limitations

This portfolio includes individual exercises and group projects. Group results belong to the relevant teams; consult their contribution records for individual responsibilities. Manufacturer examples are attributed to SunFounder. Reported scores are scoped to their recorded datasets; simulations and software-only tests do not imply field validation. Next steps include collecting repeatable physical robot trials, broader independent evaluation, and improving reproducibility of older labs.

## Contact

- [GitHub](https://github.com/jtuozzo1616)
- [LinkedIn](https://www.linkedin.com/in/jos%C3%A9-tuozzo-a018762a)
- Email: jmtuozzoi@gmail.com
