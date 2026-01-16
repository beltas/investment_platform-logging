# C++ gRPC Example

Example gRPC server using libagora_log.

## Build

```bash
mkdir build && cd build
conan install .. --build=missing
cmake ..
cmake --build .
```

## Run

```bash
./grpc_example_server
```

## Files

- `main.cpp` - gRPC server with logging
- `CMakeLists.txt` - Build configuration
