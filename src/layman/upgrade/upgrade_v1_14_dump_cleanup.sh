#!/bin/bash
set -ex

perl /code/src/layman/upgrade/upgrade_v1_14_postgis_restore.pl "$1" > "$2"
sed -i 's/ spatial_ref_sys\b/ public.spatial_ref_sys/g' "$2"
sed -i '/^\(CREATE\|ALTER\) OPERATOR FAMILY public.gist_geometry_ops/d' "$2"
sed -i '/^\(ALTER TABLE\|UPDATE\) topology\./d' "$2"
sed -i '/^COMMENT ON \(SCHEMA\|EXTENSION\)/d' "$2"
sed -i '/^CREATE EXTENSION IF NOT EXISTS \(pgrouting\|postgis_topology\)/d' "$2"
sed -i '/^ALTER DEFAULT PRIVILEGES FOR ROLE docker IN SCHEMA public GRANT SELECT ON TABLES  TO replicator;/d' "$2"
perl -0777 -i.original -pe 's/\nCOPY topology\.[^\n]*\n\\\.\n//igs' "$2"
