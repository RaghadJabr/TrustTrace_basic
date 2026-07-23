const express = require("express");
const cors = require("cors");
const path = require("path");
require("dotenv").config();

const pool = require("./src/db");
const assessmentRoutes = require("./src/routes/assessmentRoutes");
const app = express();
const PORT = Number(process.env.PORT) || 8000;

// Allows the backend to receive JSON data.
app.use(express.json());

// Allows frontend requests.
app.use(cors());
app.use("/api/assessments", assessmentRoutes);
app.use(express.json());
app.use(cors());

app.use("/api/assessments", assessmentRoutes);

// Basic server check.
app.get("/api/health", (req, res) => {
    res.status(200).json({
        status: "running",
        application: "TrustTrace",
        backend: "Node.js and Express",
    });
});


// PostgreSQL connection check.
app.get("/api/database/health", async (req, res) => {
    try {
        const result = await pool.query(`
      SELECT
        current_database() AS database_name,
        current_user AS database_user,
        NOW() AS server_time
    `);

        const database = result.rows[0];

        res.status(200).json({
            status: "connected",
            database: database.database_name,
            user: database.database_user,
            serverTime: database.server_time,
        });
    } catch (error) {
        console.error("Database health check failed:", error);

        res.status(500).json({
            status: "disconnected",
            message: "Could not connect to PostgreSQL.",
        });
    }
});


// Serve your existing HTML, CSS, and JavaScript frontend.
const staticFolder = path.join(__dirname, "app", "static");

app.use(express.static(staticFolder));

app.get("/", (req, res) => {
    res.sendFile(path.join(staticFolder, "index.html"));
});


// Start the server only after confirming PostgreSQL works.
async function startServer() {
    try {
        await pool.query("SELECT 1");

        console.log("PostgreSQL connection successful.");

        app.listen(PORT, () => {
            console.log(`TrustTrace running at http://127.0.0.1:${PORT}`);
            console.log(
                `Database health: http://127.0.0.1:${PORT}/api/database/health`
            );
        });
    } catch (error) {
        console.error("TrustTrace could not start.");
        console.error("PostgreSQL error:", error.message);
        process.exit(1);
    }
}

startServer();