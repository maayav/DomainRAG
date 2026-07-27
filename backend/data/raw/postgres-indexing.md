# PostgreSQL Indexing

## Overview
Indexes in PostgreSQL are special lookup tables that database query planners can use to speed up data retrieval. Without an index, PostgreSQL performs a sequential scan, reading every row in the table. Indexes provide direct pointers to the relevant rows, dramatically reducing query time for large tables.

## Index Types

### B-Tree (Default)
B-Tree indexes are the default and most versatile index type. They work well for equality queries (`=`) and range queries (`<`, `<=`, `>`, `>=`, `BETWEEN`, `IN`). B-Tree indexes also support `ORDER BY` and `DISTINCT` operations.

### Hash
Hash indexes are optimized for simple equality comparisons. They are generally smaller than B-Tree indexes for the same data but cannot support range queries or ordering. In PostgreSQL 10+, hash indexes are WAL-logged and safe for production use.

### GIN (Generalized Inverted Index)
GIN indexes are designed for composite types where a single row contains multiple values. They excel at indexing arrays, JSONB documents, full-text search vectors, and tsvector columns. GIN indexes are larger and slower to build but provide fast lookup for "contains" queries.

### GiST (Generalized Search Tree)
GiST indexes support specialized operations like full-text search, geometric types, and range types. They are balanced for both search and update performance and support an "order by" operation with the `<->` distance operator for nearest-neighbor queries.

## Examples

### Creating Indexes
```sql
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_name ON users USING btree (last_name, first_name);
CREATE INDEX idx_orders_total ON orders USING btree (total DESC);
CREATE INDEX idx_docs_content ON documents USING gin (to_tsvector('english', content));
CREATE INDEX idx_products_tags ON products USING gin (tags);
```

### Using EXPLAIN ANALYZE
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'alice@example.com';
```

This shows whether an index scan or sequential scan is used and the actual execution time. Look for `Index Scan` or `Bitmap Index Scan` to confirm the index is being used.

### Best Practices
- Index columns used in `WHERE`, `JOIN`, and `ORDER BY` clauses
- Multi-column indexes are most effective when the leading column has high selectivity
- Avoid over-indexing — each index adds overhead to `INSERT`, `UPDATE`, and `DELETE`
- Use `pg_stat_user_indexes` and `pg_stat_all_indexes` to find unused indexes
- Consider partial indexes (`WHERE status = 'active'`) for targeted queries
- Use concurrent index creation (`CREATE INDEX CONCURRENTLY`) to avoid locking production tables