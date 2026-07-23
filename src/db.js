const { Pool } = require("pg");
require("dotenv").config();

const requiredVariables = [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
];

for (const variable of requiredVariables) {
    if (!process.env[variable]) {
        throw new Error(`Missing environment variable: ${variable}`);
    }
}

const pool = new Pool({
    host: process.env.DB_HOST,
    port: Number(process.env.DB_PORT),
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,

    // Local PostgreSQL usually does not require SSL.
    ssl:
        process.env.DB_SSL === "true"
            ? { rejectUnauthorized: false }
            : false,

    max: 10,
    connectionTimeoutMillis: 5000,
    idleTimeoutMillis: 30000,
});

pool.on("error", (error) => {
    console.error("Unexpected PostgreSQL connection error:", error);
});

module.exports = pool;