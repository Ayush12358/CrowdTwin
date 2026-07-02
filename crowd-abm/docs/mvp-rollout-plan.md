# Crowd ABM MVP Rollout Plan

## 1. Executive Summary

- What: Roll out Crowd ABM MVP simulation core as a versioned Python library/service component for one-step crowd updates.
- Why: Deliver deterministic, test-backed, benchmarked one-step crowd simulation with API payload support and diagnostics/events.
- When: During a controlled low-traffic change window (recommended Tue-Thu, 10:00-16:00 local time).
- Expected active deployment duration: 30-45 minutes.
- Risk level: Medium.
- Estimated rollback time: 10-20 minutes.
- Affected systems:
  - Upstream orchestrator that submits per-second payloads.
  - Any service consuming simulator diagnostics/events.
- User impact:
  - No end-user downtime expected if deployed behind a feature flag or version pin.
  - Temporary reduction in simulation throughput possible during canary if resource limits are too tight.
- Expected downtime: 0 minutes for phased/canary rollout. Up to 5 minutes if a hard cutover is chosen.

## 2. Prerequisites and Approvals

### Required Approvals

- Technical lead approval: Required.
- QA approval after staging verification: Required.
- Security/compliance approval: Optional unless production data includes regulated fields.
- Product/business sign-off for release window: Required.

### Required Resources

- Runtime targets available:
  - Staging environment with representative workload.
  - Production environment.
- Python 3.12 runtime.
- Virtual environment support.
- Monitoring/alerting configured for latency and error rate.
- Rollback automation:
  - Previous artifact or commit hash available.
  - Version pin rollback path tested.

### Pre-Deployment Backups

- Back up:
  - Current production deployment artifact/version.
  - Configuration used by orchestrator to call simulator API.
  - Last known-good benchmark report.
- Store backup metadata with timestamp and operator name.

## 3. Preflight Checks

### Infrastructure Health Validation

- Verify runtime host/container health.
- Verify CPU and memory headroom >= 30% before rollout.
- Confirm disk and log storage availability.

### Application Health Baseline

Run in repository root:

```bash
uv pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m src.benchmark.harness --iterations 20
```

Baseline expectations:

- Test status: All tests pass.
- Benchmark status: Command succeeds and emits JSON with scenarios.
- No critical warnings or crashes.

### Dependency Availability

- Confirm orchestrator can import and call the simulator API.
- Confirm no missing runtime packages in target environment.

### Monitoring Baseline Metrics

Capture pre-rollout values:

- Simulator step latency p50/p95.
- Error rate (exceptions per minute).
- CPU and memory usage.
- Throughput (steps per second).

### Go/No-Go Checklist

- All required approvals are present.
- Preflight checks all pass.
- Rollback owner assigned.
- Communication templates prepared.
- On-call contacts acknowledged readiness.

## 4. Step-by-Step Rollout Procedure

### Phase A: Pre-Deployment (10-15 min)

1. Announce deployment start in team channel.
2. Freeze non-critical changes in target environment.
3. Pull exact release commit/tag.
4. Re-run validation commands:

```bash
uv pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m src.benchmark.harness --iterations 20
```

5. Validate benchmark output exists and has non-zero steps_per_sec for all scenarios.

Validation gate:

- Proceed only if all tests pass and benchmark emits expected scenario output.

### Phase B: Deployment (10-15 min)

1. Deploy MVP artifact to staging.
2. Run staging smoke:

```bash
.venv/bin/python main.py
```

3. Run payload path smoke in staging integration environment (or integration test job) using step_payload-compatible payload.
4. If staging is healthy, start production canary (5-10% traffic or selected orchestrator workers).
5. Monitor immediate signals for 5 minutes.

Validation gate:

- Proceed to full rollout only if canary passes immediate and short-term signals.

### Phase C: Progressive Verification (10-15 min)

1. Increase to 25% traffic.
2. Monitor 5 minutes.
3. Increase to 50% traffic.
4. Monitor 5 minutes.
5. Increase to 100% traffic.
6. Monitor 15 minutes.

Validation after each increment:

- Error rate stays within baseline + agreed threshold.
- Step latency remains within SLO budget.
- No sustained CPU or memory saturation.

## 5. Verification Signals

### Immediate (0-2 min)

- Deployment completed successfully.
- Runtime process/container healthy.
- Basic smoke calls return valid payload shape.
- No startup exceptions.

### Short-Term (2-5 min)

- Requests are served successfully.
- Error rate remains near baseline.
- Latency p95 remains within accepted threshold.
- Canary worker logs show normal operation.

### Medium-Term (5-15 min)

- Metrics remain stable across traffic increments.
- No growing queue/backlog in orchestrator.
- Diagnostics and optional events are structurally valid.

### Long-Term (15+ min)

- No regression in throughput under normal load.
- Capacity remains healthy.
- Downstream consumers report normal behavior.

## 6. Rollback Procedure

### Decision Criteria

Initiate rollback immediately if any of these occur:

- Repeated simulation exceptions or payload failures.
- Latency SLO breach for more than 5 minutes.
- Error rate exceeds threshold (example: >2x baseline) for more than 3 minutes.
- Determinism or correctness issues observed in production checks.

### Rollback Steps

1. Halt progressive rollout.
2. Route traffic back to previous stable version.
3. Re-pin deployment to previous release artifact/commit.
4. Restart affected worker processes if needed.
5. Confirm rollback completion in deployment tooling.

### Post-Rollback Verification

- Health checks pass.
- Error and latency metrics return to baseline.
- Orchestrator processing resumes normal cadence.

### Communication

- Send rollback alert with:
  - Trigger reason.
  - Affected scope.
  - Mitigation ETA.
  - Next update time.

## 7. Communication Plan

### Timeline

- T-24h: Send schedule, scope, risk, and rollback summary.
- T-15m: Reminder and freeze notice.
- T0: Deployment started.
- Every 10 minutes: Status update during rollout.
- Completion: Success and monitoring window notice.
- Rollback (if needed): Incident and mitigation notice immediately.

### Stakeholder Matrix

- Engineering team:
  - When: T-24h, T0, every 10 minutes, completion.
  - Channel: Team chat + incident channel if needed.
  - Content: Progress, metrics summary, blockers.
- Product owner:
  - When: T-24h, completion, rollback if needed.
  - Channel: Chat/email.
  - Content: User impact and release status.
- Operations/on-call:
  - When: T-15m, T0, rollback event.
  - Channel: Pager + incident channel.
  - Content: Alert thresholds, actions required.

## 8. Post-Deployment Tasks

### Immediate (within 1 hour)

- Verify all success criteria were met.
- Review runtime logs for anomalies.
- Confirm no hidden warnings or payload schema errors.

### Short-Term (within 24 hours)

- Compare rollout-day metrics to baseline.
- Review top error signatures, if any.
- Confirm benchmark and production behavior remain aligned.

### Medium-Term (within 1 week)

- Conduct post-deployment review.
- Document lessons learned and action items.
- Update runbook/checklist with improvements.

## 9. Contingency Plans

### Scenario: Partial Failure During Canary

- Symptoms: Elevated errors only on canary workers.
- Response: Hold traffic increase, inspect logs, hotfix or rollback canary.
- Timeline: Decision within 5 minutes.

### Scenario: Performance Degradation

- Symptoms: Latency p95/p99 grows while error rate is low.
- Response: Stop rollout progression, reduce traffic weight, tune resource limits or rollback.
- Timeline: Decision within 10 minutes.

### Scenario: Data/Payload Inconsistency

- Symptoms: Payload validation errors, mismatched occupancy vs agents.
- Response: Revert to previous version, isolate payload producer issue, replay sample payloads.
- Timeline: Decision within 5 minutes.

### Scenario: Dependency/Runtime Failure

- Symptoms: Import errors, package mismatch, startup failures.
- Response: Restore known-good environment image or lockfile, redeploy previous version.
- Timeline: Decision within 10 minutes.

## 10. Contact Information

Fill these before production rollout:

- Primary release owner: <name>, <phone/chat>
- Secondary release owner: <name>, <phone/chat>
- On-call SRE/operations: <name>, <phone/chat>
- Database/data owner (if applicable): <name>, <phone/chat>
- Security contact (if applicable): <name>, <phone/chat>
- Escalation manager: <name>, <phone/chat>

## MVP Readiness Snapshot (Current Repository)

- Implemented:
  - One-step simulation API and payload API.
  - 2D eight-neighbor movement quantization.
  - Conflict resolution by will, tie-break by lowest agent id.
  - Diagnostics and optional per-agent event payloads.
  - Validation for occupancy-agent consistency.
  - Benchmark harness with scenario output.
  - Unit/regression tests.
- Latest local verification status:
  - Unit tests: passing.
  - Benchmark harness: passing.
- Remaining before production release:
  - Populate real contact names/escalation.
  - Confirm traffic-shift mechanism in deployment environment.
  - Define production SLO thresholds if not already documented.
