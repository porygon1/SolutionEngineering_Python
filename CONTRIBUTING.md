# 🤝 Contributing to Spotify Music Recommendation System v2

**Welcome to the community! We appreciate your interest in contributing to this AI-powered music discovery platform.**

## 🎯 Overview

This document provides comprehensive guidelines for contributing to the Spotify Music Recommendation System v2, including:
- **Code contributions** and best practices
- **Development environment** setup
- **Testing requirements** and procedures
- **Documentation standards**
- **Issue reporting** and feature requests

## 🚀 Quick Start for Contributors

### 1. Fork and Clone
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/your-username/spotify-recommendation-system.git
cd spotify-recommendation-system

# Add upstream remote
git remote add upstream https://github.com/original-repo/spotify-recommendation-system.git
```

### 2. Development Setup
```bash
# Set up the complete development environment
cd spotify_recommendation_system_v2

# Start development services
docker-compose up database -d

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend setup
cd ../frontend
npm install
```

### 3. Create Feature Branch
```bash
# Create and switch to feature branch
git checkout -b feature/your-feature-name

# Make your changes...

# Commit with conventional format
git commit -m "feat: add music similarity visualization"
```

## 📋 Contribution Types

### 🐛 Bug Reports
Use GitHub Issues with the **bug** label:
```markdown
**Bug Description:**
Brief description of the issue

**Steps to Reproduce:**
1. Go to frontend
2. Click on recommendations
3. See error

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: Windows 10
- Docker Version: 4.15.0
- Browser: Chrome 120
```

### ✨ Feature Requests
Use GitHub Issues with the **enhancement** label:
```markdown
**Feature Description:**
Clear description of the proposed feature

**Use Case:**
Why is this feature needed?

**Implementation Ideas:**
Suggested approach (optional)

**Additional Context:**
Screenshots, mockups, etc.
```

### 🔧 Code Contributions
Follow this workflow:
1. **Check existing issues** or create a new one
2. **Fork and clone** the repository
3. **Create feature branch** from main
4. **Make changes** following our standards
5. **Add tests** for new functionality
6. **Update documentation** as needed
7. **Submit pull request** with clear description

## 🛠️ Development Guidelines

### Backend Development (FastAPI + Python)

#### Code Style
```python
# Use type hints everywhere
from typing import List, Optional
from pydantic import BaseModel

async def get_recommendations(
    song_id: str,
    limit: int = 10,
    cluster_id: Optional[int] = None
) -> List[Song]:
    """Get song recommendations based on similarity.
    
    Args:
        song_id: Spotify track ID
        limit: Maximum number of recommendations
        cluster_id: Optional cluster filter
        
    Returns:
        List of recommended songs
        
    Raises:
        ValueError: If song_id is invalid
    """
    pass
```

#### Code Standards
- **Type hints**: Required for all functions
- **Docstrings**: Google style for all public functions
- **Error handling**: Proper exception handling with meaningful messages
- **Async/await**: Use async patterns for database operations
- **Logging**: Use structured logging with appropriate levels

#### Database Guidelines
```python
# Use proper database patterns
async def get_song_by_id(song_id: str) -> Optional[Song]:
    async with get_database() as db:
        query = "SELECT * FROM tracks WHERE id = $1"
        result = await db.fetchrow(query, song_id)
        return Song(**result) if result else None
```

### Frontend Development (React + TypeScript)

#### Code Style
```typescript
// Use proper TypeScript interfaces
interface Song {
  id: string;
  name: string;
  artist: string;
  popularity: number;
  audioFeatures?: AudioFeatures;
}

// Functional components with hooks
const SongCard: React.FC<{ song: Song; onPlay: (id: string) => void }> = ({
  song,
  onPlay
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  
  return (
    <div className="song-card">
      {/* Component JSX */}
    </div>
  );
};
```

#### React Standards
- **Functional components**: Use hooks instead of class components
- **TypeScript**: Strict typing for all props and state
- **CSS Modules/Tailwind**: Consistent styling approach
- **Error boundaries**: Handle component errors gracefully
- **Accessibility**: ARIA labels and keyboard navigation

### Machine Learning Guidelines

#### Model Development
```python
# Clear model training pipeline
class ModelTrainer:
    def __init__(self, config: TrainingConfig):
        self.config = config
        
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare features for model training."""
        # Feature engineering with clear steps
        pass
        
    def train_clustering_model(self, features: np.ndarray) -> HDBSCAN:
        """Train HDBSCAN clustering model."""
        model = HDBSCAN(
            min_cluster_size=self.config.min_cluster_size,
            metric='euclidean'
        )
        return model.fit(features)
```

#### ML Standards
- **Reproducibility**: Set random seeds and document parameters
- **Validation**: Cross-validation and proper evaluation metrics
- **Documentation**: Clear explanation of model choices
- **Performance**: Monitor training time and memory usage

## 🧪 Testing Requirements

### Backend Testing
```python
# API endpoint tests
import pytest
from fastapi.testclient import TestClient

def test_get_recommendations(client: TestClient):
    """Test recommendation endpoint."""
    response = client.post(
        "/api/v2/recommendations",
        json={"song_ids": ["test_id"], "limit": 5}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) <= 5
```

### Frontend Testing
```typescript
// Component tests with React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import SongCard from './SongCard';

test('plays song when play button clicked', () => {
  const mockOnPlay = jest.fn();
  const song = { id: '1', name: 'Test Song', artist: 'Test Artist' };
  
  render(<SongCard song={song} onPlay={mockOnPlay} />);
  
  fireEvent.click(screen.getByRole('button', { name: /play/i }));
  expect(mockOnPlay).toHaveBeenCalledWith('1');
});
```

### Test Categories
- **Unit Tests**: Individual functions and components
- **Integration Tests**: API endpoints and database operations
- **E2E Tests**: Full user workflows
- **Performance Tests**: Response times and load testing

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e

# All tests
npm run test:all
```

## 📚 Documentation Standards

### Code Documentation
- **README files**: Clear setup and usage instructions
- **API documentation**: OpenAPI/Swagger specs
- **Inline comments**: Explain complex logic, not obvious code
- **Architecture docs**: System design and data flow

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/):
```bash
# Format: type(scope): description
feat(api): add song similarity endpoint
fix(frontend): resolve audio player state bug
docs(readme): update setup instructions
test(backend): add recommendation algorithm tests
refactor(database): optimize query performance
```

## 🔄 Pull Request Process

### PR Template
```markdown
## 📝 Description
Brief description of changes

## 🎯 Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## 🧪 Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## 📋 Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings or errors
```

### Review Process
1. **Automated checks**: CI/CD pipeline must pass
2. **Code review**: At least one maintainer approval
3. **Testing**: All tests must pass
4. **Documentation**: Updates must be included
5. **Merge**: Squash and merge to main branch

## 🌟 Code Review Guidelines

### For Authors
- **Small PRs**: Keep changes focused and manageable
- **Clear description**: Explain what and why
- **Self-review**: Check your own code first
- **Tests included**: Cover new functionality
- **Documentation**: Update relevant docs

### For Reviewers
- **Be constructive**: Suggest improvements, don't just criticize
- **Ask questions**: If something isn't clear
- **Check functionality**: Does it work as intended?
- **Consider impact**: How does this affect other parts?
- **Approve**: When ready, approve and merge

## 📊 Performance Considerations

### Backend Performance
- **Database queries**: Use indexes and avoid N+1 queries
- **Caching**: Implement caching for expensive operations
- **Async operations**: Use async/await for I/O operations
- **Memory usage**: Monitor memory consumption in ML operations

### Frontend Performance
- **Bundle size**: Keep JavaScript bundles small
- **Lazy loading**: Load components and data on demand
- **Caching**: Cache API responses appropriately
- **Rendering**: Optimize re-renders with React.memo

### ML Performance
- **Training time**: Efficient algorithms and data structures
- **Inference speed**: Fast recommendation generation
- **Memory usage**: Handle large datasets efficiently
- **Model size**: Balance accuracy and deployment size

## 🔒 Security Guidelines

### API Security
- **Input validation**: Validate all user inputs
- **SQL injection**: Use parameterized queries
- **Authentication**: Implement proper auth if needed
- **Rate limiting**: Prevent abuse

### Data Privacy
- **Minimal data**: Only collect necessary data
- **Data encryption**: Encrypt sensitive information
- **Access control**: Limit data access
- **Compliance**: Follow relevant privacy laws

## 🚀 Release Process

### Version Management
- **Semantic versioning**: MAJOR.MINOR.PATCH
- **Release notes**: Document changes and breaking changes
- **Migration guides**: Help users upgrade
- **Deprecation notices**: Warn before removing features

### Deployment
- **Staging environment**: Test before production
- **Rollback plan**: Be ready to revert if needed
- **Monitoring**: Watch metrics after deployment
- **Communication**: Notify users of changes

## 🎓 Learning Resources

### Technologies Used
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://reactjs.org/docs/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **HDBSCAN**: https://hdbscan.readthedocs.io/
- **Docker**: https://docs.docker.com/

### Best Practices
- **Clean Code**: Robert Martin's principles
- **API Design**: RESTful design patterns
- **React Patterns**: Modern React development
- **Database Design**: Normalization and indexing
- **Testing**: Test-driven development

## 🤝 Community

### Communication
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and ideas
- **Pull Requests**: Code contributions
- **Code Reviews**: Collaborative improvement

### Recognition
Contributors will be recognized in:
- **README**: Contributors section
- **Release notes**: Major contributions
- **GitHub**: Contributor statistics
- **Documentation**: Author credits

## 📞 Getting Help

### Development Issues
1. **Check documentation**: README and setup guides
2. **Search issues**: Look for existing solutions
3. **Create issue**: Describe your problem clearly
4. **Join discussions**: Ask questions in GitHub Discussions

### Contact Maintainers
- **GitHub Issues**: Public discussions
- **GitHub Discussions**: Q&A and ideas
- **Pull Request reviews**: Code feedback

---

**🎵 Thank you for contributing to the future of music discovery!** 🎵

*Together, we're building an amazing AI-powered music recommendation system that helps people discover their next favorite songs.* 