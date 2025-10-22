-- Service20 Funding Opportunities Database Schema
-- This creates the table for storing funder/investor research results

-- Service20 Funding Opportunities Table
CREATE TABLE IF NOT EXISTS service20_funding_opportunities (
    id SERIAL PRIMARY KEY,

    -- Research query and results
    query TEXT NOT NULL,
    research_brief TEXT,
    final_report TEXT,
    notes JSONB DEFAULT '[]',

    -- Funder identification
    funder_name VARCHAR(500),
    funder_type VARCHAR(100),  -- impact_investor, development_bank, private_equity, venture_capital, green_bond, government_grant, corporate_fund, family_office, foundation
    funder_subtype VARCHAR(100),  -- e.g., multilateral_development_bank, bilateral_development_bank, climate_fund
    organization_type VARCHAR(100),  -- public, private, non_profit, multilateral

    -- Geographic focus
    geographic_scope VARCHAR(50),  -- global, continental, multi_national, national, regional, city
    continent TEXT[],  -- Array of continents (Europe, North America, Asia, etc.)
    countries TEXT[],  -- Array of ISO country codes or names
    regions TEXT[],  -- Array of regions (Western Europe, Southeast Asia, etc.)
    cities TEXT[],  -- Array of specific cities if city-level

    -- Sector focus
    primary_sector VARCHAR(100),
    sectors TEXT[],  -- Array of sectors they fund
    subsectors TEXT[],  -- More specific subsectors
    excluded_sectors TEXT[],  -- Sectors they DON'T fund

    -- Financial criteria
    total_fund_size DECIMAL(20,2),  -- Total assets under management
    currency VARCHAR(10) DEFAULT 'USD',
    min_investment DECIMAL(20,2),  -- Minimum ticket size
    max_investment DECIMAL(20,2),  -- Maximum ticket size
    typical_investment DECIMAL(20,2),  -- Typical ticket size

    -- Investment structure
    investment_types TEXT[],  -- equity, debt, grant, blended_finance, guarantee, etc.
    financial_instruments TEXT[],  -- senior_debt, subordinated_debt, convertible_note, etc.

    -- Return expectations
    min_roi_requirement DECIMAL(5,2),  -- Minimum ROI expected (%)
    target_roi DECIMAL(5,2),  -- Target ROI (%)
    max_acceptable_roi DECIMAL(5,2),  -- Maximum ROI they'll accept
    accepts_below_market_returns BOOLEAN DEFAULT FALSE,
    concessional_finance BOOLEAN DEFAULT FALSE,  -- Willing to provide below-market rates

    -- Timeline and terms
    investment_horizon_min INTEGER,  -- Minimum years
    investment_horizon_max INTEGER,  -- Maximum years
    typical_timeline VARCHAR(50),  -- e.g., "5-10 years"

    -- Project stage preferences
    project_stages TEXT[],  -- early_stage, development, construction, operational, refinancing
    technology_maturity TEXT[],  -- pilot, proven, mature, emerging

    -- ESG and impact criteria
    requires_carbon_metrics BOOLEAN DEFAULT FALSE,
    min_carbon_reduction DECIMAL(15,2),  -- Minimum tons CO2/year
    sdg_alignment TEXT[],  -- UN SDG goals required
    impact_measurement_required BOOLEAN DEFAULT FALSE,

    -- Application process
    application_process TEXT,  -- Description of how to apply
    application_url TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    decision_timeline VARCHAR(100),  -- e.g., "3-6 months"

    -- Requirements and restrictions
    requires_co_financing BOOLEAN DEFAULT FALSE,
    min_co_financing_percent DECIMAL(5,2),
    local_participation_required BOOLEAN DEFAULT FALSE,
    min_local_participation_percent DECIMAL(5,2),

    -- Historical performance
    active_portfolio_count INTEGER,
    total_projects_funded INTEGER,
    average_deal_size DECIMAL(20,2),
    recent_deals JSONB DEFAULT '[]',  -- Array of recent deal examples

    -- Availability and status
    currently_accepting BOOLEAN DEFAULT TRUE,
    next_call_date DATE,
    deadline_date DATE,
    fund_status VARCHAR(50) DEFAULT 'active',  -- active, closed, fundraising, deploying

    -- Research metadata
    research_iterations INTEGER DEFAULT 0,
    tool_calls_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    langfuse_trace_id TEXT,

    -- Source information
    sources JSONB DEFAULT '[]',  -- Array of source URLs and documents
    last_verified_date DATE,
    data_quality_score DECIMAL(3,2),  -- 0.00 to 1.00

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255) DEFAULT 'research-agent'
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_service20_funding_funder_type ON service20_funding_opportunities(funder_type);
CREATE INDEX IF NOT EXISTS idx_service20_funding_geographic_scope ON service20_funding_opportunities(geographic_scope);
CREATE INDEX IF NOT EXISTS idx_service20_funding_primary_sector ON service20_funding_opportunities(primary_sector);
CREATE INDEX IF NOT EXISTS idx_service20_funding_currently_accepting ON service20_funding_opportunities(currently_accepting);
CREATE INDEX IF NOT EXISTS idx_service20_funding_fund_status ON service20_funding_opportunities(fund_status);
CREATE INDEX IF NOT EXISTS idx_service20_funding_created_at ON service20_funding_opportunities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_service20_funding_min_investment ON service20_funding_opportunities(min_investment);
CREATE INDEX IF NOT EXISTS idx_service20_funding_max_investment ON service20_funding_opportunities(max_investment);

-- GIN indexes for array and JSONB queries
CREATE INDEX IF NOT EXISTS idx_service20_funding_countries ON service20_funding_opportunities USING GIN (countries);
CREATE INDEX IF NOT EXISTS idx_service20_funding_sectors ON service20_funding_opportunities USING GIN (sectors);
CREATE INDEX IF NOT EXISTS idx_service20_funding_investment_types ON service20_funding_opportunities USING GIN (investment_types);
CREATE INDEX IF NOT EXISTS idx_service20_funding_project_stages ON service20_funding_opportunities USING GIN (project_stages);
CREATE INDEX IF NOT EXISTS idx_service20_funding_metadata ON service20_funding_opportunities USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_service20_funding_recent_deals ON service20_funding_opportunities USING GIN (recent_deals);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_service20_funding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_service20_funding_updated_at
    BEFORE UPDATE ON service20_funding_opportunities
    FOR EACH ROW
    EXECUTE FUNCTION update_service20_funding_updated_at();

-- Comments for documentation
COMMENT ON TABLE service20_funding_opportunities IS 'Stores research on funders, investors, and grant programs for Net Zero projects';
COMMENT ON COLUMN service20_funding_opportunities.funder_type IS 'Type of funder: impact_investor, development_bank, private_equity, venture_capital, green_bond, government_grant, corporate_fund, family_office, foundation';
COMMENT ON COLUMN service20_funding_opportunities.geographic_scope IS 'Geographic reach: global, continental, multi_national, national, regional, city';
COMMENT ON COLUMN service20_funding_opportunities.investment_types IS 'Array of investment types: equity, debt, grant, blended_finance, guarantee, technical_assistance';
COMMENT ON COLUMN service20_funding_opportunities.project_stages IS 'Preferred project stages: early_stage, development, construction, operational, refinancing';
COMMENT ON COLUMN service20_funding_opportunities.concessional_finance IS 'TRUE if funder provides below-market financing terms for impact';
COMMENT ON COLUMN service20_funding_opportunities.recent_deals IS 'JSONB array of recent deal examples with project details and terms';
