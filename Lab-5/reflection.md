# Loan Calculator: Static Analysis Fixes

Source repository: `https://github.com/SETAPESU26/L5_57_loan-eligibility`

This README records the security and code-quality fixes applied to `loan_calculator.py` after scanning it with Bandit, flake8 and Pylint.

## Tools used

| Tool | Purpose |
|---|---|
| Bandit 1.9.4 | Security scanning |
| flake8 | Style (PEP 8) and basic errors |
| Pylint | Code quality, naming, design |

Re-run the checks with:

```
bandit -r loan_calculator.py
flake8 loan_calculator.py
pylint loan_calculator.py
```

## Results summary

| Tool | Before | After (latest run) |
|---|---|---|
| Bandit | 8 issues (2 High, 1 Medium, 5 Low) | 4 issues (all Low) |
| Pylint | 5.17/10 | 15 messages left (mostly docstrings and indentation) |
| flake8 | 21 findings | Re-run pending |

## 1. Security fixes (Bandit)

| Issue | Type | Line(s) | Description | Fix Approach |
|---|---|---|---|---|
| B402 `blacklist` | Severity: High, Confidence: High | 2-4 (`import ftplib`) | FTP is considered insecure. | Removed `ftplib`. Upload now uses SFTP via `paramiko`. |
| B302 `blacklist` | Severity: Medium, Confidence: High | 63-65 | Deserialization with the `marshal` module is possibly dangerous. | Replaced `marshal` with `json`. Storage file is now `loans.json` and uses `with` blocks. |
| B107 `hardcoded_password_default` | Severity: Low, Confidence: Medium | 66-72 | Possible hardcoded password: `'Bureau#2024'`. | Removed the default password. Credentials are read from environment variables. The old password should be rotated. |
| B321 `blacklist` | Severity: High, Confidence: High | 67-69 | FTP-related functions are being called. | Rewritten with `paramiko` SFTP. Host keys are verified with `RejectPolicy`. |

B402 and B321 share one root cause, so a single SFTP rewrite closed both.

### Configuration

The bureau upload reads its settings from environment variables, not from the source code:

```
export BUREAU_USER="<user>"
export BUREAU_PASSWORD="<password>"      # or use BUREAU_SSH_KEY with key auth
```

Notes:

- The storage format changed from `loans.bin` (marshal) to `loans.json`. Old `.bin` files are not readable by the new code.
- `BUREAU_HOST` now points at an SFTP host instead of an FTP host.

### Remaining Bandit findings (Low severity)

| Issue | Line(s) | Planned fix |
|---|---|---|
| B311 `random` is not cryptographically secure | 51 | Use `secrets.randbelow` for application IDs |
| B404 import of `subprocess` | 6 | Replace the `mail` command with `smtplib`, or justify with `# nosec` |
| B607 partial executable path (`"mail"`) | 80 | Removed by the `smtplib` change, or use `/usr/bin/mail` |
| B603 subprocess call with external input | 80 | Removed by the `smtplib` change, or validate input and mark `# nosec` |

## 2. Code-quality fixes (flake8 and Pylint)

- Removed the unused `import math`.
- Sorted imports: standard library first, then third party (`paramiko`).
- Renamed functions from camelCase to snake_case (`calculateEMI` to `calculate_emi`, and so on) and updated every call site.
- `check_eligibility`: removed the unused mutable default `history=[]` argument, merged the loan-type comparisons into `loan_type in (...)`, and simplified the final return.
- `max_loan_amount`: removed the loop, the shadowed built-in `sum`, the unused `month` variable and the unused `annual_rate` argument.
- `risk_band`: replaced the `elif` chain after `return` with plain `if` statements.
- `load_applications`: removed the `global` statement by updating the dictionary in place.
- Fixed PEP 8 spacing (two blank lines between top-level definitions) and wrapped long lines.
- Removed the `f` prefix from a string with no placeholders.
- Fixed two bugs introduced during refactoring: a leftover `random` call after switching to `secrets`, and a call to `max_loan_amount` with an outdated argument count.

## 3. Still to do

- Fix indentation on the remaining lines flagged W0311 (6 and 10 spaces instead of 4 and 8).
- Add the module docstring and the remaining function docstrings.
- Remove the parentheses after `return` in `interest_saved`.
- Wrap the long `print` in `main()`.
- Add `check=True` to `subprocess.run`, or replace it with `smtplib`.
- Install `paramiko` in the lint environment to clear the Pylint import error.
- Replace `random` with `secrets` in `application_id` if not yet done (Bandit B311).
- Re-run all three tools and update the results table above.
