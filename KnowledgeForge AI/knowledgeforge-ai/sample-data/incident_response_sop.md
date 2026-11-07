# Site Reliability Engineering Incident Response & Post-Mortem SOP

## 1. Incident Severity Definitions

- **Severity-1 (Critical Outage)**: Core user-facing functionality is fully unavailable or suffering catastrophic data corruption across multiple regions.
  - Escalation bridge convened within 5 minutes.
  - Executive leadership notification within 15 minutes.
  - Status page public update every 20 minutes until resolved.
- **Severity-2 (Major Impairment)**: Critical feature degraded with significant customer impact, but workable fallback or partial availability exists.
  - Escalation bridge convened within 15 minutes.
  - Customer status update every 45 minutes.
- **Severity-3 (Minor Disruption)**: Non-critical subsystem failing without immediate revenue or transaction impact.
  - Response within 2 business hours.
- **Severity-4 (Low Impact)**: Minor cosmetic defect, non-blocking bug, or internal tooling delay.
  - Handled during standard operating sprint cycles.

## 2. Command Authority and Incident Roles

- **Incident Commander (IC)**: The Incident Commander or designated on-call Lead SRE has single-point operational authority to declare a Severity-1 incident, order service rollbacks, execute database failovers, and direct all technical response teams.
- **Communications Lead (CL)**: Dedicated liaison responsible for internal stakeholder updates and external public status page maintenance.
- **Operations Lead (OL)**: Coordinates engineering responders conducting live root-cause isolation and deployment of mitigation patches.

## 3. Incident Lifecycle Phases

1. **Detection & Triage**: Automated alerting triggered via Prometheus/Datadog monitors or customer report ingestion.
2. **Containment**: Prioritize customer impact mitigation (e.g., traffic shedding, feature-flag kill switches, region failovers) over investigative troubleshooting.
3. **Resolution**: Verification of normal telemetry baselines for at least 30 consecutive minutes following fix deployment.
4. **Blameless Post-Mortem**: A blameless root-cause analysis (RCA) must be published within 72 hours of incident closure, including a chronological timeline, contributing causes, and preventive action items assigned to engineering owners.

