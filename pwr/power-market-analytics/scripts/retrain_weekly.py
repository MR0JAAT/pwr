"""Wrapper to retrain models weekly. Intended to be scheduled via cron or task scheduler."""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    subprocess.check_call([sys.executable, str(BASE / 'train_models.py')])


if __name__ == '__main__':
    main()
