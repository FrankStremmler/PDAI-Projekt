'''
Main entry point for the PDAI-Project.
Integrating AI and a Household_Budget to a Personal Digital Assistant in a single application.
The Personal Digital Assistant (PDAI) is a software application designed to assist users in managing their daily tasks, schedules, and information. It integrates artificial intelligence (AI) capabilities to provide personalized assistance and enhance user experience. The PDAI can perform various functions such as setting reminders, answering questions, providing recommendations, and managing household budgets.

The AI is used to analyze Receipts and can also provide insights and Analysis of the Budget.
'''
import os
import sys
from dotenv import load_dotenv
from openai import api_key

load_dotenv()

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def main():
    from pdai_gui import run_app
    return run_app()


if __name__ == "__main__":
    sys.exit(main())
