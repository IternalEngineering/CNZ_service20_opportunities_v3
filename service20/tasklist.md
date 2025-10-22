# City Research Task List

Research task: Run opportunity and funder research for all test cities

## Task Progress

### North America

- [x] 1. Boston, US (Climate Resilience Manager) - COMPLETED
- [ ] 2. Austin, US (Renewable Energy Coordinator)
- [ ] 3. Seattle, US (Green Building Manager)
- [ ] 4. San Francisco, US (Zero Waste Coordinator)
- [ ] 5. New York City, US (Climate Advisor)
- [ ] 18. Vancouver, CA (Sustainability Coordinator)

### Europe

- [ ] 6. Birmingham, GB (Transport Decarbonization Lead)
- [ ] 7. Edinburgh, GB (Sustainability Director)
- [ ] 8. Manchester, GB (Green Economy Lead)
- [ ] 9. Bristol, GB (Climate Manager)
- [ ] 13. Stockholm, SE (Environmental Strategist)
- [ ] 17. Copenhagen, DK (Climate Advisor)

### Asia-Pacific

- [ ] 11. Melbourne, AU (Climate Officer)
- [ ] 12. Mumbai, IN (Air Quality Manager)
- [ ] 14. Auckland, NZ (Climate Lead)
- [ ] 15. Dubai, AE (Green Economy Director)
- [ ] 19. Tokyo, JP (Environmental Director)
- [ ] 21. Singapore, SG (Sustainability Manager)

### South America

- [ ] 10. Bogotá, CO (Transport Planner)
- [ ] 16. São Paulo, BR (Environmental Manager)

### Africa

- [ ] 20. Cape Town, ZA (Climate Officer)

## Research Commands

Each city requires two research runs:

1. **Opportunity Research**:
   ```bash
   python research_city_opportunity.py --city "CityName" --country COUNTRY_CODE --sector renewable_energy --range 1000000-10000000
   ```

2. **Funder Research**:
   ```bash
   python research_funder_opportunity.py impact_investor --scope national --countries "CountryName" --sectors renewable_energy,solar_energy --min 1000000 --max 10000000
   ```

## Notes

- Boston already completed in previous session
- All cities are from service6_onboarding_voice with email test@urbanzero.ai
- Research results stored in service20_investment_opportunities and service20_funding_opportunities tables
- All research traced to Arize AX dashboard for monitoring
