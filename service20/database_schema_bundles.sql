-- Service20 Bundles Database Schema
-- This creates the table for storing bundled project opportunities

-- Service20 Bundles Table
CREATE TABLE IF NOT EXISTS service20_bundles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bundle_id VARCHAR(255) UNIQUE NOT NULL,
    bundle_name VARCHAR(500) NOT NULL,
    bundle_description TEXT,

    -- Bundle composition
    opportunity_ids TEXT[] NOT NULL,  -- Array of opportunity research IDs
    opportunity_count INTEGER NOT NULL DEFAULT 0,

    -- Geographic distribution
    cities TEXT[] NOT NULL,  -- Array of city names
    countries TEXT[] NOT NULL,  -- Array of country names
    regions TEXT[] NOT NULL,  -- Array of regions (e.g., Europe, North America)

    -- Sector information
    primary_sector VARCHAR(100) NOT NULL,
    sectors TEXT[] NOT NULL,  -- All sectors involved
    subsectors TEXT[],  -- All subsectors

    -- Financial metrics
    total_investment DECIMAL(20, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    blended_roi DECIMAL(5, 2),  -- Average ROI across all projects
    roi_range_min DECIMAL(5, 2),
    roi_range_max DECIMAL(5, 2),

    -- Carbon impact
    total_carbon_reduction DECIMAL(15, 2),  -- Total tons/year across all projects
    average_carbon_per_project DECIMAL(15, 2),

    -- Timeline alignment
    earliest_start_date DATE,
    latest_completion_date DATE,
    timeline_alignment_score DECIMAL(3, 2),  -- 0.00 to 1.00

    -- Technical compatibility
    technologies TEXT[],  -- Array of technologies used
    total_capacity_mw DECIMAL(10, 2),  -- Total capacity if applicable

    -- Bundle metrics
    bundle_metrics JSONB NOT NULL DEFAULT '{}',  -- Detailed bundle analysis

    -- Compatibility and scoring
    compatibility_score DECIMAL(3, 2),  -- 0.00 to 1.00
    confidence_level VARCHAR(20) CHECK (confidence_level IN ('low', 'medium', 'high')),
    bundling_rationale TEXT,  -- Why these projects bundle well

    -- Matching status
    status VARCHAR(50) DEFAULT 'proposed' CHECK (status IN ('proposed', 'matched', 'approved', 'rejected', 'active', 'completed')),
    matched_funder_id VARCHAR(255),  -- Research ID of matched funder if any
    match_date TIMESTAMP,

    -- Requirements
    minimum_funder_capacity DECIMAL(20, 2),  -- Minimum funder requirement
    preferred_funder_types TEXT[],  -- e.g., ['impact_investor', 'development_bank']

    -- Enhanced criteria stored as JSONB
    criteria JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    created_by VARCHAR(255) DEFAULT 'api-system-user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Langfuse tracking
    langfuse_trace_id TEXT
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_service20_bundles_bundle_id ON service20_bundles(bundle_id);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_status ON service20_bundles(status);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_primary_sector ON service20_bundles(primary_sector);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_created_at ON service20_bundles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_compatibility_score ON service20_bundles(compatibility_score DESC);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_confidence_level ON service20_bundles(confidence_level);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_matched_funder ON service20_bundles(matched_funder_id);

-- GIN indexes for array and JSONB queries
CREATE INDEX IF NOT EXISTS idx_service20_bundles_cities ON service20_bundles USING GIN (cities);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_sectors ON service20_bundles USING GIN (sectors);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_opportunity_ids ON service20_bundles USING GIN (opportunity_ids);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_criteria ON service20_bundles USING GIN (criteria);
CREATE INDEX IF NOT EXISTS idx_service20_bundles_bundle_metrics ON service20_bundles USING GIN (bundle_metrics);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_service20_bundles_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_service20_bundles_updated_at
    BEFORE UPDATE ON service20_bundles
    FOR EACH ROW
    EXECUTE FUNCTION update_service20_bundles_updated_at();

-- Comments for documentation
COMMENT ON TABLE service20_bundles IS 'Stores bundled project opportunities with enhanced metadata for intelligent matching';
COMMENT ON COLUMN service20_bundles.opportunity_ids IS 'Array of research IDs from service20_investment_opportunities that are bundled together';
COMMENT ON COLUMN service20_bundles.bundle_metrics IS 'JSONB field containing detailed bundle analysis, synergies, and compatibility metrics';
COMMENT ON COLUMN service20_bundles.criteria IS 'JSONB field containing structured criteria including requirements, preferences, and constraints';
COMMENT ON COLUMN service20_bundles.compatibility_score IS 'Overall compatibility score for the bundle (0.00 to 1.00)';
COMMENT ON COLUMN service20_bundles.timeline_alignment_score IS 'How well aligned the project timelines are (0.00 to 1.00)';
