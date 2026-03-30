# Implementation Plan - Phase 3: Multi-tenant Cloud Lab

This plan outlines the transition from a local, single-user lab to a centralized, multi-tenant cloud-hosted environment. The goal is to allow multiple participants to run the lab simultaneously without needing local Docker or Python installations.

## User Review Required
- **Shared vs Separate Containers**: I recommend a shared Splunk container for all participants (easier to manage) but separate or centrally-managed Ollama resources.
- **Authentication**: Using Splunk's built-in user management with role-based search filtering.
- **Cloud Hosting**: Will require a VM (e.g., AWS EC2) or a container platform (e.g., Cisco Intersight and/or Kubernetes) to host the stack.

## Proposed Changes

### 1. Cloud Infrastructure
- **Host**: A single VPC-based Virtual Machine (Ubuntu 22.04) running the existing Docker stack.
- **Access**: 
  - Splunk Web (8000) exposed via HTTPS (Reverse Proxy + Let's Encrypt).
  - HEC API (8088) exposed for telemetry ingestion.
  - **Cloud IDE**: Integrate `code-server` (VS Code in browser) into the Docker stack so users can run Python scripts without local setup.

### 2. Splunk Multi-tenancy
- **User Creation**: 
  - Admin creates participant accounts (e.g., `user01`, `user02`).
  - Passwords distributed to participants.
- **Data Isolation**: 
  - Create a new role `lab_participant`.
  - Add search filter to the role: `user="$user$"` (This ensures users only see data they generated).
- **Dashboard Updates**:
  - Update GenAI Observability dashboards to automatically filter by the logged-in user's ID.

### 3. Application Updates (Telemetry Tagging)
#### [MODIFY] [predictive_engine.py](file:///Users/micdemar/Library/CloudStorage/OneDrive-Cisco/Predictive%20Insights/predictive_engine.py)
- Read `LAB_USER_ID` from environment variables.
- Add `"user": LAB_USER_ID` to the `metrics` dictionary.

#### [MODIFY] [agent_demo.py](file:///Users/micdemar/Library/CloudStorage/OneDrive-Cisco/Predictive%20Insights/hello_agent/agent_demo.py)
- Update `setup_splunk_telemetry` to include the user ID in the metadata/traces.

### 4. Documentation Updates
#### [MODIFY] [portability_and_remote_access.md](file:///Users/micdemar/Library/CloudStorage/OneDrive-Cisco/Predictive%20Insights/docs/portability_and_remote_access.md)
- Add "Section 3: Multi-tenant Cloud Hosting".
- Detailed instructions for instructors to set up the shared environment.

## Verification Plan
1.  **Multi-user Test**: Log in as `user01` and run the simulation. Log in as `user02` and verify that `user01`'s data is NOT visible in the dashboard.
2.  **Remote Ingestion**: Verify that a script running from a different machine can send data to the centralized HEC endpoint with the correct `user` tag.
