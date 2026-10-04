#!/usr/bin/env bash
# run_all.sh : stage -> upload -> load -> build -> demo results. Run from repo root.
set -euo pipefail
C="--connection portpilot"
DATA="datagen/output"

echo "== 1/3 stage + file format =="
snow sql $C -q "USE ROLE PORTPILOT_ENGINEER; USE WAREHOUSE PORTPILOT_LOAD_WH;
CREATE FILE FORMAT IF NOT EXISTS PORTPILOT.RAW.CSV_GZ TYPE=CSV COMPRESSION=GZIP PARSE_HEADER=TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY='\"' NULL_IF=('') EMPTY_FIELD_AS_NULL=TRUE;
CREATE STAGE IF NOT EXISTS PORTPILOT.RAW.LANDING FILE_FORMAT=PORTPILOT.RAW.CSV_GZ;"

echo "== 2/3 upload files =="
for f in dim_customer dim_vessel fact_container_journey fact_container_event fact_delay_event advisory_documents; do
  snow sql $C -q "USE ROLE PORTPILOT_ENGINEER; PUT file://$PWD/$DATA/$f.csv.gz @PORTPILOT.RAW.LANDING AUTO_COMPRESS=FALSE OVERWRITE=TRUE;"
done

echo "== 3/3 load + build + demo =="
snow sql $C -f snowflake/load_and_build.sql | tee snowflake/demo_results.txt
echo "DONE. Results saved to snowflake/demo_results.txt"

# Switch roles for governance screenshot
# Switch to PORTPILOT_OPS_ANALYST
snow sql $C -q "USE ROLE PORTPILOT_OPS_ANALYST;"

# Take governance screenshot here

# Switch to PORTPILOT_CUSTOMER_SUCCESS
snow sql $C -q "USE ROLE PORTPILOT_CUSTOMER_SUCCESS;"

# Take governance screenshot here
