# Global Plan for SQL Query Agent Project

## 1. Specialized Protocols for SQL Query Generation

### A. Query Type Restrictions
1. **SELECT Queries Only**
   - Limit to SELECT statements for data retrieval
   - No DDL (CREATE, ALTER, DROP)
   - No DML (INSERT, UPDATE, DELETE)
   - No DCL (GRANT, REVOKE)
   - Avoid SELECT * - specify columns explicitly for better performance

### B. Query Generation Protocol
1. **Query Construction Rules**
   - Always start with SELECT
   - Apply LIMIT for result size control (warning user)

2. **Metadata**
   - Include query execution time
   - Show number of rows returned
   - Provide query explanation

### C. Learning and Improvement Protocol
1. **Feedback Collection**
   - Monitor query performance
