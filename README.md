# 🎧 Spotify Music Analysis & Modeling Strategy

This project explores a dataset of Spotify tracks, artists, audio, and lyric features to identify patterns and present potential modeling strategies. Built using Python, Jupyter Notebooks, and designed for interactive presentation using **Voilà** or **Streamlit**.

## 📊 Project Goals

- Perform **exploratory data analysis (EDA)** on Spotify data
- Visualize patterns in popularity, genres, audio & lyrical features
- Outline **modeling strategies** for tasks like:
  - Popularity prediction
  - Genre classification
  - Unsupervised song clustering
- Share findings via a **clean Voilà dashboard** or **Streamlit app**

## 📁 Project Structure

```
├── notebooks/
│   └── eda\_model\_overview\.ipynb    # Main presentation notebook
├── data/
│   ├── spotify\_artists.csv
│   ├── spotify\_albums.csv
│   ├── spotify\_tracks.csv
│   ├── lyrics\_features.csv
│   └── low\_level\_audio\_features.csv
├── streamlit_app/                    # Streamlit application
│   ├── app.py                        # Main Streamlit app
│   ├── Dockerfile                    # Dockerfile for the app
│   └── requirements.txt              # App dependencies
├── docker-compose.yml                # Docker Compose configuration
├── .gitignore
├── README.md

```

## 🚀 Running Locally

### Option 1: Traditional Python Setup

#### 1. Clone the repository

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

#### 2. Set up Python environment

```bash
python -m venv venv
source venv/bin/activate  # or .\\venv\\Scripts\\activate on Windows
pip install -r requirements.txt
```

#### 3. Launch Voilà

```bash
voila scripts/exploration_analysis/voila_template.ipynb
```

This opens a web interface with your analysis presented cleanly — no code cells visible.

### Option 2: Docker Deployment (Streamlit App)

#### 1. Prerequisites

- Docker and Docker Compose installed on your system
- The Spotify dataset files in the `data/raw` directory

#### 2. Start the application

```bash
docker-compose up -d
```

#### 3. Access the Streamlit app

Open your browser and navigate to:
```
http://localhost:8501
```

## 🧠 Next Steps

* Implement models described in the strategy section
* Explore feature engineering techniques
* Package as a web app or deploy on Binder/Heroku


