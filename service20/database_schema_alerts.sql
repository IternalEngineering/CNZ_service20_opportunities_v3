-- Service20 Alerts Database Schema
-- This creates the tables needed for storing research alerts with enhanced metadata

-- Service20 Alerts Table
CREATE TABLE IF NOT EXISTS service20_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) DEFAULT 'api-system-user',
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('investment', 'funding')),

    -- Basic info
    title TEXT,
    description TEXT,

    -- Enhanced criteria stored as JSONB
    criteria JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Status
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'matched', 'expired', 'cancelled'))
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_service20_alerts_research_id ON service20_alerts(research_id);
CREATE INDEX IF NOT EXISTS idx_service20_alerts_type ON service20_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_service20_alerts_created_at ON service20_alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_service20_alerts_status ON service20_alerts(status);

-- GIN index for JSONB criteria queries
CREATE INDEX IF NOT EXISTS idx_service20_alerts_criteria ON service20_alerts USING GIN (criteria);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_service20_alerts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at
CREATE TRIGGER trigger_update_service20_alerts_updated_at
    BEFORE UPDATE ON service20_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_service20_alerts_updated_at();

-- Comments for documentation
COMMENT ON TABLE service20_alerts IS 'Stores research alerts with enhanced metadata for intelligent matching';
COMMENT ON COLUMN service20_alerts.criteria IS 'JSONB field containing structured criteria including sector, financial, location, timeline, technical, and bundling information';
COMMENT ON COLUMN service20_alerts.alert_type IS 'Type of alert: investment (city seeking funding) or funding (funder seeking projects)';
