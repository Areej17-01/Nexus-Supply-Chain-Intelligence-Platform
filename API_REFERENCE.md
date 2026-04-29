# NEXUS Supplier Agent System - API Reference

## Base URL
```
http://localhost:8010
```

---

## CORE ENDPOINTS

### 1️⃣ HEALTH CHECK
**Check if platform is running**

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "platform": "NEXUS Supply Chain",
  "version": "1.0.0"
}
```

---

### 2️⃣ LIST SUPPLIERS
**Get all registered suppliers (with filters)**

```http
GET /api/suppliers
  ?region=EU
  &capability=temperature_sensors
  &min_trust_score=0.8
  &limit=20
```

**Parameters:**
- `region` (optional): EU, Asia, US, etc.
- `capability` (optional): Product category
- `min_trust_score` (optional): 0-1 scale
- `limit` (optional): Max results (default: 20)

**Response:**
```json
{
  "suppliers_found": 3,
  "suppliers": [
    {
      "supplier_id": "supplier-001",
      "company_name": "Berlin Electronics GmbH",
      "country": "Germany",
      "region": "EU",
      "certifications": ["CE", "ISO9001"],
      "trust_score": 0.92,
      "contact_email": "sales@berlin-electronics.de"
    }
  ]
}
```

---

### 3️⃣ GET SUPPLIER DETAILS
**Get full info about specific supplier**

```http
GET /api/suppliers/{supplier_id}
```

**Example:**
```http
GET /api/suppliers/supplier-001
```

**Response:**
```json
{
  "supplier_id": "supplier-001",
  "company_name": "Berlin Electronics GmbH",
  "country": "Germany",
  "region": "EU",
  "certifications": ["CE", "ISO9001", "ISO14001", "RoHS"],
  "trust_score": 0.92,
  "contact_email": "sales@berlin-electronics.de",
  "api_endpoint": null,
  "negotiation_style": "balanced",
  "is_active": 1,
  "registered_at": "2024-04-27T10:00:00Z"
}
```

---

### 4️⃣ SEND REQUEST FOR QUOTE (RFQ)
**Query multiple suppliers for quotes**

```http
POST /api/rfq
Content-Type: application/json
```

**Request Body:**
```json
{
  "buyer_id": "buyer-001",
  "items": [
    {
      "product_id": "prod-001",
      "quantity": 500
    },
    {
      "product_id": "prod-002",
      "quantity": 100
    }
  ],
  "delivery_region": "EU",
  "deadline_days": 10,
  "max_budget": 2000,
  "required_certifications": ["CE", "ISO9001"],
  "negotiation_style": "balanced"
}
```

**Response:**
```json
{
  "rfq_id": "buyer-001",
  "status": "quotes_received",
  "requested_items": 2,
  "suppliers_contacted": 5,
  "quotes_received": 3,
  "quotes": [
    {
      "supplier_id": "supplier-001",
      "supplier_name": "Berlin Electronics GmbH",
      "supplier_trust_score": 0.92,
      "quote": {
        "quote_id": "quote-abc123",
        "line_items": [...],
        "subtotal": 1125.00,
        "payment_terms": "Net-30",
        "currency": "EUR",
        "valid_until": "2024-05-04T10:00:00Z"
      }
    }
  ],
  "next_action": "negotiation_agent"
}
```

---

### 5️⃣ GET DIRECT QUOTE
**Get quote directly from one supplier**

```http
POST /api/suppliers/{supplier_id}/quote
Content-Type: application/json
```

**Example:**
```http
POST /api/suppliers/supplier-001/quote
```

**Request Body:** (Same as RFQ)
```json
{
  "buyer_id": "buyer-001",
  "items": [{"product_id": "prod-001", "quantity": 500}],
  "delivery_region": "EU",
  "deadline_days": 10
}
```

**Response:**
```json
{
  "supplier_id": "supplier-001",
  "rfq_request": {...},
  "quote_response": {
    "quote_id": "quote-xyz789",
    "supplier_id": "supplier-001",
    "line_items": [
      {
        "product_name": "Temperature Sensor NTC 10K",
        "quantity": 500,
        "unit_price": 2.50,
        "discount_rate": 0.10,
        "discounted_unit_price": 2.25,
        "line_total": 1125.00,
        "lead_time_days": 5,
        "in_stock": true
      }
    ],
    "subtotal": 1125.00,
    "payment_terms": "Net-30",
    "currency": "EUR"
  }
}
```

---

### 6️⃣ REGISTER SUPPLIER
**Register new supplier in network**

```http
POST /api/suppliers/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "supplier_id": "supplier-new",
  "company_name": "New Tech Corporation",
  "country": "Netherlands",
  "region": "EU",
  "certifications": ["CE", "ISO9001", "RoHS"],
  "contact_email": "sales@newtechcorp.com",
  "trust_score": 0.75,
  "negotiation_style": "balanced"
}
```

**Response:**
```json
{
  "success": true,
  "supplier_id": "supplier-new",
  "company_name": "New Tech Corporation",
  "message": "Supplier registered successfully",
  "timestamp": "2024-04-27T11:30:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Supplier with ID supplier-new already exists"
}
```

---

### 7️⃣ PLATFORM INFO
**Get info about available endpoints**

```http
GET /api/info
```

**Response:**
```json
{
  "platform": "NEXUS Supply Chain Intelligence Platform",
  "description": "AI-powered procurement with buyer and supplier agents",
  "endpoints": {
    "buyer_agents": "/buyer",
    "rfq": "/api/rfq",
    "suppliers": "/api/suppliers",
    "supplier_registration": "/api/suppliers/register",
    "supplier_quote": "/api/suppliers/{supplier_id}/quote"
  }
}
```

---

## PARAMETER REFERENCE

### Delivery Regions
```
"EU"           - European Union
"Asia"         - Asia-Pacific
"US"           - United States
"North America" - USA + Canada + Mexico
"ANY"          - No region preference
```

### Common Certifications
```
"CE"           - European conformity
"ISO9001"      - Quality management
"ISO13485"     - Medical devices
"ISO14001"     - Environmental management
"FDA"          - Food & Drug Administration
"ITAR"         - International Traffic in Arms
"RoHS"         - Restriction of Hazardous Substances
"UL"           - Underwriters Laboratories
"JIS"          - Japanese Industrial Standard
"REACH"        - Registration, Evaluation, Authorisation
```

### Negotiation Styles
```
"balanced"     - Medium price, medium terms
"aggressive"   - Lower price, stricter terms (Net-15)
"quality_first"- Higher price, relaxed terms (Net-45)
```

### Product Categories
```
"temperature_sensors"
"pressure_sensors"
"humidity_sensors"
"flow_sensors"
"wireless_modules"
"microcontrollers"
```

---

## CURL EXAMPLES

### List EU suppliers
```bash
curl -X GET "http://localhost:8010/api/suppliers?region=EU"
```

### Send RFQ
```bash
curl -X POST "http://localhost:8010/api/rfq" \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_id": "buyer-001",
    "items": [{"product_id": "prod-001", "quantity": 500}],
    "delivery_region": "EU",
    "deadline_days": 10
  }'
```

### Get direct quote
```bash
curl -X POST "http://localhost:8010/api/suppliers/supplier-001/quote" \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_id": "buyer-001",
    "items": [{"product_id": "prod-001", "quantity": 500}],
    "delivery_region": "EU",
    "deadline_days": 10
  }'
```

### Register supplier
```bash
curl -X POST "http://localhost:8010/api/suppliers/register" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": "supplier-new",
    "company_name": "New Tech",
    "country": "Germany",
    "region": "EU",
    "certifications": ["CE"],
    "contact_email": "sales@newtech.com"
  }'
```

---

## PYTHON EXAMPLES

### Using requests library

```python
import requests
import json

BASE_URL = "http://localhost:8010"

# List suppliers
response = requests.get(f"{BASE_URL}/api/suppliers?region=EU")
suppliers = response.json()
print(f"Found {suppliers['suppliers_found']} suppliers")

# Send RFQ
rfq = {
    "buyer_id": "buyer-001",
    "items": [{"product_id": "prod-001", "quantity": 500}],
    "delivery_region": "EU",
    "deadline_days": 10
}
response = requests.post(f"{BASE_URL}/api/rfq", json=rfq)
quotes = response.json()
print(f"Received {len(quotes['quotes'])} quotes")

# Register supplier
new_supplier = {
    "supplier_id": "supplier-new",
    "company_name": "New Tech Corp",
    "country": "Netherlands",
    "region": "EU",
    "certifications": ["CE"],
    "contact_email": "sales@newtech.com"
}
response = requests.post(f"{BASE_URL}/api/suppliers/register", json=new_supplier)
result = response.json()
if result['success']:
    print(f"Supplier registered: {result['supplier_id']}")
```

---

## RESPONSE CODES

| Code | Meaning |
|------|---------|
| 200 | ✅ Success |
| 400 | ❌ Bad request (invalid parameters) |
| 404 | ❌ Not found (supplier/product doesn't exist) |
| 500 | ❌ Server error (check logs) |

---

## RATE LIMITS (Recommended)

- **RFQs**: 100 per minute per buyer
- **Supplier queries**: 1000 per minute
- **Registrations**: 10 per minute
- **Direct quotes**: 500 per minute per supplier

---

## DATA TYPES

### Quote Object
```json
{
  "quote_id": "string",
  "supplier_id": "string",
  "line_items": [
    {
      "product_id": "string",
      "product_name": "string",
      "quantity": "integer",
      "unit_price": "float",
      "discount_rate": "float (0-1)",
      "discounted_unit_price": "float",
      "line_total": "float",
      "lead_time_days": "integer",
      "in_stock": "boolean"
    }
  ],
  "subtotal": "float",
  "payment_terms": "string",
  "currency": "string",
  "created_at": "ISO 8601 timestamp",
  "valid_until": "ISO 8601 timestamp"
}
```

### Supplier Object
```json
{
  "supplier_id": "string",
  "company_name": "string",
  "country": "string",
  "region": "string",
  "certifications": ["string"],
  "trust_score": "float (0-1)",
  "contact_email": "string",
  "negotiation_style": "string"
}
```

---

## COMMON USE CASES

### Use Case 1: Get quotes from all EU suppliers
```bash
# Step 1: List EU suppliers
curl http://localhost:8010/api/suppliers?region=EU

# Step 2: Send RFQ
curl -X POST http://localhost:8010/api/rfq -d '...'
```

### Use Case 2: Get quote from best supplier
```bash
# Step 1: List suppliers sorted by trust score
curl http://localhost:8010/api/suppliers?region=EU&min_trust_score=0.9

# Step 2: Get direct quote from top supplier
curl -X POST http://localhost:8010/api/suppliers/supplier-001/quote -d '...'
```

### Use Case 3: Onboard new supplier
```bash
# Register supplier
curl -X POST http://localhost:8010/api/suppliers/register -d '...'

# Add products via direct API call to Python
# (See SUPPLIER_AGENT_GUIDE.md for details)
```

---

## TROUBLESHOOTING

**Q: No quotes returned?**
- Check that required certifications match supplier capabilities
- Verify delivery_region is supported by suppliers
- Check supplier inventory in database

**Q: "Supplier not found"?**
- List all suppliers: `GET /api/suppliers`
- Verify supplier_id spelling

**Q: Getting 500 error?**
- Check server is running: `python main.py`
- Verify `.env` has GEMINI_API_KEY and DATABASE_URL
- Check server logs in terminal

**Q: Quotes taking too long?**
- Normal: 500ms - 2s per supplier
- If longer: Check Gemini API rate limits
- Reduce number of suppliers in discovery filter

---

## VERSION
API Version: 1.0.0
Last Updated: April 27, 2024

For more details, see: `SUPPLIER_AGENT_GUIDE.md`
