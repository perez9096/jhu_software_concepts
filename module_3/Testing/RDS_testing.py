# Example Query Statement
# Project will use Postgresql setup

SELECT column1,
    AGG(column2) AS alias_name, column1
FROM table_name1 AS t1
WHERE WHERE_condition
GROUP BY column1
HAVING HAVING_condition
ORDER BY AGG(column2) DESC
JOIN table_name2 AS t2
ON t1.colummn2 = t2.column3;


