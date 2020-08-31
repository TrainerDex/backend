sudo -u postgres psql << EOF
  CREATE USER $DB_USER PASSWORD '$DB_PASS';
  CREATE DATABASE $DB_NAME OWNER $DB_USER;
  \c $DB_NAME
  CREATE EXTENSION citext;
EOF