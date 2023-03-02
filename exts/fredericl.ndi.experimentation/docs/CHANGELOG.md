# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.3.1] - 2023-03-02

### Added
- Fix crash when searching for dynamic textures and finding those that aren't dynamic

## [0.3.0] - 2023-03-01

### Added
- Can use a proxy feed which simulates a solid red color 1920x1080 at 30fps
- Filling dynamic texture with a default magenta color
    - Fixes frame drop when assigning a dynamic texture without pushing data to it first
- Fixes for developpers to the window management targeting hot reload

### Changed
- Menu element is now at "Window > NDI Dynamic Texture" instead of "Window > NDI > NDI Dynamic Texture"

## [0.2.0] - 2023-02-28

### Added
- Support for managing multiple NDI feeds

## [0.1.0] - 2023-02-22

### Added
- Initial version of extension
- Supports one NDI feed

