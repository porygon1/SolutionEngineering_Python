# 🤝 Contributing to Spotify Music Recommendation

Thank you for your interest in contributing to the Spotify Music Recommendation project! This guide will help you get started with contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Release Process](#release-process)

## 🤗 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful** and inclusive to all contributors
- **Be collaborative** and help others learn
- **Be constructive** when giving feedback
- **Focus on what's best** for the community and project

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.11+** installed
- **Git** for version control
- **Docker & Docker Compose** (for testing deployment)
- **Jupyter Notebook** (for model development)

### Initial Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/spotify-music-recommendation.git
   cd spotify-music-recommendation
   ```

3. **Set up the development environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   .\venv\Scripts\activate   # Windows
   
   # Install development dependencies
   pip install -r streamlit_app/requirements.txt
   pip install -r scripts/Models/requirements.txt
   
   # Install development tools
   pip install black flake8 pytest pytest-cov pre-commit
   ```

4. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Verify setup**:
   ```bash
   # Test data loading
   python -c "import pandas, sklearn, hdbscan; print('✅ All imports successful')"
   
   # Test Streamlit app
   cd streamlit_app && streamlit run app.py --check-config
   ```

## 🔄 Development Workflow

### Branch Strategy

We use a **GitHub Flow** approach:

- **`main`** branch: Stable, production-ready code
- **Feature branches**: `feature/feature-name`
- **Bug fixes**: `fix/bug-description`
- **Documentation**: `docs/update-description`
- **Model improvements**: `model/improvement-description`

### Workflow Steps

1. **Create a new branch** from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes**:
   ```bash
   # Run tests
   pytest tests/
   
   # Check code style
   black . --check
   flake8 .
   
   # Test Streamlit app
   cd streamlit_app && streamlit run app.py
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

5. **Push and create Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   ```

## 📁 Project Structure

Understanding the project structure will help you contribute effectively:

```
spotify-music-recommendation/
├── 🎵 streamlit_app/           # Web application
│   ├── app.py                  # Main Streamlit app
│   ├── components/             # UI components
│   │   ├── sidebar.py          # Navigation sidebar
│   │   ├── track_grid.py       # Track display grid
│   │   ├── music_player.py     # Music player
│   │   └── recommendations.py  # Recommendations display
│   ├── utils/                  # Utility modules
│   ├── static/                 # Static assets
│   ├── requirements.txt        # App dependencies
│   └── Dockerfile             # Container config
├── 📊 scripts/                 # Analysis & modeling
│   ├── Models/                 # ML model training
│   │   └── HDBSCAN_Clusters_KNN.ipynb
│   └── exploration_analysis/   # Data exploration
├── 📂 data/                    # Data storage
│   ├── raw/                    # Original datasets
│   └── models/                 # Trained models
├── 🐳 Docker files
│   ├── docker-compose.yml
│   └── .dockerignore
└── 📚 Documentation
    ├── README.md
    ├── SETUP.md
    ├── CONTRIBUTING.md (this file)
    ├── DOCKER_SETUP.md
    └── SPOTIFY_SETUP.md
```

## 💻 Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

#### Code Formatting
```python
# Use Black for automatic formatting
black . --line-length 88

# Use flake8 for linting
flake8 . --max-line-length=88 --extend-ignore=E203,W503
```

#### Naming Conventions
```python
# Variables and functions: snake_case
def get_song_recommendations():
    cluster_labels = model.predict(features)
    
# Classes: PascalCase
class SpotifyRecommendationEngine:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RECOMMENDATIONS = 10
DEFAULT_CLUSTER_SIZE = 50
```

#### Import Organization
```python
# Standard library imports
import os
import pickle
from typing import Dict, List, Optional

# Third-party imports
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Local imports
from .utils import load_model
from .clustering import HDBSCANCluster
```

#### Docstrings
Use **Google-style docstrings**:

```python
def get_recommendations(song_idx: int, n_recommendations: int = 5) -> tuple:
    """Get song recommendations using KNN model.
    
    Args:
        song_idx: Index of the song in the dataset
        n_recommendations: Number of recommendations to return
        
    Returns:
        Tuple of (distances, indices) arrays
        
    Raises:
        ValueError: If song_idx is out of range
        
    Example:
        >>> distances, indices = get_recommendations(100, 5)
        >>> print(f"Found {len(indices)} recommendations")
    """
    # Implementation here
    pass
```

#### Type Hints
Use type hints for better code clarity:

```python
from typing import Dict, List, Optional, Tuple
import pandas as pd

def process_audio_features(
    tracks_df: pd.DataFrame,
    feature_columns: List[str]
) -> Tuple[np.ndarray, List[str]]:
    """Process audio features for ML model."""
    pass

# For complex types
ClusterResults = Dict[str, List[int]]
```

### Streamlit-Specific Guidelines

#### App Structure
```python
# Use functions for organization
def load_data():
    """Load and cache data."""
    pass

def create_sidebar():
    """Create sidebar controls."""
    pass

def main():
    """Main app function."""
    # Page config first
    st.set_page_config(...)
    
    # Then content
    create_sidebar()
    # ... rest of app
    
if __name__ == "__main__":
    main()
```

#### Caching
```python
# Use appropriate caching decorators
@st.cache_data
def load_csv_data(file_path: str) -> pd.DataFrame:
    """Load CSV data with caching."""
    return pd.read_csv(file_path)

@st.cache_resource
def load_ml_model(model_path: str):
    """Load ML model with resource caching."""
    return joblib.load(model_path)
```

#### Error Handling
```python
# Graceful error handling
try:
    data = load_data()
    if data.empty:
        st.error("No data available")
        return
except FileNotFoundError:
    st.error("Data files not found. Please check SETUP.md")
    return
except Exception as e:
    st.error(f"Unexpected error: {e}")
    return
```

### Jupyter Notebook Guidelines

#### Cell Organization
- **Markdown cells**: Use for documentation and explanations
- **Code cells**: Keep concise and focused
- **Clear outputs**: Remove unnecessary outputs before committing

#### Code Structure
```python
# Use clear section headers
# %% [markdown]
# ## Data Loading and Validation

# %% 
# Load datasets
tracks_df = pd.read_csv("data/raw/spotify_tracks.csv")
print(f"Loaded {len(tracks_df):,} tracks")

# %% [markdown]
# ### Feature Engineering
```

#### Variables and Functions
```python
# Use descriptive variable names
audio_features_normalized = scaler.fit_transform(audio_features)
cluster_assignments = clusterer.fit_predict(audio_features_normalized)

# Create reusable functions
def evaluate_clustering_quality(features, labels):
    """Evaluate clustering using multiple metrics."""
    pass
```

## 🧪 Testing Guidelines

### Test Structure

We use **pytest** for testing. Organize tests by component:

```
tests/
├── test_data_loading.py        # Data loading functions
├── test_models.py              # ML model functions  
├── test_streamlit_app.py       # Streamlit app components
├── test_clustering.py          # Clustering algorithms
└── conftest.py                 # Shared fixtures
```

### Test Examples

#### Unit Tests
```python
# tests/test_models.py
import pytest
import numpy as np
from unittest.mock import Mock, patch

def test_get_recommendations():
    """Test recommendation generation."""
    # Mock data
    mock_knn = Mock()
    mock_knn.kneighbors.return_value = (
        np.array([[0.1, 0.2, 0.3]]), 
        np.array([[0, 5, 10]])
    )
    
    # Test function
    distances, indices = get_recommendations(mock_knn, 0, n_neighbors=3)
    
    # Assertions
    assert len(distances) == 3
    assert len(indices) == 3
    assert indices[0] == 0  # First result should be input song
```

#### Integration Tests
```python
# tests/test_streamlit_app.py
def test_app_loads_without_error():
    """Test that app loads without errors."""
    with patch('streamlit_app.app.load_data') as mock_load:
        mock_load.return_value = pd.DataFrame({'name': ['test']})
        
        # Import should not raise errors
        import streamlit_app.app
        assert True  # If we get here, app loaded successfully
```

#### Data Validation Tests
```python
# tests/test_data_loading.py
def test_required_columns_present():
    """Test that required columns are in datasets."""
    required_columns = ['name', 'artists_id', 'danceability', 'energy']
    
    # Load test data
    df = load_data('tests/fixtures/test_tracks.csv')
    
    # Check columns
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=streamlit_app --cov=scripts

# Run specific test file
pytest tests/test_models.py

# Run tests matching pattern
pytest -k "test_recommendations"

# Verbose output
pytest -v
```

## 📖 Documentation

### Code Documentation

#### Functions and Classes
- Use **docstrings** for all public functions and classes
- Include **type hints** for parameters and return values
- Provide **examples** for complex functions

#### Inline Comments
```python
# Good: Explain WHY, not WHAT
cluster_size = max(50, len(features) // 100)  # Ensure clusters scale with dataset size

# Avoid: Obvious comments
features_scaled = scaler.fit_transform(features)  # Scale the features
```

### README Updates

When adding features, update relevant README sections:

- **Main README.md**: High-level feature descriptions
- **streamlit_app/README.md**: App-specific features
- **scripts/Models/README.md**: Model-related changes

### Jupyter Notebook Documentation

- Use **markdown cells** to explain methodology
- Include **visualization** of results
- Document **parameter choices** and **assumptions**

### Changelog

Update `CHANGELOG.md` with your changes:

```markdown
## [Unreleased]

### Added
- New audio feature extraction for MFCC analysis
- Cluster visualization improvements

### Changed
- Updated Streamlit to version 1.40.0
- Improved recommendation algorithm performance

### Fixed
- Fixed artist name mapping for collaborative playlists
```

## 🔍 Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   pytest
   black . --check
   flake8 .
   ```

2. **Update documentation** as needed

3. **Test manually**:
   ```bash
   # Test Streamlit app
   cd streamlit_app && streamlit run app.py
   
   # Test Docker build
   docker-compose build
   ```

### PR Title and Description

Use **conventional commits** for PR titles:

- `feat: add new clustering algorithm`
- `fix: resolve audio playback issue`
- `docs: update setup instructions`
- `refactor: improve code organization`
- `test: add model validation tests`

### PR Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Manual testing completed

## Screenshots (if applicable)
Include screenshots for UI changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. **Automated checks** must pass (GitHub Actions)
2. **Code review** by maintainers
3. **Testing** of functionality
4. **Approval** and merge

## 🐛 Issue Guidelines

### Bug Reports

Use the bug report template:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. Windows 10, macOS 12]
- Python version: [e.g. 3.11.0]
- Streamlit version: [e.g. 1.40.0]

**Additional context**
Any other context about the problem.
```

### Feature Requests

```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

### Issue Labels

We use these labels to categorize issues:

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

## 🚀 Release Process

### Version Numbers

We use **Semantic Versioning** (SemVer):

- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible functionality additions
- **PATCH**: Backwards-compatible bug fixes

Examples:
- `1.0.0` → `1.0.1` (bug fix)
- `1.0.1` → `1.1.0` (new feature)
- `1.1.0` → `2.0.0` (breaking change)

### Release Checklist

1. **Update version numbers** in relevant files
2. **Update CHANGELOG.md** with release notes
3. **Create release tag**:
   ```bash
   git tag -a v1.1.0 -m "Release version 1.1.0"
   git push origin v1.1.0
   ```
4. **Create GitHub release** with release notes
5. **Update documentation** as needed

## 💡 Tips for Contributors

### Getting Familiar with the Codebase

1. **Start with the main README** to understand the project
2. **Run the application** to see it in action
3. **Explore the Jupyter notebook** to understand the ML pipeline
4. **Look at existing issues** for contribution ideas

### Best Practices

- **Start small**: Begin with documentation improvements or small bugs
- **Ask questions**: Use GitHub Discussions for questions
- **Be patient**: Code review takes time for quality assurance
- **Follow conventions**: Consistency helps everyone

### Common Pitfalls to Avoid

- **Large commits**: Break down changes into smaller, focused commits
- **Missing tests**: Always add tests for new functionality
- **Undocumented changes**: Update documentation when changing behavior
- **Breaking changes**: Avoid breaking existing functionality without discussion

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check README files and inline documentation
- **Code Review**: Ask for feedback during the PR process

## 🙏 Recognition

We appreciate all contributions! Contributors are recognized in:

- **GitHub Contributors** page
- **CHANGELOG.md** release notes
- **Project README** acknowledgments

---

**Thank you for contributing to the Spotify Music Recommendation System! 🎵** 