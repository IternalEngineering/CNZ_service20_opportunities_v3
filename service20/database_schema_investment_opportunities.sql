-- Service20 Investment Opportunities Database Schema
-- This creates the table for storing investment opportunity research results

-- Service20 Investment Opportunities Table
CREATE TABLE IF NOT EXISTS service20_investment_opportunities (
    id SERIAL PRIMARY KEY,

    -- Research query and results
    query TEXT NOT NULL,
    research_brief TEXT,
    final_report TEXT,
    notes JSONB DEFAULT '[]',

    -- City-specific information
    city VARCHAR(255),
    country_code VARCHAR(3),  -- ISO 3166-1 alpha-3
    country VARCHAR(255),
    region VARCHAR(255),  -- e.g., Western Europe, Southeast Asia

    -- Sector information
    sector VARCHAR(100),  -- Primary sector
    subsectors TEXT[],  -- Array of subsectors

    -- Research metadata
    research_iterations INTEGER DEFAULT 0,
    tool_calls_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    langfuse_trace_id TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255) DEFAULT 'research-agent'
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_service20_inv_city ON service20_investment_opportunities(city);
CREATE INDEX IF NOT EXISTS idx_service20_inv_country_code ON service20_investment_opportunities(country_code);
CREATE INDEX IF NOT EXISTS idx_service20_inv_country ON service20_investment_opportunities(country);
CREATE INDEX IF NOT EXISTS idx_service20_inv_sector ON service20_investment_opportunities(sector);
CREATE INDEX IF NOT EXISTS idx_service20_inv_created_at ON service20_investment_opportunities(created_at DESC);

-- GIN indexes for JSONB and array queries
CREATE INDEX IF NOT EXISTS idx_service20_inv_subsectors ON service20_investment_opportunities USING GIN (subsectors);
CREATE INDEX IF NOT EXISTS idx_service20_inv_metadata ON service20_investment_opportunities USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_service20_inv_notes ON service20_investment_opportunities USING GIN (notes);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_service20_inv_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_service20_inv_updated_at
    BEFORE UPDATE ON service20_investment_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_service20_inv_updated_at();

-- Comments for documentation
COMMENT ON TABLE service20_investment_opportunities IS 'Stores city-specific investment opportunity research results for Net Zero projects';
COMMENT ON COLUMN service20_investment_opportunities.country_code IS 'ISO 3166-1 alpha-3 country code (e.g., FRA, GBR, USA)';
COMMENT ON COLUMN service20_investment_opportunities.metadata IS 'JSONB field containing structured opportunity data, financial metrics, and project details';
COMMENT ON COLUMN service20_investment_opportunities.notes IS 'JSONB array of research findings and key insights';
