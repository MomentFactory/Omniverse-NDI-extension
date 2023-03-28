# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.8.1] - 2023-03-29

### Changed
- Dedicated NDI threads no longer daemonic

### Fixed
- Stream UI did not go back to its non running state when using the button "kill all streams"
- Order of calls on application shutdown that could cause a crash on hot reload (affected developers)
- Status of NDI source not properly reflected in the icons

## [0.8.0] - 2023-03-27

### Added
- Profiling in NDI stream functions

### Changed
- When a stream is running, it is no longer possible to change its source, display a running status instead

### Fixed
- Selected NDI source in combobox doesn't change when wources are updated
- Make name USD safe when creating new material instead of throwing error
- NDI status icon goes back to valid if a NDI source is started after being closed
- Won't attempt to start a stream if it isn't valid (i.e. can't find the source)

## [0.7.0] - 2023-03-21

### Fixed
- Removed the parts of the extension that caused the app to freeze. Might still encounter low fps during the following:
    - Starting a stream
    - Closing a NDI® source while the stream is still running in the extension
    - Using Remote Connection 1 or proxy as a stream source

## [0.6.0] - 2023-03-16

### Changed
- Stream Optimization (no need to flatten the NDI® frame)
- Individual streams now run in different thread
- Removed refresh NDI® feed button in favor of a watcher that runs on a second thread
- If a NDI® source closes while the stream is still running in the extension, it will automatically stop after a few seconds (5)

### Fixed
- Extension is now know as mf.ov.ndi
- Omniverse app won't crash when the NDI® source is closed and a stream is still running
    - The app will still freeze for a few seconds

## [0.5.0] - 2023-03-07

### Added
- Support for receiving the low bandwidth version of a NDI® stream (this is a feature of NDI® that we now support)

## [0.4.0] - 2023-03-03

### Added
- Support for dynamic rect light (works when `IsProjector` is enabled to simulate a projector)

### Changed
- Now uses the [recommended logging](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/logging.html) system

### Removed
- Obsolete pip dependency to open-cv

## [0.3.1] - 2023-03-02

### Fixed
- Crash when searching for dynamic textures and finding those that aren't dynamic

## [0.3.0] - 2023-03-01

### Added
- Can use a proxy feed which simulates a solid red color 1920x1080 at 30fps

## Fixed
- Filling dynamic texture with a default magenta color
    - Fixes frame drop when assigning a dynamic texture without pushing data to it first
- Fixes for developpers to the window management targeting hot reload

### Changed
- Menu element is now at "Window > NDI® Dynamic Texture" instead of "Window > NDI® > NDI® Dynamic Texture"

## [0.2.0] - 2023-02-28

### Added
- Support for managing multiple NDI® feeds

## [0.1.0] - 2023-02-22

### Added
- Initial version of extension
- Supports one NDI® feed

