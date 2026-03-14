import asyncio
import os
from dotenv import load_dotenv
from tutorial_agentic_procurement_agent import OracleReadOnlyGateway, _init_oracle_client

load_dotenv()

def test_db():
    print("Testing Oracle initialization...")
    print(f"Thick mode loaded: {_init_oracle_client()}")
    print("Testing connection...")
    try:
        gateway = OracleReadOnlyGateway()
        res = gateway.test_connection()
        print(f"SUCCESS: {res}")
    except Exception as e:
        print(f"ERROR: {e}")

test_db()
