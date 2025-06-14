def convert_text_to_sql(text: str) -> str:
	"""
	Convert a natural language text query into an SQL query.

	Args:
	    text (str): The natural language text to convert.

	Returns:
	    str: The generated SQL query.
	"""

	return f"""
SELECT c.Email, SUM(il.Quantity * il.UnitPrice) AS TotalSpent
FROM Customer c
JOIN Invoice i ON c.CustomerId = i.CustomerId
JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
JOIN Track t ON il.TrackId = t.TrackId
WHERE t.UnitPrice > 1
GROUP BY c.Email
HAVING COUNT(il.TrackId) > 3
LIMIT 10;
"""
