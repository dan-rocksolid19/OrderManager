# JobManager Application

A LibreOffice extension for managing jobs, quotes, and invoices.

## Architecture Overview

The JobManager application follows a strict initialization sequence to ensure reliable startup and proper resource management.

### Boot Sequence

1. **Environment Checks**
   - Database connectivity and migrations
   - Authentication system readiness
   - No UI elements are created until checks pass

2. **Frame Manager**
   - Creates main application window (hidden)
   - Handles window events and geometry

3. **UI Initialization**
   - Creates sidebar (hidden initially)
   - Prepares component containers
   - Loads login component

4. **Post-Login**
   - Shows sidebar
   - Creates menubar/toolbar
   - Switches to main UI (job list view)

### Component Lifecycle

The application enforces strict component lifecycle rules:

1. **Creation**
   - Components are created on-demand
   - No component caching
   - Each component gets a dedicated container

2. **Disposal**
   - Components are fully disposed when switching views
   - Resources are cleaned up immediately
   - Containers are managed by the sidebar

3. **Visibility**
   - Components control their own visibility
   - Sidebar manages container visibility
   - Clean transitions between components

### Key Classes

- `AppBootstrap`: Manages application startup sequence
- `UIInitializer`: Handles UI component initialization
- `ComponentManager`: Controls component lifecycle
- `SidebarManager`: Manages containers and navigation
- `JobManager`: Main application coordinator

## Development

### Running Tests

```bash
python -m unittest discover source/tests
```

### Adding New Components

1. Create component class in appropriate directory
2. Add factory method to ComponentManager
3. Update sidebar configuration if needed
4. Add container management in SidebarManager

### Error Handling

- All errors are logged with full stack traces
- User-facing errors use message boxes
- Components handle their own cleanup

## Dependencies

- LibreOffice Python Runtime (bundled)
- PyBrex UI Toolkit (included)
- Standard library only (no external packages) 