# Contributing to ZeroPhix

Thank you for your interest in contributing to ZeroPhix! We welcome bug reports, feature requests, and pull requests.

## Getting Started

### Prerequisites
- Python 3.9+
- Git
- pip or conda

### Setup Development Environment

1. **Fork and clone the repo**
```bash
git clone https://github.com/yassienshaalan/zerophix.git
cd zerophix
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install in development mode**
```bash
pip install -e ".[dev,all]"
```

4. **Verify installation**
```bash
pytest tests/
```

## Contribution Types

### Bug Reports
- Use GitHub Issues with title: `[BUG] description`
- Include:
  - Steps to reproduce
  - Expected vs actual behavior
  - Python version, OS, zerophix version
  - Minimal reproducible example

### Feature Requests
- Use GitHub Issues with title: `[FEATURE] description`
- Explain use case and expected behavior
- Link related issues

### Pull Requests
- Create feature branch: `git checkout -b feature/my-feature`
- Make focused, atomic commits
- Reference issue in PR description: `Fixes #123`

## Code Standards

### Style
- Use **black** for formatting: `black src/ tests/`
- Use **ruff** for linting: `ruff check src/ tests/`
- Type hints required for public APIs
- Maximum line length: 100 characters

### Testing
- Add tests for new features in `tests/`
- Run tests locally: `pytest -v`
- Aim for >80% coverage on new code
- Tests should be deterministic and fast

### Documentation
- Docstrings: Google-style format
- Update README.md if adding user-facing features
- Add example in `examples/` for major features
- Update REDACTION_LOGIC.md for detection/redaction changes

## Pre-Commit Checklist

Before submitting a PR:
- [ ] Code passes `black` formatting
- [ ] Code passes `ruff` linting: `ruff check --fix`
- [ ] All tests pass: `pytest`
- [ ] Type checking passes: `mypy src/zerophix` (if applicable)
- [ ] Added tests for new functionality
- [ ] Updated docstrings and comments
- [ ] Updated README.md if user-facing change
- [ ] Commit messages are clear and descriptive
- [ ] No secrets or credentials in code/commits

## PR Review Process

1. **Automated checks must pass**
   - CI/CD tests run on all PRs
   - Code owner review required
   - Status checks must be green

2. **Code Review**
   - Maintainer will review within 3-5 business days
   - Feedback will be constructive and timely
   - Changes may be requested

3. **Merge**
   - PRs merged via "Squash and merge" for clean history
   - Requires approval from code owner
   - All status checks passing

## Running Tests Locally

```bash
# All tests
pytest

# Specific test file
pytest tests/test_basic.py

# With coverage
pytest --cov=src/zerophix --cov-report=html

# Specific test
pytest tests/test_basic.py::test_function_name -v
```

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Respect confidentiality of security issues
- Report violations to maintainers

## Legal

- By submitting a PR, you agree to license your contribution under the Apache-2.0 license
- Ensure you have rights to the code you're contributing

## Questions?

- Open a GitHub Discussion
- Check existing issues and discussions
- Email maintainers for security concerns

## Maintainer Guidelines

Code owners review all PRs. Focus on:
- Correctness and security
- Consistency with codebase
- Performance implications
- Test coverage
- Documentation completeness

---

**Happy contributing! 🚀**
