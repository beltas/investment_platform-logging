# Try to find Catch2 locally first, otherwise use FetchContent
find_package(Catch2 3 QUIET)

if(NOT Catch2_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        Catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG        v3.4.0
    )
    FetchContent_MakeAvailable(Catch2)
    list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
endif()

add_executable(agora_log_tests
    test_logger.cpp
    test_handlers.cpp
    test_rotation.cpp
    test_formatter.cpp
    test_config.cpp
)

target_link_libraries(agora_log_tests
    PRIVATE
        agora_log
        Catch2::Catch2WithMain
)

# Enable all warnings
target_compile_options(agora_log_tests PRIVATE
    $<$<CXX_COMPILER_ID:GNU>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:Clang>:-Wall -Wextra -Wpedantic>
    $<$<CXX_COMPILER_ID:MSVC>:/W4>
)

include(Catch)
catch_discover_tests(agora_log_tests)
