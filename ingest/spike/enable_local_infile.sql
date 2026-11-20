-- Run against SingleStore Helios (MySQL protocol, port 3306) as a privileged user.
-- Required for Airbyte MySQL destination bulk LOAD DATA.

SET GLOBAL local_infile = true;

SHOW GLOBAL VARIABLES LIKE 'local_infile';
-- Expect: Variable_name = local_infile, Value = ON
