# Installation Guide

This guide covers all installation methods for the Agora Trading Platform logging library across Python, C++, and JavaScript/TypeScript.

## Table of Contents

- [Python Installation](#python-installation)
- [JavaScript/TypeScript Installation](#javascripttypescript-installation)
- [C++ Installation](#c-installation)
- [Local Development Setup](#local-development-setup)
- [Troubleshooting](#troubleshooting)

---

## Python Installation

### From Git Repository (SSH)

**Install directly from the main branch:**
```bash
pip install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python
```

**Install a specific version/tag:**
```bash
pip install git+ssh://git@github.com/agora/investment_platform-logging.git@v0.1.0#subdirectory=python
```

**Install a specific branch:**
```bash
pip install git+ssh://git@github.com/agora/investment_platform-logging.git@feature-branch#subdirectory=python
```

### From Git Repository (HTTPS)

```bash
pip install git+https://github.com/agora/investment_platform-logging.git#subdirectory=python
```

### Local Editable Install

For development or when you have a local clone:

```bash
# Clone the repository
git clone git@github.com:agora/investment_platform-logging.git
cd investment_platform-logging

# Install in editable mode
pip install -e python/
```

### With Optional Dependencies

**FastAPI integration:**
```bash
pip install "git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python[fastapi]"
```

**OpenTelemetry integration:**
```bash
pip install "git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python[opentelemetry]"
```

**Development tools:**
```bash
pip install "git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python[dev]"
```

### In requirements.txt

Add to your `requirements.txt`:

```txt
# Using SSH
agora-log @ git+ssh://git@github.com/agora/investment_platform-logging.git@v0.1.0#subdirectory=python

# Using HTTPS
agora-log @ git+https://github.com/agora/investment_platform-logging.git@v0.1.0#subdirectory=python

# With optional dependencies
agora-log[fastapi] @ git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python
```

### In pyproject.toml

Add to your `pyproject.toml`:

```toml
[project]
dependencies = [
    "agora-log @ git+ssh://git@github.com/agora/investment_platform-logging.git@v0.1.0#subdirectory=python",
]

[project.optional-dependencies]
fastapi = [
    "agora-log[fastapi] @ git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python",
]
```

Or using PEP 621 format:

```toml
[tool.poetry.dependencies]
python = "^3.11"
agora-log = { git = "ssh://git@github.com/agora/investment_platform-logging.git", subdirectory = "python", tag = "v0.1.0" }
```

### Verification

```bash
# Verify installation
python -c "from agora_log import initialize, get_logger; print('agora-log installed successfully')"

# Check version
python -c "import agora_log; print(agora_log.__version__)"
```

---

## JavaScript/TypeScript Installation

### From Git Repository (SSH)

**Install directly from the main branch:**
```bash
npm install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js
```

**Install a specific version/tag:**
```bash
npm install "agora/investment_platform-logging#semver:v0.1.0"
```

### From Git Repository (HTTPS)

```bash
npm install git+https://github.com/agora/investment_platform-logging.git#subdirectory=js
```

### Local Install

For development or when you have a local clone:

```bash
# Clone the repository
git clone git@github.com:agora/investment_platform-logging.git
cd investment_platform-logging

# Install from local path
npm install /path/to/investment_platform-logging/js

# Or use npm link for development
cd js
npm link
cd /path/to/your/project
npm link @agora/logger
```

### In package.json

Add to your `package.json`:

```json
{
  "dependencies": {
    "@agora/logger": "git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js"
  }
}
```

Or with a specific version:

```json
{
  "dependencies": {
    "@agora/logger": "github:agora/investment_platform-logging#semver:v0.1.0"
  }
}
```

### Yarn Installation

```bash
# Yarn v1
yarn add git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js

# Yarn v2+
yarn add @agora/logger@github:agora/investment_platform-logging#workspace=js&commit=main
```

### pnpm Installation

```bash
pnpm add git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js
```

### Verification

```bash
# Verify installation
node -e "const { initialize } = require('@agora/logger'); console.log('Logger installed successfully')"

# TypeScript verification
npx ts-node -e "import { initialize } from '@agora/logger'; console.log('Logger installed')"
```

---

## C++ Installation

### Using CMake FetchContent

Add to your `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.25)
project(my_service)

include(FetchContent)

# Fetch agora_log from Git
FetchContent_Declare(
  agora_log
  GIT_REPOSITORY git@github.com:agora/investment_platform-logging.git
  GIT_TAG main
  SOURCE_SUBDIR cpp
)

FetchContent_MakeAvailable(agora_log)

# Your executable
add_executable(my_service src/main.cpp)

# Link against agora_log
target_link_libraries(my_service PRIVATE agora::log)
```

**Using a specific version:**
```cmake
FetchContent_Declare(
  agora_log
  GIT_REPOSITORY git@github.com:agora/investment_platform-logging.git
  GIT_TAG v0.1.0
  SOURCE_SUBDIR cpp
)
```

**Using HTTPS:**
```cmake
FetchContent_Declare(
  agora_log
  GIT_REPOSITORY https://github.com/agora/investment_platform-logging.git
  GIT_TAG main
  SOURCE_SUBDIR cpp
)
```

### Using Git Submodule

```bash
# Add as submodule
git submodule add git@github.com:agora/investment_platform-logging.git external/investment_platform-logging
git submodule update --init --recursive
```

In your `CMakeLists.txt`:

```cmake
# Add subdirectory
add_subdirectory(external/investment_platform-logging/cpp)

# Link against the library
target_link_libraries(my_service PRIVATE agora::log)
```

### Manual Installation

```bash
# Clone the repository
git clone git@github.com:agora/investment_platform-logging.git
cd investment_platform-logging/cpp

# Install dependencies with Conan
conan install . --build=missing

# Build and install
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local
cmake --build . -j$(nproc)
sudo cmake --install .
```

Then use `find_package` in your project:

```cmake
find_package(agora_log REQUIRED)
target_link_libraries(my_service PRIVATE agora::log)
```

### Using Conan Package

If you publish to a Conan repository:

**conanfile.txt:**
```ini
[requires]
agora_log/0.1.0

[generators]
cmake
```

**CMakeLists.txt:**
```cmake
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

target_link_libraries(my_service PRIVATE ${CONAN_LIBS})
```

### Verification

```bash
# Build test program
cat > test.cpp << 'EOF'
#include <agora/log/logger.hpp>
int main() {
    auto logger = agora::log::get_logger("test");
    logger.info("Logger installed successfully");
    return 0;
}
EOF

g++ -std=c++23 test.cpp -lagora_log -o test
./test
```

---

## Local Development Setup

### Clone Repository

```bash
# SSH
git clone git@github.com:agora/investment_platform-logging.git
cd investment_platform-logging

# HTTPS
git clone https://github.com/agora/investment_platform-logging.git
cd investment_platform-logging
```

### Python Development

```bash
cd python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/agora_log

# Linting
ruff check src/
```

### JavaScript/TypeScript Development

```bash
cd js

# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test

# Type checking
npm run typecheck

# Linting
npm run lint
```

### C++ Development

```bash
cd cpp

# Install dependencies
conan install . --build=missing

# Build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build . -j$(nproc)

# Run tests
ctest --output-on-failure
```

### Running Examples

Each language has example projects in the `examples/` directory:

```bash
# Python FastAPI example
cd examples/python-fastapi
pip install -r requirements.txt
uvicorn main:app --reload

# Node.js NestJS example
cd examples/nodejs-nestjs
npm install
npm run start:dev

# C++ gRPC example
cd examples/cpp-grpc
mkdir build && cd build
cmake ..
cmake --build .
./portfolio_service
```

---

## Troubleshooting

### Python Issues

**Issue: `pip install` fails with "subdirectory not found"**

Solution: Ensure you're using pip 19.0+ which supports the `#subdirectory` syntax:
```bash
pip install --upgrade pip
```

**Issue: Import error after installation**

Solution: Verify the package is installed:
```bash
pip list | grep agora-log
pip show agora-log
```

**Issue: Editable install doesn't reflect changes**

Solution: Reinstall in editable mode:
```bash
pip install -e python/ --force-reinstall --no-deps
```

### JavaScript Issues

**Issue: `npm install` hangs or fails**

Solution: Clear npm cache and retry:
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Issue: TypeScript compilation errors**

Solution: Ensure `prepare` script runs on install:
```bash
npm rebuild @agora/logger
```

**Issue: Module not found errors**

Solution: Verify the installation:
```bash
npm ls @agora/logger
cat node_modules/@agora/logger/package.json
```

**Issue: Git subdirectory installation not working**

Solution: npm doesn't natively support subdirectories well. Use a local path or npm link:
```bash
# Clone and link
git clone git@github.com:agora/investment_platform-logging.git
cd investment_platform-logging/js
npm link
cd /path/to/your/project
npm link @agora/logger
```

### C++ Issues

**Issue: CMake can't find dependencies**

Solution: Install dependencies via Conan first:
```bash
cd cpp
conan install . --build=missing
```

**Issue: FetchContent fails to fetch**

Solution: Verify Git credentials and network access:
```bash
git ls-remote git@github.com:agora/investment_platform-logging.git
```

**Issue: Build fails with "C++23 not supported"**

Solution: Use a modern compiler:
```bash
# GCC 12+ or Clang 15+
g++ --version
clang++ --version

# Update CMake
cmake --version  # Requires 3.25+
```

**Issue: Linking errors**

Solution: Ensure all dependencies are found:
```cmake
# In your CMakeLists.txt, add verbose output
set(CMAKE_FIND_DEBUG_MODE TRUE)
find_package(agora_log REQUIRED)
set(CMAKE_FIND_DEBUG_MODE FALSE)
```

### General Issues

**Issue: SSH authentication fails**

Solution: Set up SSH keys for GitHub:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Add public key to GitHub
cat ~/.ssh/id_ed25519.pub
# Copy and paste to GitHub Settings > SSH Keys
```

**Issue: HTTPS authentication required**

Solution: Use personal access token or switch to SSH:
```bash
# Use SSH instead
git remote set-url origin git@github.com:agora/investment_platform-logging.git
```

**Issue: Version conflicts**

Solution: Pin to a specific commit or tag:
```bash
# Python
pip install "git+ssh://git@github.com/agora/investment_platform-logging.git@abc123#subdirectory=python"

# npm
npm install "github:agora/investment_platform-logging#abc123"

# CMake
FetchContent_Declare(agora_log GIT_TAG abc123 ...)
```

---

## Environment-Specific Notes

### Docker Installations

**Python Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install from Git (requires SSH keys or HTTPS)
RUN pip install git+https://github.com/agora/investment_platform-logging.git#subdirectory=python

# Or copy local directory
COPY investment_platform-logging/python /tmp/agora-log
RUN pip install /tmp/agora-log && rm -rf /tmp/agora-log
```

**Node.js Dockerfile:**
```dockerfile
FROM node:18-alpine

# Install from Git
RUN npm install git+https://github.com/agora/investment_platform-logging.git#subdirectory=js

# Or copy local directory
COPY investment_platform-logging/js /tmp/logger
RUN npm install /tmp/logger && rm -rf /tmp/logger
```

**C++ Dockerfile:**
```dockerfile
FROM ubuntu:22.04

# Install build tools
RUN apt-get update && apt-get install -y cmake g++ git

# FetchContent will download during build
COPY CMakeLists.txt /app/
WORKDIR /app
RUN cmake -B build && cmake --build build
```

### CI/CD Integration

**GitHub Actions:**
```yaml
- name: Install Python dependencies
  run: |
    pip install git+https://github.com/agora/investment_platform-logging.git#subdirectory=python

- name: Install Node.js dependencies
  run: |
    npm install git+https://github.com/agora/investment_platform-logging.git#subdirectory=js

- name: Build C++ project
  run: |
    cmake -B build -DAGORA_LOG_GIT_TAG=main
    cmake --build build
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/agora/investment_platform-logging/issues
- Documentation: https://github.com/agora/investment_platform-logging/tree/main/docs
- Email: team@agora.example.com
