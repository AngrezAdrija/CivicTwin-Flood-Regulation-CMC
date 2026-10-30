const { Pool } = require('pg');

const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'civictwin',
  password: 'JDBC2608', 
  port: 5432,
});

module.exports = pool;