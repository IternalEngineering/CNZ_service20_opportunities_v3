-- Database schema for Service20 Match Proposals System
-- This table stores proposed matches between opportunities and funders

CREATE TABLE IF NOT EXISTS opportunity_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id VARCHAR(255) UNIQUE NOT NULL,
    match_type VARCHAR(50) NOT NULL, -- 'simple' (1:1), 'bundled' (1:many), 'syndicated' (many:1)

    -- Match participants (stored as JSON arrays)
    opportunity_alert_ids JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Array of opportunity alert IDs
    funder_alert_ids JSONB NOT NULL DEFAULT '[]'::jsonb,       -- Array of funder alert IDs

    -- Detailed participant data for easy querying
    opportunities_data JSONB NOT NULL DEFAULT '[]'::jsonb,  -- Full opportunity details
    funders_data JSONB NOT NULL DEFAULT '[]'::jsonb,         -- Full funder details

    -- Match quality metrics
    compatibility_score DECIMAL(5,2) NOT NULL,  -- 0.00 to 1.00
    confidence_level VARCHAR(20) NOT NULL,       -- 'high' (>0.80), 'medium' (0.60-0.80), 'low' (<0.60)

    -- Bundle calculations (for bundled matches)
    bundle_metrics JSONB,  -- {total_investment, blended_roi, carbon_reduction, etc.}

    -- Matching criteria
    criteria_met TEXT[] DEFAULT ARRAY[]::TEXT[],      -- List of criteria satisfied
    criteria_warnings TEXT[] DEFAULT ARRAY[]::TEXT[], -- Potential concerns

    -- Approval workflow
    requires_approval BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,

    -- Notification tracking
    notifications_sent BOOLEAN DEFAULT FALSE,
    notified_at TIMESTAMP,

    -- Proposal status (for tracking only, not enforced)
    status VARCHAR(50) DEFAULT 'proposed',  -- 'proposed', 'approved', 'notified'

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Add indexes for common queries
    CONSTRAINT valid_match_type CHECK (match_type IN ('simple', 'bundled', 'syndicated')),
    CONSTRAINT valid_confidence CHECK (confidence_level IN ('high', 'medium', 'low')),
    CONSTRAINT valid_score CHECK (compatibility_score >= 0 AND compatibility_score <= 1)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_matches_match_id ON opportunity_matches(match_id);
CREATE INDEX IF NOT EXISTS idx_matches_match_type ON opportunity_matches(match_type);
CREATE INDEX IF NOT EXISTS idx_matches_confidence ON opportunity_matches(confidence_level);
CREATE INDEX IF NOT EXISTS idx_matches_status ON opportunity_matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_created ON opportunity_matches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_matches_score ON opportunity_matches(compatibility_score DESC);
CREATE INDEX IF NOT EXISTS idx_matches_requires_approval ON opportunity_matches(requires_approval) WHERE requires_approval = TRUE;

-- GIN indexes for JSONB columns (for searching within JSON)
CREATE INDEX IF NOT EXISTS idx_matches_opportunity_ids ON opportunity_matches USING GIN (opportunity_alert_ids);
CREATE INDEX IF NOT EXISTS idx_matches_funder_ids ON opportunity_matches USING GIN (funder_alert_ids);
CREATE INDEX IF NOT EXISTS idx_matches_bundle_metrics ON opportunity_matches USING GIN (bundle_metrics);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_matches_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_matches_timestamp
    BEFORE UPDATE ON opportunity_matches
    FOR EACH ROW
    EXECUTE FUNCTION update_matches_updated_at();

-- Comment on table
COMMENT ON TABLE opportunity_matches IS 'Stores match proposals between investment opportunities and funding sources, including bundled opportunities';

-- Comments on key columns
COMMENT ON COLUMN opportunity_matches.match_type IS 'simple=1:1, bundled=1 funder:many opportunities, syndicated=many funders:1 opportunity';
COMMENT ON COLUMN opportunity_matches.compatibility_score IS 'Match quality score from 0.00 to 1.00 based on sector, financial, timeline, and technical alignment';
COMMENT ON COLUMN opportunity_matches.bundle_metrics IS 'For bundled matches: {total_investment, blended_roi, total_carbon_reduction, geographic_spread, etc.}';
COMMENT ON COLUMN opportunity_matches.requires_approval IS 'TRUE for medium/low confidence matches that need human review before notification';
COMMENT ON COLUMN opportunity_matches.status IS 'Informational only - Service20 just proposes, does not track acceptance';
