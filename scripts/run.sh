#!/bin/bash
# Temporary CPU audit entry point; restored after the audit job.
set -euo pipefail
cd /home/user
exec bash redteam/bundle.sh
