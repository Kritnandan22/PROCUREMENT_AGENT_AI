import oracledb
import os

try:
    # Enable thick mode
    oracledb.init_oracle_client(lib_dir=os.environ.get("ORACLE_CLIENT_PATH"))
    
    # Connect to Oracle database
    conn = oracledb.connect(
        user="APPS",
        password="apps",
        dsn="161.118.185.249:1521/EBSDB"
    )
    
    cursor = conn.cursor()
    
    # Query to get all organization IDs
    cursor.execute("""
        SELECT COUNT(DISTINCT org_id) as total_orgs
        FROM org_organization_definitions
    """)
    
    result = cursor.fetchone()
    print(f"Total Unique Org IDs: {result[0]}")
    
    # Get list of all org IDs
    cursor.execute("""
        SELECT DISTINCT org_id, organization_code, organization_name 
        FROM org_organization_definitions
        ORDER BY org_id
    """)
    
    rows = cursor.fetchall()
    print(f"\nAll Organization IDs ({len(rows)} total):")
    print("-" * 80)
    print(f"{'Org ID':<10} {'Org Code':<20} {'Organization Name':<50}")
    print("-" * 80)
    
    for row in rows:
        org_id, org_code, org_name = row
        print(f"{org_id:<10} {org_code:<20} {org_name:<50}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
