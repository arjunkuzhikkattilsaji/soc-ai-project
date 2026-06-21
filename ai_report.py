import boto3
import requests
import json

# Connect to your DynamoDB table
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('security-findings')

# Pull every finding stored so far
response = table.scan()
findings = response.get('Items', [])

if not findings:
    print("No findings to report.")
else:
    # Turn the findings into plain text the AI can read
    findings_text = ""
    for f in findings:
        findings_text += f"- {f.get('timestamp')}: {f.get('summary')} (Severity: {f.get('severity')}, MITRE: {f.get('mitre_technique')})\n"

    # Build the prompt we send to the AI
    prompt = f"""You are a SOC analyst assistant. Below is a list of security findings from an AWS account.
Write a clear, professional incident report summarizing these findings, grouped by severity,
and recommend next steps for each.

Findings:
{findings_text}
"""

    # Send the prompt to your local Ollama model
    ai_response = requests.post("http://localhost:11434/api/generate", json={
        "model": "phi3",
        "prompt": prompt,
        "stream": False
    })

    report = ai_response.json()["response"]

    print("===== AI THREAT REPORT =====")
    print(report)

    # Save it to a file too, for your portfolio
    with open("threat_report.txt", "w") as f:
        f.write(report)