# ZooProcess-python Requirements

## Overview
ZooProcess-python is a REST API designed to pilot the Ecotaxa pipelines for processing plankton images. The system provides functionality for separating multiple plankton organisms from images, processing scans, managing backgrounds, and importing projects.

## Core Goals
1. Provide a REST API for interacting with Ecotaxa pipelines
2. Enable separation of multiple plankton organisms from images
3. Process scans with background removal and segmentation
4. Support image format conversion
5. Manage project data and metadata
6. Track task status and progress
7. Integrate with external services for image processing

## Functional Requirements

### Image Processing
- Convert images between formats (TIFF to JPEG)
- Process scans by removing backgrounds
- Segment images to identify individual plankton organisms
- Generate masks for separating plankton organisms
- Apply masks to separate plankton organisms from backgrounds
- Create medium backgrounds from multiple background scans

### Project Management
- Import projects from existing sources
- Manage project metadata (name, description, etc.)
- Associate projects with instruments
- Link projects to Ecotaxa projects

### Task Management
- Track task status (RUNNING, FINISHED, FAILED)
- Report task progress
- Handle task errors
- Associate processed images with tasks

### API Integration
- Integrate with external separation services
- Communicate with database servers
- Support authentication via bearer tokens
- Handle cross-origin requests

## Technical Constraints
- Must work with existing Ecotaxa infrastructure
- Must handle large image files efficiently
- Must support various image formats (TIFF, JPEG, PNG, GIF)
- Must provide proper error handling and status reporting
- Must be deployable in Docker containers
- Must be accessible through standard HTTP requests

## Performance Requirements
- Process images in a reasonable time frame
- Handle multiple concurrent requests
- Efficiently manage memory when processing large images

## Security Requirements
- Authenticate users via bearer tokens
- Validate input data
- Protect against unauthorized access

## Integration Requirements
- Integrate with Ecotaxa database
- Communicate with separation services
- Support file system operations for image storage and retrieval