# Lab Portability & Remote Access Guide

This document explains how to move the **Digital Twin: Predictive Insights** lab to a new machine and how to open it up for remote users.

## 1. Portability: Running on a New Machine

To ensure the lab behaves the same way on a different computer, follow these steps:

### Prerequisites
- **Docker & Docker Compose**: Installed and running.
- **Python 3.9+**: For running the predictive engine locally.
- **Hardware**: At least 8GB RAM (16GB recommended for Ollama/Llama3).

> [!CAUTION]
> **Permission Pitfall (Cloud Sync)**: Do NOT run this lab inside a folder synced by **OneDrive, Dropbox, or iCloud**. Docker volumes mounted from these locations often suffer from "Permission Denied" errors because the cloud provider and Docker fight over file ownership.

### Step-by-Step Migration
1.  **Transfer the Directory**: Copy the entire `Predictive Insights` folder to the target machine.
    *   **Best Practice**: Place the folder in a local, non-synced directory (e.g., `~/Documents/Lab/` or `/Users/YourUser/Lab/`).
2.  **Initialize Environment**:
    ```bash
    cd "Predictive Insights"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Start Infrastructure**:
    ```bash
    docker-compose up -d
    ```
4.  **Pull AI Model**:
    ```bash
    docker exec -it ollama ollama pull llama3
    ```
5.  **Ollama Connectivity**:
    *   The lab expects Ollama at `localhost:11434`.
    *   If you see connection errors on your host terminal, ensure `OLLAMA_HOST` is either unset or set to `127.0.0.1:11434`.
    *   **Fix**: `unset OLLAMA_HOST` before running the Python scripts.
6.  **Run Engines**:
    - Start the telemetry producer (if using Docker, it starts automatically).
    - Run the predictive engine: `python predictive_engine.py`.

---

## 2. Remote Access: Opening the Lab to Users

To allow other users to access your Splunk dashboards and the Predictive Insights lab remotely, use one of the following methods:

### Method A: Local Network Access (Easiest)
If users are on the same WiFi/VPN:
1.  Find your Local IP: `ifconfig | grep "inet "` (macOS).
2.  Users can access Splunk at `http://<YOUR_IP>:8000`.
3.  **Security Note**: Change the Splunk admin password from `ChangedPassword123` to something unique.

### Method B: Secure Tunneling (ngrok/Cloudflare)
If you want to expose the lab over the internet without modifying router settings:
1.  **Install ngrok**: `brew install ngrok`.
2.  **Expose Splunk**: `ngrok http 8000`.
3.  **Provide the URL**: Share the generated `https://xxxx.ngrok-free.app` link.
    > [!WARNING]
    > Monitoring telemetry and AI logs over a public tunnel should only be done for demos. Do not use for production data.

### Method C: Tailscale (Recommended for Private Access)
1.  Install **Tailscale** on your machine and the remote user's machine.
2.  Your machine will get a private "MagicDNS" name (e.g., `my-mac.tailscale.net`).
3.  Users can access the lab at `http://my-mac.tailscale.net:8000` from anywhere in the world securely.

### Method D: Exposing Ollama (Advanced)
If you want users to run their *own* predictive engines against your local Ollama:
1.  Update `docker-compose.yml` to bind Ollama to `0.0.0.0`:
    ```yaml
    ollama:
      ports:
        - "0.0.0.0:11434:11434"
    ```
2.  Users set their `OLLAMA_URL` environment variable to `http://<YOUR_IP>:11434/api/generate`.

---

## 3. Multi-tenant Cloud Lab Hosting (Zero-Footprint)

For large-scale workshops or environments where users cannot run Docker locally, the lab can be hosted centrally. This approach prioritizes **Lab Experience** and **Data Isolation**.

### Architecture Overview
1.  **Central VM**: One high-spec VM (e.g., 32GB RAM, 16 vCPUs) hosting the entire Docker stack.
2.  **Shared Splunk**: A single Splunk instance with dedicated user accounts for each participant.
3.  **Cloud IDE (Optional)**: Integrate `code-server` (VS Code in browser) so users can run the Python scripts without any local setup.

### Splunk Multi-tenancy Setup

#### 1. User Management
Instructors should pre-create participant accounts:
- **Path**: `Settings > Users`
- **Naming**: `participant01`, `participant02`, etc.
- **Roles**: Create a custom `lab_participant` role and assign it to these users.

#### 2. Data Isolation (Role-Based Search Filters)
To prevent participants from seeing each other's traces in the shared dashboards:
1.  Go to `Settings > Roles > lab_participant`.
2.  In the **Search Filter** box, add: `user="$user$"`
3.  **How it works**: Splunk automatically appends `AND user=<logged_in_user_name>` to every search, ensuring users only see their own telemetry.

### Application Integration
To support this multi-tenant isolation, the agentic scripts must tag their data:

#### **Predictive Engine Configuration**
Users set an environment variable before running:
```bash
export LAB_USER_ID="participant01"
python3 predictive_engine.py
```

#### **The MCP Component**
The **Splunk MCP Server** (`splunk_mcp/mcp_server.py`) is the "Translator" for the lab. It acts as a gateway that allows AI agents (like Claude) to query Splunk index data using plain English. In a multi-tenant setup, this component ensures that even natural language queries are scoped to the correct user.

There are two ways to solve for this in a shared lab:

**Option A: The Cloud IDE (Recommended - Zero Footprint)**
Participants use the browser-based Web IDE provided by the lab.
1.  Open the terminal in the Web IDE.
2.  **Splunk AI Analyst CLI**: Run `python3 splunk_agent.py "report status"`.
3.  **Aha! Moment**: Watch as the agent translates natural language into SPL, searches Splunk, and provides a structured health report (matching the premium "Claude Code" experience).
4.  **Benefit**: No installation (Claude or Docker) required.

**Option B: The Manual Export (The "Aha!" Moment)**
If participants want to use **Claude Desktop** locally:
1.  **Download Claude**: Participants must download Claude Desktop before the lab.
2.  **Tunnel to MCP**: Use Tailscale to reach the Mac mini's MCP server.
3.  **Configure**: Participants add the remote MCP server to their `claude_desktop_config.json`:
    ```json
    "mcpServers": {
      "splunk": {
        "command": "ssh",
        "args": ["-t", "participant01@lab-mac-mini.tailscale.net", "source /path/to/venv/bin/activate && python3 /path/to/mcp_server.py"],
        "env": { "LAB_USER_ID": "participant01" }
      }
    }
    ```
4.  **Benefit**: Participants experience the premium "Agency" flow directly in their desktop app.

### Instructor Checklist for Cloud Deployment
- [ ] **Infrastructure**: Deploy VM to AWS/Azure/Cisco Intersight.
- [ ] **SSL**: Use Nginx + Let's Encrypt for `https://splunk.yourlab.com`.
- [ ] **Ollama**: Pre-pull `llama3` and ensure the API is reachable over the private VPC.
- [ ] **Account Provisioning**: Generate a list of login credentials for the classroom.

---

## 4. Permanent Lab Hosting: Mac mini + Tailscale

A high-performance **Mac mini (M2/M3)** is the ideal "Permanent Lab" host. It provides the necessary power for Ollama while maintaining a small physical footprint and silent operation. Combining this with **Tailscale** creates a secure, zero-config "Lab-in-a-Box."

### Why this Configuration?
- **Always-On**: The Mac mini can run 24/7 in a lab closet or under a desk.
- **Apple Silicon Performance**: The M-series chips are exceptionally efficient at running LLMs like Llama3 via Ollama.
- **Secure Mesh Networking**: Tailscale allows users to access the lab from anywhere (even behind NAT/Firewalls) without opening public ports.

### Setup Instructions

#### 1. Prepare the Mac mini
- Install **Docker Desktop** and allocate at least 12GB of RAM to the VM.
- Install **Tailscale** and sign in.
- Enable **"Start Tailscale at Login"** and **"Always-On"** in macOS Settings.

#### 2. Configure Tailscale "MagicDNS"
- In the Tailscale Admin Console, note the **MagicDNS** name of your Mac mini (e.g., `lab-mac-mini.tailnet-name.ts.net`).
- Users will use this URL to access Splunk and the HEC endpoint.

#### 3. Start the Multi-tenant Stack
Follow the steps in [Section 3](#3-multi-tenant-cloud-lab-hosting-zero-footprint) to start the multi-tenant Docker stack.

#### 4. Participant Access
Provide participants with:
1.  **Tailscale Invitation**: Ask users to join your Tailnet (or use a shared invite link).
2.  **Splunk URL**: `http://lab-mac-mini.tailnet-name.ts.net:8000`
3.  **HEC Endpoint**: `http://lab-mac-mini.tailnet-name.ts.net:8088` (for remote agent execution).

---

## 5. Fallback: Remote Access via ngrok

If **Tailscale** is blocked by corporate policy (e.g., Cisco Umbrella), **ngrok** provides a reliable fallback for exposing the Splunk dashboard.

### Setup Instructions

1.  **Install ngrok**: `brew install --cask ngrok`
2.  **Add Authtoken**: Obtain your token from the [ngrok Dashboard](https://dashboard.ngrok.com/) and run:
    ```bash
    ngrok config add-authtoken <YOUR_TOKEN>
    ```
3.  **Start Tunnel**: Expose the **Unified Lab Gateway** (Port 80):
    ```bash
    # Secure start (highly recommended)
    ngrok http 80 --auth "admin:YourStrongPassword"
    ```
4.  **How to Stop**: `pkill ngrok`
5.  **Unified DNA Access**:
    - **Splunk Dashboard**: `https://*.ngrok-free.dev/`
    - **Cloud IDE (Web MCP)**: `https://*.ngrok-free.dev/ide/` (The trailing slash is required).

> [!TIP]
> **Premium Feel**: This setup allows all lab components to share a single public URL, providing a seamless "Portal" experience for participants.

> [!CAUTION]
> **Ephemeral URLs**: On the ngrok free tier, the public URL changes every time you restart the service. If you stop the service, you must provide your participants with a new link.

> [!TIP]
> **Subnet Routing**: For advanced labs, you can configure the Mac mini as a **Tailscale Subnet Router**. This allows participants to reach other physical hardware (like real Cisco Nexus switches) in your lab through the Tailscale tunnel.
