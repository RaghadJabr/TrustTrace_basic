const pool = require("./src/db");

async function testDatabase() {
    try {
        const result = await pool.query(`
      SELECT
        current_database() AS database_name,
        current_user AS database_user,
        COUNT(*)::integer AS transaction_count
      FROM transactions
    `);

        const row = result.rows[0];

        console.log("PostgreSQL connection successful.");
        console.log(`Database: ${row.database_name}`);
        console.log(`User: ${row.database_user}`);
        console.log(`Transactions: ${row.transaction_count}`);
    } catch (error) {
        console.error("PostgreSQL connection failed.");
        console.error(error.message);
        process.exitCode = 1;
    } finally {
        await pool.end();
    }
}

testDatabase();