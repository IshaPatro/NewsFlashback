# NewsFlashback - Financial News Analysis System

## Connection Troubleshooting Guide

### Neo4j Connection Issue

If you're experiencing the following error when running the application:

```
Cannot resolve address 0a6ba303.databases.neo4j.io:7687
```

This indicates a DNS resolution issue with your Neo4j Aura database. This typically happens when:

1. The Neo4j Aura database instance no longer exists or has been renamed
2. There's a network connectivity issue preventing DNS resolution
3. The database ID in the connection URL is incorrect

### How to Fix

1. **Run the connection fix script**:
   ```
   python3 fix_neo4j_connection.py
   ```
   This interactive script will guide you through updating your Neo4j connection details.

2. **Verify your Neo4j Aura database**:
   - Log in to your [Neo4j Aura Console](https://console.neo4j.io/)
   - Check if your database is active and not paused
   - Get the correct connection details from the database information page

3. **Test the connection**:
   ```
   python3 test_neo4j_connection.py
   ```
   This will verify if your connection details are correct.

4. **Update your .env file manually** (if needed):
   Make sure your `.env` file contains the correct Neo4j connection details:
   ```
   NEO4J_URL = "neo4j+s://your-db-id.databases.neo4j.io"
   NEO4J_USER = "neo4j"
   NEO4J_PASSWORD = "your-password"
   ```

## Running the Application

Once you've fixed the connection issue, you can run the main application:

```
python3 NewsFlashback.py
```