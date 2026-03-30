# Lab Credentials & Participant Access

This document contains the login credentials for the **Digital Twin: Predictive Insights** lab. 

> [!IMPORTANT]
> **Data Isolation**: Participants must use their assigned **User ID** in their telemetry scripts to ensure they only see their own data in Splunk.

## 1. Credentials List (Total: 25)

| Role | User ID (Splunk/WebUI) | Default Password | Assigned Participant |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `ChangedPassword123` | Instructor |
| Participant | `user01` | `CiscoLab2026!` | |
| Participant | `user02` | `CiscoLab2026!` | |
| Participant | `user03` | `CiscoLab2026!` | |
| Participant | `user04` | `CiscoLab2026!` | |
| Participant | `user05` | `CiscoLab2026!` | |
| Participant | `user06` | `CiscoLab2026!` | |
| Participant | `user07` | `CiscoLab2026!` | |
| Participant | `user08` | `CiscoLab2026!` | |
| Participant | `user09` | `CiscoLab2026!` | |
| Participant | `user10` | `CiscoLab2026!` | |
| Participant | `user11` | `CiscoLab2026!` | |
| Participant | `user12` | `CiscoLab2026!` | |
| Participant | `user13` | `CiscoLab2026!` | |
| Participant | `user14` | `CiscoLab2026!` | |
| Participant | `user15` | `CiscoLab2026!` | |
| Participant | `user16` | `CiscoLab2026!` | |
| Participant | `user17` | `CiscoLab2026!` | |
| Participant | `user18` | `CiscoLab2026!` | |
| Participant | `user19` | `CiscoLab2026!` | |
| Participant | `user20` | `CiscoLab2026!` | |
| Participant | `user21` | `CiscoLab2026!` | |
| Participant | `user22` | `CiscoLab2026!` | |
| Participant | `user23` | `CiscoLab2026!` | |
| Participant | `user24` | `CiscoLab2026!` | |

## 2. Splunk Batch Creation Script

Run the following command from your host terminal to create these users in the Splunk container automatically.

```bash
# Create the 'lab_participant' role with data isolation (user="$user$")
docker exec splunk /opt/splunk/bin/splunk add role lab_participant -srchFilter 'user="$user$"' -auth admin:ChangedPassword123

# Batch create users 01-24
for i in {01..24}; do
  username="user$i"
  echo "Creating Splunk user: $username"
  docker exec splunk /opt/splunk/bin/splunk add user "$username" -password "CiscoLab2026!" -role lab_participant -auth admin:ChangedPassword123
done
```

## 4. Quick Start: Participant Onboarding (Zero Footprint)

Tell your participants to follow these **4 steps** to join the lab:

1.  **Open the Web IDE**: [https://roosevelt-nonentreating-paler.ngrok-free.dev/ide/](https://roosevelt-nonentreating-paler.ngrok-free.dev/ide/)
    - **Password**: `LabPassword123`
2.  **Open a Terminal**: Go to the top-left menu -> **Terminal** -> **New Terminal**.
3.  **Start your Agent**: Run these exact commands:
    ```bash
    cd project
    export LAB_USER_ID="userXX"    # <--- USE YOUR ASSIGNED ID (e.g. user01)
    python3 telemetry_producer.py
    ```
4.  **Chat with AI**: Open the **Premium Chat UI** at [https://roosevelt-nonentreating-paler.ngrok-free.dev/](https://roosevelt-nonentreating-paler.ngrok-free.dev/).
    - **Email**: `userXX@cisco.com`
    - **Password**: `CiscoLab2026!`

> [!TIP]
> **Data Privacy**: Because of our isolation filters, students will ONLY see their own data in Splunk dashboards ([https://roosevelt-nonentreating-paler.ngrok-free.dev/splunk/](https://roosevelt-nonentreating-paler.ngrok-free.dev/splunk/)) and when they ask the AI questions.
