# QA Dashboard Frontend V3 Architecture

## Application Structure

### router

Contains React Router configuration for:

- Dashboard
- Test Cycles
- Test Assets
- Test Planning
- History
- Reports
- Projects
- Environments
- Integrations

### layouts

Contains the global dashboard shell:

- Sidebar
- Active project selector
- Header
- Environment status
- Backend status
- Execution status
- Main content outlet

### pages

Contains route-level screens.

#### Overview

- Main Dashboard

#### Testing

- Test Cycles
- Test Assets
- Test Planning

#### Results

- History
- Reports

#### Configuration

- Projects
- Environments
- Integrations

### stores

Zustand state ownership:

- Workspace state
- Selected project
- Selected environment
- Test cycle drafts
- UI preferences

Persistent draft state will use browser storage.

### services

Contains communication with FastAPI:

- Project service
- Environment service
- Test cycle service
- Execution service
- Report service
- Integration service

### components

Contains reusable UI components such as:

- Page headers
- Metric cards
- Status badges
- Data tables
- Filters
- Forms
- Modals
- Progress indicators

### styles

Contains:

- Design tokens
- Global styles
- Dashboard layout
- Reusable component styles

## Execution State

Execution state belongs to the FastAPI backend so an active
test cycle remains available when the user changes pages,
refreshes the browser, or opens another session.

## Test Cycle Model

One Test Cycle may contain:

- UI tests
- API tests
- Unit tests
- E2E tests
- Related regression tests

Each runner remains modular, while results are consolidated
under one cycle ID.

## Project and Environment Store

`projectEnvironmentStore.js` owns:

- Registered projects
- Registered environments
- Active project
- Active environment
- Project creation
- Environment creation
- Project updates
- Environment updates

The store uses Zustand persistence backed by browser
local storage during the MVP frontend stage.

Persistent storage key:

`qa-dashboard-project-environment-v1`

This browser persistence will later be replaced or
synchronized with the FastAPI Project Registry.

## Post-MVP API Playground

After the MVP test-cycle workflow is stable, the dashboard
will provide an API Playground under Test Assets.

Planned capabilities:

- Manual API request input
- Method, URL, path, query parameters, and headers
- Authentication and credential references
- JSON request body validation
- Direct response status, headers, body, size, and duration
- Positive and negative response assertions
- Import from cURL
- Import from Postman Collection
- Import from OpenAPI or Swagger
- Save requests as reusable API Test Assets
- Execute saved API assets inside a Test Cycle

API requests will be executed through the FastAPI backend,
not directly from the browser.
