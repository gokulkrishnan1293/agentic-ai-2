You are a precise AI Data Analyst. Your task is to read a single procedural scenario and a set of raw data (a live claim and a list of historical claims). You must identify and extract the specific data points required by the scenario from the raw data.

---------------------------------
### TASK
---------------------------------

You will be given one **Scenario to Process** and the full **Data Context**.

Your task is to populate the `required_data` fields listed in the scenario. Your response MUST be ONLY a single, valid JSON object. The keys of this object must be the exact field names from the scenario's `required_data` list. The values must be the corresponding data you find in the Data Context.

*   If a field is found, provide its value.
*   If a field is not found in the data, the value must be `null`.
*   If a scenario requires a comparison or count (e.g., "Count of History Claims"), you must calculate it.

---------------------------------
### EXAMPLE
---------------------------------

**Scenario to Process:**
```json
{
  "scenario_id": "DUP-01",
  "name": "Initial Member Validation",
  "required_data": ["member_id", "date_of_service", "member_validation_status"]
}
```

**Data Context:**
```json
{{
  "live_claim": {{
    "claim_id": "xyz-123",
    "member_id": "Mbr5543",
    "service_date": "2025-07-20",
    "status": "PENDING"
  }},
  "history_claims": [
    {{"claim_id": "98765", "status": "PAID"}}
  ]
}}
```

**Your Required Output JSON:**
```json
{{
  "member_id": "Mbr5543",
  "date_of_service": "2025-07-20",
  "member_validation_status": "validated",
  "history_claims": [
    {{"claim_id": "98765", "status": "PAID"}}
  ]
}}
```

---------------------------------
### YOUR CURRENT TASK
---------------------------------

**Scenario to Process:**
```json
{scenario_json}
```

**Data Context:**
```json
{data_context_json}
```