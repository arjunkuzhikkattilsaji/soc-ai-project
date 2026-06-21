# Incident Response Runbook
### AI-Powered AWS Threat Detection Project

This runbook defines the standard response procedure for each detection in this project. It is written in the same format real SOC teams use to ensure consistent, repeatable incident handling regardless of who is on shift.

---

## How to Use This Document

When an alert is received (via email from SNS), locate the matching detection below and follow the **Triage → Investigation → Containment → Remediation → Post-Incident** steps in order. Do not skip Triage — it determines whether the rest of the runbook is even necessary.

---

## Runbook 1: AWS Console Login Without MFA

**MITRE ATT&CK Technique:** T1556 — Modify Authentication Process
**Severity:** High
**Detection Source:** CloudTrail → CloudWatch Logs Subscription Filter → Lambda

### What This Detection Means
A user successfully signed in to the AWS Management Console without completing multi-factor authentication. This does not always mean an attack occurred — it may be a legitimate user whose account simply doesn't have MFA enforced — but it is always a risk worth verifying, since password-only accounts are a common entry point for credential theft and brute-force attacks.

### Indicators Captured
- Username
- Source IP address
- Timestamp
- Login success/failure

### Response Procedure

**1. Triage (target: within 15 minutes of alert)**
- Identify the username and source IP from the alert
- Check whether the IP address is known/expected for this user (e.g., their usual office or home network)
- Check whether this user is expected to have MFA configured at all (some test/service accounts may not need it)

**2. Investigation**
- Pull recent CloudTrail activity for this username — what did they do after logging in?
- Check for multiple login attempts in a short window (possible brute-force or credential stuffing)
- Cross-reference the source IP against any known malicious IP lists if available
- Determine: is this expected user behavior, or does it look anomalous?

**3. Containment (if suspicious)**
- Temporarily disable the affected IAM user's console access
- Invalidate any active sessions if possible
- Do not yet delete the account — preserve evidence for investigation

**4. Remediation**
- Require the user to reset their password
- Enforce MFA on the account before restoring access
- If credential compromise is confirmed, rotate any access keys associated with the account

**5. Post-Incident**
- Document the root cause (misconfiguration vs. actual compromise)
- If this was a legitimate user without MFA, follow up with an account-wide MFA enforcement policy to prevent recurrence
- Update this runbook if any step needs adjustment based on what was learned

### Escalation Criteria
Escalate immediately to a senior analyst if:
- The source IP is from an unexpected country/region
- Multiple different users show this pattern within the same timeframe
- Any sensitive actions (IAM changes, billing changes, data access) occurred during the session

---

## Runbook 2: Security Group Opened to the Entire Internet (0.0.0.0/0)

**MITRE ATT&CK Technique:** T1562.007 — Impair Defenses: Disable or Modify Cloud Firewall
**Severity:** Critical
**Detection Source:** CloudTrail → EventBridge → Lambda

### What This Detection Means
A security group rule was modified to allow inbound traffic from any IP address on the internet. This is one of the most common root causes of real-world cloud breaches — an exposed database, SSH port, or application becomes immediately reachable by automated scanning tools the moment this rule is saved.

### Indicators Captured
- Username who made the change
- Security group ID affected
- Source IP of the user making the change
- Timestamp

### Response Procedure

**1. Triage (target: within 5 minutes — this is Critical severity)**
- Identify which security group was modified and what resources (EC2 instances, databases, etc.) are attached to it
- Determine if any attached resource is currently running and reachable

**2. Investigation**
- Check what ports/protocols were opened (all traffic vs. a specific port like SSH/RDP)
- Determine whether this change was intentional (a legitimate deployment/testing need) or unauthorized
- Check CloudTrail for who made the change and what else they did around the same time

**3. Containment (immediate, regardless of intent)**
- Revert the security group rule immediately — remove the `0.0.0.0/0` entry
- If a resource was exposed and there's any sign of scanning/connection attempts in logs, isolate that resource (e.g., remove from the security group, stop the instance) until verified clean

**4. Remediation**
- Replace the open rule with a properly scoped one (specific IP ranges, only required ports)
- Review IAM permissions of the user who made the change — should they have this level of access?
- If this was unauthorized or malicious, follow the same credential-compromise steps as Runbook 1

**5. Post-Incident**
- Document whether any resource was actually exposed during the window the rule was open, and for how long
- If accidental misconfiguration, consider adding a guardrail (e.g., AWS Config rule) to prevent this in the future
- If this was a legitimate change made incorrectly, provide guidance to the team on proper security group scoping

### Escalation Criteria
Escalate immediately to a senior analyst or incident commander if:
- A production resource (not a test/dev resource) was exposed
- There is evidence of inbound connection attempts during the exposure window
- The change was made by an account that should not have had permission to modify security groups

---

## General Severity & Response Time Matrix

| Severity | Target Triage Time | Escalation Required If |
|----------|--------------------|--------------------------|
| Critical | 5 minutes | Any sign of actual exploitation or production impact |
| High | 15 minutes | Pattern across multiple users/accounts, or sensitive resource access |
| Medium | 1 hour | Repeated occurrences from the same source |
| Low | Next business day | N/A — log and monitor for patterns |

---

*This runbook is a living document. As new detections are added to this project, corresponding runbook sections should be added following the same structure.*
