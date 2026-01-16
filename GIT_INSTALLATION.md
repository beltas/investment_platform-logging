# Quick Reference: Git-Based Installation

This repository is configured for direct Git-based installation across all three languages.

## Quick Commands

### Python
```bash
# Latest from main branch
pip install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=python

# Specific version
pip install git+ssh://git@github.com/agora/investment_platform-logging.git@v0.1.0#subdirectory=python

# Local editable install
pip install -e /path/to/investment_platform-logging/python
```

### JavaScript/TypeScript
```bash
# From Git (limited subdirectory support)
npm install git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js

# Recommended: Local development with npm link
cd /path/to/investment_platform-logging/js
npm link
cd /path/to/your/project
npm link @agora/logger
```

### C++
```cmake
# CMake FetchContent (recommended)
FetchContent_Declare(
  agora_log
  GIT_REPOSITORY git@github.com:agora/investment_platform-logging.git
  GIT_TAG main
  SOURCE_SUBDIR cpp
)
FetchContent_MakeAvailable(agora_log)
target_link_libraries(my_service PRIVATE agora::log)
```

## Configuration Files

### Python: requirements.txt
```txt
agora-log @ git+ssh://git@github.com/agora/investment_platform-logging.git@v0.1.0#subdirectory=python
```

### JavaScript: package.json
```json
{
  "dependencies": {
    "@agora/logger": "git+ssh://git@github.com/agora/investment_platform-logging.git#subdirectory=js"
  }
}
```

### C++: CMakeLists.txt
```cmake
include(FetchContent)
FetchContent_Declare(
  agora_log
  GIT_REPOSITORY git@github.com:agora/investment_platform-logging.git
  GIT_TAG v0.1.0
  SOURCE_SUBDIR cpp
)
FetchContent_MakeAvailable(agora_log)
```

## Full Documentation

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for:
- Complete installation instructions
- Troubleshooting guide
- Docker and CI/CD examples
- Version pinning strategies
- Local development setup

## Testing Your Installation

### Python
```bash
python -c "from agora_log import initialize, get_logger; print('Success!')"
```

### JavaScript
```bash
node -e "const { initialize } = require('@agora/logger'); console.log('Success!');"
```

### C++
```cpp
#include <agora/log/logger.hpp>
auto logger = agora::log::get_logger("test");
```

## Repository Structure

```
investment_platform-logging/
├── python/           # Python package (pip installable)
├── cpp/              # C++ library (CMake FetchContent)
├── js/               # JavaScript/TypeScript package (npm)
├── docs/
│   └── INSTALLATION.md  # Complete installation guide
└── examples/         # Integration examples
```

## Notes

- Replace `agora` with your actual GitHub organization name
- Push tags for version-specific installations: `git tag v0.1.0 && git push origin v0.1.0`
- Python subdirectory installation requires pip 19.0+
- npm subdirectory support is limited; use npm link for local development
- C++ uses CMake FetchContent with SOURCE_SUBDIR for clean integration
