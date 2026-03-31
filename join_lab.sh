#!/bin/bash

# GenAI Observability Lab - Participant Onboarding Tool
# This script automates Step 3 of the Onboarding Guide.

echo "----------------------------------------------------"
echo "🚀 Welcome to the Predictive Insights Lab!"
echo "----------------------------------------------------"

# Prompt for User ID if not already exported
if [ -z "$LAB_USER_ID" ]; then
    read -p "Please enter your assigned User ID (e.g., user01): " USER_ID
    export LAB_USER_ID=$USER_ID
fi

echo "Setting identity: $LAB_USER_ID"
echo "Starting Telemetry Producer for $LAB_USER_ID..."

# Launch the telemetry producer
python3 telemetry_producer.py
