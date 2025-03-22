# Add OpenFace-specific CMAKE_MODULE_PATH
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../OpenFace/cmake/modules")

# Minimum required cmake version and C++ standard
cmake_minimum_required (VERSION 3.8)
set(CMAKE_CXX_STANDARD 17)

# Project details
project(FairTalk VERSION 1.0)

# Include OpenFace subdirectory
add_subdirectory(../OpenFace)

# Gather all OpenFace targets
get_property(openface_targets DIRECTORY ../OpenFace PROPERTY BUILDSYSTEM_TARGETS)

# Explicitly define the targets to be included from OpenFace
set(my_openface_targets Utilities)

# Include OpenFace-specific paths
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../OpenFace/lib/local/LandmarkDetector/include)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../OpenFace/lib/local/FaceAnalyser/include)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../OpenFace/lib/local/GazeAnalyser/include)

# Define the custom FeatureExtraction target
add_executable(myFeatureExtraction "custom-FeatureExtraction/FeatureExtraction.cpp")

# Define the output directory
set_target_properties(myFeatureExtraction PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin/)

# Link OpenFace libraries to the target
foreach(target ${my_openface_targets})
    target_link_libraries(myFeatureExtraction ${target})
endforeach()

# Link specific libraries to the FeatureExtraction target
target_link_libraries(myFeatureExtraction LandmarkDetector)
target_link_libraries(myFeatureExtraction FaceAnalyser)
target_link_libraries(myFeatureExtraction GazeAnalyser)
target_link_libraries(myFeatureExtraction Utilities)
