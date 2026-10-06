# Network Incident Agent

A multi-agent system that detects, diagnoses, and remediates network incidents automatically — built with [Google ADK](https://github.com/google/adk-python), Gemini, and real Google Cloud telemetry.

> Built for [Hackathon name] — a demonstration of agentic AI applied to NOC (Network Operations Center) workflows.

---

## What it does

Instead of one large model trying to do everything, this project splits the incident-response workflow across **three specialized agents**, each with a narrow job — the same way a real NOC team splits work across a monitoring engineer, a senior diagnostician, and a team lead:

| Agent | Job | Input | Output |
|---|---|---|---|
| **Detection** | Watches alarms, logs, and topology data; decides if a real incident is happening | Live Cloud Monitoring + Cloud Logging data | A plain-language incident summary |
| **Diagnosis** | Performs root-cause analysis | Detection's summary | Root cause + affected services |
| **Remediation** | Writes an action plan for the ops team | Diagnosis's output | A numbered, prioritized remediation plan |

The three agents are chained with ADK's `SequentialAgent`, so each agent's real output automatically becomes the next agent's input — no manual hand-off, no shared global state.

Critically, the agents are instructed **not to invent incidents**. When the underlying data shows nothing wrong, Detection correctly reports "no incident detected," and Diagnosis/Remediation both stand down rather than fabricating analysis — this was verified against real (quiet) GCP data before a real incident was deliberately simulated.

---

## Architecture

```
            ┌─────────────────┐
  Trigger → │ Detection Agent │  reads: Cloud Monitoring (alarms)
            └────────┬────────┘         Cloud Logging (logs)
                     │ summary          Network topology
                     ▼
            ┌─────────────────┐
            │ Diagnosis Agent │  reasons over Detection's output only
            └────────┬────────┘
                     │ root cause + affected services
                     ▼
            ┌──────────────────┐
            │ Remediation Agent│  reasons over Diagnosis's output only
            └────────┬──────────┘
                     │
                     ▼
            Prioritized action plan for the ops team
```

Orchestration: `google.adk.agents.SequentialAgent`
Model: `gemini-3.1-flash-lite` (chosen for generous free-tier quota and low latency; swap `MODEL` in any file to use a different Gemini model)

---

## Tech stack

- **[Google ADK](https://github.com/google/adk-python)** — agent definitions, tool-calling, and sequential orchestration
- **Gemini API** (`gemini-3.1-flash-lite`) — the reasoning model behind each agent
- **Google Cloud Monitoring API** — real alert policy data
- **Google Cloud Logging API** — real log entries
- **Python 3.12**, `asyncio`

---

## Project structure

```
.
├── agent1_detection.py          # Detection agent, standalone (mocked data)
├── agent2_diagnosis.py          # Diagnosis agent, standalone (mocked input)
├── agent3_remediation.py        # Remediation agent, standalone (mocked input)
├── full_pipeline.py             # All 3 agents chained, mocked data
├── real_data_tools.py           # Real GCP data tools, tested standalone
├── full_pipeline_real_data.py   # All 3 agents chained, REAL GCP data
├── seed_test_incident.py        # Writes a simulated incident into Cloud Logging for demo purposes
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.10+ (3.12 recommended)
- A Google Cloud project with the **Cloud Monitoring API** and **Cloud Logging API** enabled
- A free [Gemini API key](https://aistudio.google.com/) from AI Studio
- `gcloud` CLI installed and authenticated

### 2. Clone and set up the environment

```bash
git clone <this-repo-url>
cd network-incident-agent
python3 -m venv venv
source venv/bin/activate
pip install google-adk google-cloud-monitoring google-cloud-logging
```

### 3. Authenticate to Google Cloud

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

> This project uses Application Default Credentials rather than a service account key file, since many GCP organizations now block key creation by policy (`iam.disableServiceAccountKeyCreation`).

### 4. Set your Gemini API key

```bash
export GOOGLE_API_KEY="your-ai-studio-key"
```

### 5. Update the project ID

In `real_data_tools.py`, `full_pipeline_real_data.py`, and `seed_test_incident.py`, set:

```python
PROJECT_ID = "your-gcp-project-id"
```

---

## Usage

### Run the full pipeline against mocked data (no GCP calls)

```bash
python full_pipeline.py
```

### Run against real GCP data

```bash
python full_pipeline_real_data.py
```

On a quiet project, this correctly reports "no incident detected."

### Simulate an incident for a live demo

```bash
python seed_test_incident.py          # writes realistic incident log entries into Cloud Logging
python full_pipeline_real_data.py     # re-run — the agents now detect, diagnose, and remediate it
```

### Run an individual agent in isolation

```bash
python agent1_detection.py
python agent2_diagnosis.py
python agent3_remediation.py
```

---

## Example output

```
--- [detection_agent] ---
A significant service incident is currently in progress...
- Service Outage: us-east1 region unhealthy, 100% traffic failover to us-central1
- Performance Degradation: checkout-api p99 latency at 4200ms (threshold 500ms)
- Dependency Failure: checkout-api → payment-gateway connection timeouts
- Resource Exhaustion: payment-gateway at 95% CPU

--- [diagnosis_agent] ---
Root cause: resource exhaustion in payment-gateway, caused by traffic
failover from the us-east1 outage.
Affected services: payment-gateway, checkout-api, load-balancer

--- [remediation_agent] ---
1. Scale payment-gateway instances immediately
2. Investigate and restore us-east1 health
3. Monitor us-central1 for secondary overload
4. Verify checkout-api connection pools clear once stable
5. Set up alert policies — none existed, which is why this went undetected
```

---

## Known limitations / next steps

- **Network topology** data (Network Intelligence Center) is currently a placeholder — Detection reasons from alarms and logs only.
- No persistent incident history or ticketing integration yet.
- Designed for demo-scale GCP projects; not yet load-tested against high-volume production logging.
- `SequentialAgent` is marked deprecated in favor of ADK's newer `Workflow` API — migration pending `Workflow` support for `LlmAgent` sub-agents.

---
