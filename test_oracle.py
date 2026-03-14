import oracledb
import os

print("Testing Oracle initialization...")
try:
    oracledb.init_oracle_client()
    print("Success without lib_dir")
except Exception as e:
    print(f"Failed without lib_dir: {e}")

path = os.getenv("ORACLE_CLIENT_PATH")
if path:
    try:
        oracledb.init_oracle_client(lib_dir=path)
        print("Success WITH lib_dir")
    except Exception as e:
        print(f"Failed WITH lib_dir: {e}")
