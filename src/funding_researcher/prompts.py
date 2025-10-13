"""Prompts for the funding research agent."""

QUERY_GENERATOR_PROMPT = """You are an expert at generating targeted search queries to find funding opportunities for Net Zero and sustainability projects.

Given a project description and geographic level, generate specific search queries that will help find relevant funding opportunities.

Project Description: {project_description}
Project Location: {project_location}
Project Sectors: {project_sectors}
Funding Types Sought: {funding_types}
Current Research Level: {level}

Generate 5-8 diverse search queries that will help find {level} funding opportunities. Include:
- Specific funding program names
- Government schemes and initiatives
- Private sector investment opportunities
- Grant databases and funding portals
- Regional development funds (for regional level)
- National innovation programs (for national level)
- International climate finance (for global level)

For each query, consider:
- Net Zero, carbon reduction, and sustainability focus
- The specific sectors involved
- The geographic scope ({level})
- Different funding mechanisms (grants, loans, equity, tax incentives)

Return ONLY a JSON list of search query strings, like:
["query 1", "query 2", "query 3", ...]

No additional explanation or formatting."""


FUNDER_EXTRACTOR_PROMPT = """You are an expert at extracting and structuring funding opportunity information from search results.

Analyze the following search results and extract detailed information about funding opportunities for Net Zero projects.

Project Context:
- Description: {project_description}
- Location: {project_location}
- Sectors: {project_sectors}
- Funding Types: {funding_types}
- Geographic Level: {level}

Search Results:
{search_results}

Extract ALL relevant funding opportunities found in these results. For each funder, provide:

1. **Name**: The funding program or opportunity name
2. **Organization**: The organization providing the funding
3. **Level**: {level} (the current geographic level being researched)
4. **Location**: Geographic coverage area
5. **Opportunity Type**: Grant, Loan, Equity, Tax Credit, etc.
6. **Award Range**: Amount or range of funding available
7. **Sectors**: Relevant sectors from: Agrifood, Biotechnology, Chemistry, Creative Industries, Design, Digital, Electronics, Energy, Geospatial, Health, Industrial Maths, Infrastructure, Investment, Manufacturing, Materials, Photonics, Place, Quantum, Robotics & AI, Security & Defence, Sensors, Space, Sustainability, Transport, Water
8. **Registration Details**: When applications open, deadlines, or if rolling basis
9. **Eligibility**: Who can apply (SMEs, startups, corporations, non-profits, etc.)
10. **Website**: Official URL for the funding program
11. **Contact Info**: Email, phone, or contact person if available
12. **Additional Notes**: Any other relevant information
13. **Source URL**: The URL where this information was found

Return ONLY a JSON list of funding opportunities with this exact structure:
[
  {{
    "name": "Funding Program Name",
    "organization": "Organization Name",
    "level": "{level}",
    "location": "Geographic area",
    "opportunity_type": "Grant/Loan/Equity/etc",
    "award_range": "£X - £Y or specific amount",
    "sectors": ["Sector1", "Sector2"],
    "registration_details": "Application details",
    "eligibility": "Who can apply",
    "website": "https://...",
    "contact_info": "Contact details",
    "additional_notes": "Other info",
    "source_url": "https://..."
  }}
]

Include ONLY genuine funding opportunities that are currently active or have regular funding rounds. Do not include expired programs or placeholder information."""


REPORT_GENERATOR_PROMPT = """You are an expert at creating comprehensive funding research reports for Net Zero projects.

Generate a detailed, well-structured report summarizing all funding opportunities found across regional, national, and global levels.

Project Information:
- Description: {project_description}
- Location: {project_location}
- Sectors: {project_sectors}
- Funding Types Sought: {funding_types}

Funding Opportunities Found:

## Regional Funders ({regional_count})
{regional_funders}

## National Funders ({national_count})
{national_funders}

## Global Funders ({global_count})
{global_funders}

Create a comprehensive report with the following sections:

1. **Executive Summary**
   - Total number of funding opportunities identified
   - Breakdown by geographic level
   - Key findings and recommendations

2. **Regional Funding Opportunities**
   - Detailed list of each regional funder
   - For each: name, organization, award range, application process, eligibility, contact info

3. **National Funding Opportunities**
   - Detailed list of each national funder
   - For each: name, organization, award range, application process, eligibility, contact info

4. **Global Funding Opportunities**
   - Detailed list of each global funder
   - For each: name, organization, award range, application process, eligibility, contact info

5. **Sector Analysis**
   - Which sectors have the most funding available
   - Sector-specific opportunities

6. **Funding Type Analysis**
   - Breakdown by type (grants, loans, equity, etc.)
   - Advantages of each funding type for this project

7. **Application Strategy Recommendations**
   - Priority funders to target first
   - Timeline for applications
   - Tips for maximizing funding success

8. **Quick Reference Table**
   - Summary table with key details for all funders

Format the report in clear, professional markdown with proper headings, bullet points, and tables where appropriate.
Make it actionable and easy to navigate."""


RESEARCH_PLANNER_PROMPT = """You are an expert research planner for funding opportunities.

Given a Net Zero project, create a strategic research plan for finding funders at regional, national, and global levels.

Project Details:
- Description: {project_description}
- Location: {project_location}
- Sectors: {project_sectors}
- Funding Types: {funding_types}

Create a research plan that outlines:

1. **Regional Research Strategy** (for {project_location} and surrounding areas)
   - Key regional funding bodies to investigate
   - Local government schemes
   - Regional development agencies
   - Local sustainability initiatives

2. **National Research Strategy** (for the country where project is located)
   - National government departments and agencies
   - Innovation funding programs
   - Energy transition schemes
   - National development banks

3. **Global Research Strategy**
   - International climate finance institutions
   - Global sustainability funds
   - Multinational development banks
   - International private equity firms focused on Net Zero

4. **Search Optimization Tips**
   - Key terms and phrases to use
   - Databases and portals to check
   - Networking opportunities

Provide specific, actionable guidance for each level."""
