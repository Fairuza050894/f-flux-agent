# QA Dashboard Frontend V3

## Structure

### router
Application route configuration.

### layouts
Shared application layouts such as the dashboard shell.

### pages
Top-level application pages:
- Main Dashboard
- UI Testing
- API Testing
- Regression Testing
- Test Planning
- History

### stores
Zustand stores for workspace, draft, and execution state.

### services
Frontend API services for FastAPI endpoints.

### components
Reusable UI components such as sidebar, header, cards, and form fields.

### styles
Global styles, design tokens, layouts, and component styles.

## State ownership

### UI state
Stored in the frontend workspace store.

### Draft state
Stored in Zustand with browser persistence.

### Execution state
Stored in the FastAPI execution store and retrieved by run ID or project ID.
