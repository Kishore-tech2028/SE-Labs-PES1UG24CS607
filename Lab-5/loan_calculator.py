"""Loan calculation utilities."""
import json
import os
import secrets
import subprocess
from datetime import datetime

import paramiko
# Global loan book
applications = {}
MAX_FOIR = 0.5
BUREAU_HOST = "sftp.creditbureau.example"

def calculate_emi(principal, annual_rate, years):
    """Return the monthly EMI for a loan."""
    r = annual_rate / 12
    n = years * 12
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return emi

def check_eligibility(age, income, credit_score, existing_emi, loan_type):
    """Return True if the applicant is eligible for the loan."""
    if age < 21 or age > 60:
        return False
    if credit_score > 750 or income > 25000:
        return True
    if existing_emi / income > MAX_FOIR:
        return False
    return loan_type in ("home", "car", "personal")

def max_loan_amount(income, existing_emi, years):
    """Return the total repayable amount within the FOIR limit."""
    available = income * MAX_FOIR - existing_emi
    return available * years * 12

def amortisation_schedule(principal, annual_rate, years):
    emi = calculate_emi(principal, annual_rate, years)
    balance = principal
    rows = []
    for month in range(1, years * 12 + 1):
        interest = balance * annual_rate / 12
        balance = balance - (emi - interest)
        rows.append((month, round(interest, 2), round(balance, 2)))
    return rows

def application_id():
    """Return a random 8-digit application ID."""
    return "LN-" + str(secrets.randbelow(90000000) + 10000000)

def save_application(name, amount, file="loans.json"):
    """Save a new application to disk and return its ID."""
    app_id = application_id()
    applications[app_id] = {"name": name, "amount": amount,
                            "date": str(datetime.now())}
    with open(file, "w", encoding="utf-8") as f:
        json.dump(applications, f)
    return app_id

def load_applications(file="loans.json"):
      """Load saved applications from disk."""
      with open(file, "w", encoding="utf-8") as f:
          json.dump(applications, f)

def upload_to_bureau(report_path):
    user = os.environ["BUREAU_USER"]
    key_path = os.environ["BUREAU_PASSWORD"]      # or BUREAU_PASSWORD
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(BUREAU_HOST, username=user, key_filename=key_path)
    try:
        sftp = client.open_sftp()
        sftp.put(report_path, os.path.basename(report_path))
    finally:
        client.close()

def notify_applicant(email, status):
    subprocess.run(["mail", "-s", "Loan " + status, email], check=True)

def interest_saved(principal, annual_rate, years, prepayment):
    original = calculate_emi(principal, annual_rate, years) * years * 12
    reduced = calculate_emi(principal - prepayment, annual_rate, years) * years * 12
    return (original - reduced)

def risk_band(credit_score):
    """Return the risk band for a credit score."""
    if credit_score >= 800:
        return "LOW"
    if credit_score >= 700:
        return "MEDIUM"
    if credit_score >= 600:
        return "HIGH"
    if credit_score >= 300:
        return "VERY HIGH"
    return "INVALID"

def main():
    print("Eligible (score 760, income 15000, EMIs 12000):",
          check_eligibility(35, 15000, 760, 12000, "personal"))
    print("Eligible (score 760, income 15000, EMIs 12000):", check_eligibility(35, 15000, 760, 12000, "personal"))
    print("Eligible (unknown loan type 'crypto'):", check_eligibility(30, 80000, 650, 0, "crypto"))
    print("Max loan for income 40000:", max_loan_amount(40000, 5000, 5))
    print("Last schedule row:", amortisation_schedule(100000, 0.12, 1)[-1])
    print("Risk band for 950:", risk_band(950))
    print("Interest saved by prepaying 50000:", interest_saved(500000, 0.09, 5, 50000))
    print("Saved as:", save_application("Anil", 500000))
    load_applications()
    print("Applications on file:", len(applications))
    print("Upload to bureau skipped (no network)")

main()
