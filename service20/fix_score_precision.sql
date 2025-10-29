-- Fix score column precision to allow values 0-100
-- Change from DECIMAL(3,2) to DECIMAL(5,2)

ALTER TABLE service20_matches
ALTER COLUMN council_match_score TYPE DECIMAL(5,2);

ALTER TABLE service20_matches
ALTER COLUMN investor_match_score TYPE DECIMAL(5,2);

ALTER TABLE service20_matches
ALTER COLUMN provider_match_score TYPE DECIMAL(5,2);

ALTER TABLE service20_matches
ALTER COLUMN overall_match_score TYPE DECIMAL(5,2);

-- Also fix compatibility_score if it exists
ALTER TABLE service20_matches
ALTER COLUMN compatibility_score TYPE DECIMAL(5,2);

-- Verify the changes
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'service20_matches'
AND column_name LIKE '%score%';
