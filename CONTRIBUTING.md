# Contributing to Agora Logging Library

Thank you for your interest in contributing to the Agora Trading Platform logging library!

## Development Setup

### Python

```bash
cd python
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### C++

```bash
cd cpp
mkdir build && cd build
conan install .. --build=missing
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .
```

### JavaScript/TypeScript

```bash
cd js
npm install
npm run build
```

## Running Tests

### Python

```bash
cd python
pytest
```

### C++

```bash
cd cpp/build
ctest --output-on-failure
```

### JavaScript/TypeScript

```bash
cd js
npm test
```

## Code Style

- **Python**: Follow PEP 8, use ruff for linting
- **C++**: Follow C++ Core Guidelines, use clang-format
- **JavaScript/TypeScript**: Follow ESLint configuration

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run linting and tests
5. Submit a pull request

## Documentation

When adding new features:
- Update relevant README files
- Add usage examples
- Update API documentation
- Add entries to CHANGELOG.md

## Questions?

Open an issue for any questions or suggestions.
