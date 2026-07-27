# SQL JOINs

## Overview

SQL JOINs are used to combine rows from two or more tables based on a related column between them. They are fundamental to relational database queries, enabling the retrieval of data spread across normalized tables. Without JOINs, working with relational databases would be impractical, as related data would need to be fetched in separate queries and assembled in application code.

## Details

### INNER JOIN

Returns only the rows where there is a match in both tables. If a row in the left table has no matching row in the right table, it is excluded from the result set. This is the most commonly used JOIN type.

### LEFT JOIN (or LEFT OUTER JOIN)

Returns all rows from the left table and the matched rows from the right table. If no match exists in the right table, NULL values are returned for the right table's columns. This is useful when you need every record from the primary table regardless of whether related data exists.

### RIGHT JOIN (or RIGHT OUTER JOIN)

The mirror of LEFT JOIN. It returns all rows from the right table and the matched rows from the left table. Many developers avoid RIGHT JOIN in favor of LEFT JOIN by swapping table order, as it tends to be more readable.

### FULL JOIN (or FULL OUTER JOIN)

Returns all rows from both tables. Where a match is found in either table, the corresponding row from the other table is included. Where no match exists, NULLs fill the missing side. FULL JOIN is less commonly used but valuable for finding orphaned records on both sides.

### CROSS JOIN

Produces a Cartesian product of both tables, pairing every row from the first table with every row from the second. No join condition is specified. CROSS JOINs can generate very large result sets and are typically used for generating test data or enumeration tasks.

## Examples

```sql
-- Sample tables: employees (id, name, dept_id) and departments (id, name)

-- INNER JOIN: employees with their department names
SELECT e.name, d.name AS department
FROM employees e
INNER JOIN departments d ON e.dept_id = d.id;

-- LEFT JOIN: all employees, even those without a department
SELECT e.name, d.name AS department
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.id;

-- RIGHT JOIN: all departments, even those with no employees
SELECT e.name, d.name AS department
FROM employees e
RIGHT JOIN departments d ON e.dept_id = d.id;

-- FULL JOIN: all employees and all departments
SELECT e.name, d.name AS department
FROM employees e
FULL JOIN departments d ON e.dept_id = d.id;

-- CROSS JOIN: every employee paired with every department
SELECT e.name AS employee, d.name AS department
FROM employees e
CROSS JOIN departments d;

-- Self-join: employees and their managers (manager_id references same table)
SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

Performance considerations: JOINs on unindexed foreign key columns can cause full table scans. Always ensure join columns are indexed, especially in large tables. Use `EXPLAIN ANALYZE` to examine query plans and identify slow JOIN operations.
