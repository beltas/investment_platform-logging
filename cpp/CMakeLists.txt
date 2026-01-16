cmake_minimum_required(VERSION 3.25)
project(agora_log VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Options
option(AGORA_LOG_BUILD_TESTS "Build tests" ON)
option(AGORA_LOG_BUILD_EXAMPLES "Build examples" ON)

# Allow building as subdirectory
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    set(AGORA_LOG_IS_MAIN_PROJECT TRUE)
else()
    set(AGORA_LOG_IS_MAIN_PROJECT FALSE)
    set(AGORA_LOG_BUILD_TESTS OFF CACHE BOOL "Build tests" FORCE)
    set(AGORA_LOG_BUILD_EXAMPLES OFF CACHE BOOL "Build examples" FORCE)
endif()

# Conan integration (if available)
if(EXISTS "${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
    include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
    conan_basic_setup()
endif()

# Library sources
set(AGORA_LOG_SOURCES
    src/logger.cpp
    src/config.cpp
    src/formatter.cpp
    src/context.cpp
    src/timer.cpp
    src/handlers/console.cpp
    src/handlers/file.cpp
    src/handlers/rotating_file.cpp
    src/handlers/buffered_file.cpp
)

# Create library
add_library(agora_log ${AGORA_LOG_SOURCES})
add_library(agora::log ALIAS agora_log)

target_include_directories(agora_log
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_compile_features(agora_log PUBLIC cxx_std_23)

# Find dependencies
find_package(nlohmann_json 3.11 QUIET)
if(nlohmann_json_FOUND)
    target_link_libraries(agora_log PUBLIC nlohmann_json::nlohmann_json)
endif()

find_package(spdlog 1.11 QUIET)
if(spdlog_FOUND)
    target_link_libraries(agora_log PUBLIC spdlog::spdlog)
endif()

# Compiler warnings
target_compile_options(agora_log PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:Clang>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
)

# Tests
if(AGORA_LOG_BUILD_TESTS AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/tests")
    enable_testing()
    add_subdirectory(tests)
endif()

# Examples
if(AGORA_LOG_BUILD_EXAMPLES AND EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../examples/cpp-grpc")
    add_subdirectory(../examples/cpp-grpc ${CMAKE_CURRENT_BINARY_DIR}/examples)
endif()

# Install (only if main project or explicitly requested)
if(AGORA_LOG_IS_MAIN_PROJECT)
    include(GNUInstallDirs)
    include(CMakePackageConfigHelpers)

    install(TARGETS agora_log
        EXPORT agora_log_targets
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    )

    install(DIRECTORY include/agora
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    )

    # Create and install config file
    configure_package_config_file(
        ${CMAKE_CURRENT_SOURCE_DIR}/cmake/agora_log-config.cmake.in
        ${CMAKE_CURRENT_BINARY_DIR}/agora_log-config.cmake
        INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/agora_log
    )

    write_basic_package_version_file(
        ${CMAKE_CURRENT_BINARY_DIR}/agora_log-config-version.cmake
        VERSION ${PROJECT_VERSION}
        COMPATIBILITY SameMajorVersion
    )

    install(EXPORT agora_log_targets
        FILE agora_log-targets.cmake
        NAMESPACE agora::
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/agora_log
    )

    install(FILES
        ${CMAKE_CURRENT_BINARY_DIR}/agora_log-config.cmake
        ${CMAKE_CURRENT_BINARY_DIR}/agora_log-config-version.cmake
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/agora_log
    )
endif()
