-- Migration: Rename service20_bundles to service20_matches
-- This table will now store three-way match results instead of just bundles

-- Step 1: Rename the table
ALTER TABLE IF EXISTS service20_bundles RENAME TO service20_matches;

-- Step 2: Rename indexes
ALTER INDEX IF EXISTS idx_service20_bundles_bundle_id RENAME TO idx_service20_matches_match_id;
ALTER INDEX IF EXISTS idx_service20_bundles_status RENAME TO idx_service20_matches_status;
ALTER INDEX IF EXISTS idx_service20_bundles_primary_sector RENAME TO idx_service20_matches_primary_sector;
ALTER INDEX IF EXISTS idx_service20_bundles_created_at RENAME TO idx_service20_matches_created_at;
ALTER INDEX IF EXISTS idx_service20_bundles_compatibility_score RENAME TO idx_service20_matches_compatibility_score;
ALTER INDEX IF EXISTS idx_service20_bundles_confidence_level RENAME TO idx_service20_matches_confidence_level;
ALTER INDEX IF EXISTS idx_service20_bundles_matched_funder RENAME TO idx_service20_matches_matched_funder;
ALTER INDEX IF EXISTS idx_service20_bundles_cities RENAME TO idx_service20_matches_cities;
ALTER INDEX IF EXISTS idx_service20_bundles_sectors RENAME TO idx_service20_matches_sectors;
ALTER INDEX IF EXISTS idx_service20_bundles_opportunity_ids RENAME TO idx_service20_matches_opportunity_ids;
ALTER INDEX IF EXISTS idx_service20_bundles_criteria RENAME TO idx_service20_matches_criteria;
ALTER INDEX IF EXISTS idx_service20_bundles_bundle_metrics RENAME TO idx_service20_matches_match_metrics;

-- Step 3: Rename column bundle_id to match_id
ALTER TABLE service20_matches RENAME COLUMN bundle_id TO match_id;

-- Step 4: Rename bundle_metrics to match_metrics
ALTER TABLE service20_matches RENAME COLUMN bundle_metrics TO match_metrics;

-- Step 5: Rename the trigger function
ALTER FUNCTION update_service20_bundles_updated_at() RENAME TO update_service20_matches_updated_at;

-- Step 6: Drop old trigger and create new one
DROP TRIGGER IF EXISTS trigger_update_service20_bundles_updated_at ON service20_matches;
CREATE TRIGGER trigger_update_service20_matches_updated_at
    BEFORE UPDATE ON service20_matches
    FOR EACH ROW
    EXECUTE FUNCTION update_service20_matches_updated_at();

-- Step 7: Add new columns for three-way matching
ALTER TABLE service20_matches
ADD COLUMN IF NOT EXISTS council_doc_url TEXT,
ADD COLUMN IF NOT EXISTS investor_doc_url TEXT,
ADD COLUMN IF NOT EXISTS provider_doc_url TEXT,
ADD COLUMN IF NOT EXISTS council_match_score DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS investor_match_score DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS provider_match_score DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS overall_match_score DECIMAL(5,2),
ADD COLUMN IF NOT EXISTS match_analysis TEXT,
ADD COLUMN IF NOT EXISTS recommendations TEXT[],
ADD COLUMN IF NOT EXISTS match_failed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS failure_reason TEXT;

-- Step 8: Update table comment
COMMENT ON TABLE service20_matches IS 'Stores three-way match results (council-investor-provider) for investment opportunities';
COMMENT ON COLUMN service20_matches.match_id IS 'Unique identifier for this match';
COMMENT ON COLUMN service20_matches.match_metrics IS 'JSONB field containing detailed match analysis and compatibility metrics';
COMMENT ON COLUMN service20_matches.council_doc_url IS 'URL to council requirements document used for matching';
COMMENT ON COLUMN service20_matches.investor_doc_url IS 'URL to investor criteria document used for matching';
COMMENT ON COLUMN service20_matches.provider_doc_url IS 'URL to service provider capabilities document used for matching';
COMMENT ON COLUMN service20_matches.council_match_score IS 'Match score with council requirements (0-100)';
COMMENT ON COLUMN service20_matches.investor_match_score IS 'Match score with investor criteria (0-100)';
COMMENT ON COLUMN service20_matches.provider_match_score IS 'Match score with provider capabilities (0-100)';
COMMENT ON COLUMN service20_matches.overall_match_score IS 'Overall three-way match score (0-100)';
COMMENT ON COLUMN service20_matches.match_analysis IS 'Detailed compatibility analysis text';
COMMENT ON COLUMN service20_matches.recommendations IS 'Array of actionable recommendations';
COMMENT ON COLUMN service20_matches.match_failed IS 'TRUE if no suitable terms were found';
COMMENT ON COLUMN service20_matches.failure_reason IS 'Reason why matching failed if match_failed is TRUE';

-- Step 9: Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_service20_matches_overall_score ON service20_matches(overall_match_score DESC);
CREATE INDEX IF NOT EXISTS idx_service20_matches_match_failed ON service20_matches(match_failed);

-- Verification queries
-- SELECT tablename FROM pg_tables WHERE tablename = 'service20_matches';
-- SELECT indexname FROM pg_indexes WHERE tablename = 'service20_matches';
-- \d service20_matches
