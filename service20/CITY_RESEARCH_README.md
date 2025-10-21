# City-Specific Investment Opportunity Research

## Overview

The `research_city_opportunity.py` script provides a structured way to research Net Zero investment opportunities for specific cities. It requires both city name and country code to ensure accurate, location-specific research.

## Database Schema Updates

The `service20_investment_opportunities` table has been updated with new columns:

- `city` (VARCHAR 255) - City name
- `country_code` (VARCHAR 3) - ISO 3166-1 alpha-3 country code
- `country` (VARCHAR 255) - Full country name
- `sector` (VARCHAR 100) - Primary sector

Indexes have been created on `city`, `country_code`, and `sector` for optimal query performance.

## Usage

### Basic Usage

```bash
python research_city_opportunity.py --city CITY_NAME --country COUNTRY_CODE
```

### Examples

```bash
# Research Paris renewable energy opportunities
python research_city_opportunity.py --city Paris --country FRA

# Research London solar energy with default investment range
python research_city_opportunity.py --city London --country GBR --sector solar_energy

# Research New York wind energy with custom investment range
python research_city_opportunity.py --city "New York" --country USA --sector wind_energy --range 1000000-10000000

# Research Berlin energy storage
python research_city_opportunity.py --city Berlin --country DEU --sector energy_storage

# Research Tokyo sustainable transport
python research_city_opportunity.py --city Tokyo --country JPN --sector sustainable_transport --range 2000000-20000000
```

## Parameters

### Required Parameters

- `--city`: City name (e.g., "Paris", "London", "New York")
  - Use quotes if city name contains spaces

- `--country`: ISO 3166-1 alpha-3 country code (e.g., FRA, GBR, USA)
  - Must be a valid 3-letter country code

### Optional Parameters

- `--sector`: Primary sector (default: `renewable_energy`)
  - Options:
    - `renewable_energy` - General renewable energy projects
    - `solar_energy` - Solar panel installations
    - `wind_energy` - Wind turbine projects
    - `energy_storage` - Battery storage systems
    - `green_buildings` - Energy-efficient building retrofits
    - `sustainable_transport` - EV infrastructure, public transit
    - `waste_management` - Waste-to-energy, recycling
    - `water_management` - Water treatment, conservation

- `--range`: Investment range in USD (default: `500000-5000000`)
  - Format: `MIN-MAX` (e.g., `1000000-10000000`)

## Supported Countries

The script includes 30+ supported countries with their ISO codes:

| Code | Country              | Code | Country              |
|------|---------------------|------|---------------------|
| USA  | United States       | GBR  | United Kingdom      |
| FRA  | France              | DEU  | Germany             |
| ESP  | Spain               | ITA  | Italy               |
| NLD  | Netherlands         | BEL  | Belgium             |
| SWE  | Sweden              | NOR  | Norway              |
| DNK  | Denmark             | FIN  | Finland             |
| POL  | Poland              | CZE  | Czech Republic      |
| AUT  | Austria             | CHE  | Switzerland         |
| CAN  | Canada              | AUS  | Australia           |
| NZL  | New Zealand         | JPN  | Japan               |
| KOR  | South Korea         | SGP  | Singapore           |
| IND  | India               | CHN  | China               |
| BRA  | Brazil              | MEX  | Mexico              |
| ARG  | Argentina           | CHL  | Chile               |
| ZAF  | South Africa        | ARE  | UAE                 |
| SAU  | Saudi Arabia        |      |                     |

To see the full list, run:
```bash
python research_city_opportunity.py --city Test --country XXX
```

## Output

The script will:

1. Validate city and country inputs
2. Generate a comprehensive research prompt
3. Execute deep research using the LangGraph workflow
4. Store results in the database with city/country metadata
5. Display:
   - Research brief summary
   - Report statistics (length, findings count)
   - Report preview (first 500 characters)
   - Database record ID
   - Next steps

### Database Storage

Results are stored in `service20_investment_opportunities` table with:

- Full research query and report
- City, country code, and country name
- Sector classification
- Metadata (notes count, report length)
- Langfuse trace ID (if available)
- Timestamps (created_at, updated_at)

## Research Output

Each research run produces:

1. **Executive Summary** - High-level overview
2. **3-5 Project Proposals** - Specific, actionable opportunities
3. **Financial Analysis** - Investment amounts, ROI, payback periods
4. **Carbon Impact** - Quantified CO2 reduction (tons/year)
5. **Implementation Roadmap** - Timelines and milestones
6. **Risk Assessment** - Potential challenges and mitigation
7. **Funding Recommendations** - Partnership opportunities

## Next Steps After Research

1. **Review Database Record**
   ```sql
   SELECT * FROM service20_investment_opportunities WHERE id = [RECORD_ID];
   ```

2. **Create Alert for Matching**
   - Use the research ID to create an alert in `service20_alerts`
   - Alert will be used by matching engine to find compatible funders

3. **Run Matching Job**
   - Daily matching job will process the alert
   - Find compatible funding opportunities
   - Generate bundling recommendations

4. **View in Dashboard**
   - Open `runs_dashboard.html`
   - Navigate to "Research History" tab
   - Filter by city or sector

## Technical Details

### Research Prompt Structure

The script generates a detailed research prompt including:

- City and country context
- Sector focus
- Investment range constraints
- Specific deliverables (ROI, carbon metrics, timelines)
- Municipal and city-level focus
- Reference to official sources (government, environmental orgs)

### Database Integration

The `store_investment_research()` function in `database_storage.py`:

- Accepts structured research data
- Validates required fields (city, country_code)
- Stores in PostgreSQL with proper typing
- Returns database record ID for reference

### Error Handling

The script includes comprehensive error handling:

- Country code validation with helpful error messages
- Database connection error handling
- Research execution error handling
- Graceful failure with detailed error messages

## Troubleshooting

### Invalid Country Code

```
ERROR: Invalid country code 'XX'

Supported country codes:
  AUS: Australia
  ...
```

**Solution**: Use a valid 3-letter ISO country code from the supported list.

### Database Connection Error

```
ERROR: DATABASE_URL not set
```

**Solution**: Ensure `.env` file contains valid `DATABASE_URL`.

### Research Timeout

If research takes too long:
- Check Langfuse trace ID for debugging
- Review OpenAI API rate limits
- Consider simpler research prompts

## Best Practices

1. **City Naming**
   - Use official city names
   - Include quotes for multi-word names: `--city "New York"`

2. **Investment Range**
   - Match to city size (larger ranges for major cities)
   - Consider local economic context

3. **Sector Selection**
   - Research one sector at a time for focused results
   - Run multiple researches for comprehensive coverage

4. **Follow-up Actions**
   - Always review database record after research
   - Create alerts promptly for matching
   - Document findings in project management system

## Example Workflow

```bash
# 1. Research Paris solar opportunities
python research_city_opportunity.py --city Paris --country FRA --sector solar_energy

# Output shows:
# Research ID: 42
# City: Paris, France
# Sector: solar_energy

# 2. Review in database
# SELECT * FROM service20_investment_opportunities WHERE id = 42;

# 3. Check dashboard
# Open runs_dashboard.html → Research History tab

# 4. Create alert (manual or automated)
# 5. Wait for daily matching job
# 6. Review matches in dashboard
```

## Integration with Service20 Workflow

This script is part of the Service20 intelligent matching system:

```
1. City Research (this script)
   ↓
2. Store in Database
   ↓
3. Create Alert
   ↓
4. Daily Matching Job
   ↓
5. Find Compatible Funders
   ↓
6. Bundle Similar Projects
   ↓
7. Notify Participants
```

## Support

For issues or questions:
1. Check database logs: `SELECT * FROM service20_investment_opportunities ORDER BY created_at DESC;`
2. Review Langfuse traces for debugging
3. Check CloudWatch logs (if deployed to AWS)
