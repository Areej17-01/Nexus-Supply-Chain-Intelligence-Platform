# Supplier Agent Implementation Guide

## Overview

This is a complete **supplier-side agent system** built on Google ADK for the NEXUS Supply Chain Intelligence Platform. It enables suppliers to automatically respond to buyer RFQs (Requests for Quote) through intelligent agents that handle inventory checks, quote generation, and negotiation.

---

## System Architecture

### Core Components

```
supplier/
├── __init__.py
├── QuoteAgent/
│   ├── __init__.py
│   ├── agent.py                 # Google ADK agent definition
│   ├── supplier_tools.py        # Tool implementations
│   └── supplier_prompts.py      # Agent instructions & behavior
├── supplier_registry.py         # Supplier discovery & registration
└── supplier_catalog.py          # Sample data & seeding
```

### How It Works

1. **Buyer sends RFQ** → `/api/rfq` endpoint
2. **Registry discovers suppliers** → Filters by capability, region, certifications
3. **Supplier agent activated** → For each matching supplier
4. **Agent checks inventory** → Uses `check_inventory()` tool
5. **Agent validates requirements** → Uses `validate_buyer_requirements()` tool
6. **Agent generates quote** → Uses `calculate_quote()` tool
7. **Quote saved** → Uses `save_quote_to_db()` tool
8. **Results returned** → Ranked by price, trust score, and lead time

---

## Key Features

### 1. **Dynamic Agent Instantiation**
Each supplier has an agent created on-demand when handling RFQs:
```python
agent = get_supplier_agent("supplier-001")
quote = await agent.ainvoke(rfq_request)
```

### 2. **Intelligent Quote Generation**
- **Volume discounts**: Automatic tiered pricing (100+, 500+, 1000+ units)
- **Loyalty discounts**: 2% for repeat buyers (3+ orders)
- **Inventory awareness**: Real-time stock checking
- **Lead time calculation**: Based on stock availability
- **Requirement validation**: Checks certifications, regions, deadlines

### 3. **Supplier Registry**
Centralized discovery with multiple filters:
```python
suppliers = SupplierRegistry.discover_suppliers(
    capability="temperature_sensors",
    region="EU",
    certifications_required=["CE", "ISO9001"],
    min_trust_score=0.8
)
```

### 4. **Extensible Catalog**
Easy to add suppliers and products:
```python
SupplierRegistry.add_product_to_supplier(
    supplier_id="supplier-001",
    product_id="prod-001",
    product_name="Temperature Sensor",
    unit_price=2.50,
    stock_quantity=5000
)
```

---

## API Endpoints

### RFQ Handling

**POST `/api/rfq`** - Send a Request for Quote
```json
{
  "buyer_id": "buyer-001",
  "items": [
    {"product_id": "prod-001", "quantity": 500}
  ],
  "delivery_region": "EU",
  "deadline_days": 10,
  "required_certifications": ["CE", "ISO9001"],
  "negotiation_style": "balanced"
}
```

**Response**: Array of quotes from suppliers ranked by score

---

### Supplier Management

**GET `/api/suppliers`** - List all suppliers
```
?region=EU&capability=temperature_sensors&min_trust_score=0.8
```

**GET `/api/suppliers/{supplier_id}`** - Get supplier details
```json
{
  "supplier_id": "supplier-001",
  "company_name": "Berlin Electronics GmbH",
  "region": "EU",
  "certifications": ["CE", "ISO9001"],
  "trust_score": 0.92
}
```

**POST `/api/suppliers/register`** - Register new supplier
```json
{
  "supplier_id": "supplier-new",
  "company_name": "New Tech Corp",
  "country": "Germany",
  "region": "EU",
  "certifications": ["CE"],
  "contact_email": "sales@newtech.com"
}
```

**POST `/api/suppliers/{supplier_id}/quote`** - Get direct quote
Same RFQ format as `/api/rfq`

---

## Supplier Tools

### 1. `get_supplier_catalog(supplier_id)`
Retrieves the supplier's product catalog and company info
```python
catalog = get_supplier_catalog("supplier-001")
# Returns: products, prices, stock, certifications
```

### 2. `check_inventory(supplier_id, product_id, quantity)`
Checks if inventory is available and calculates lead time
```python
inventory = check_inventory("supplier-001", "prod-001", 500)
# Returns: availability status, stock level, lead time
```

### 3. `validate_buyer_requirements(supplier_id, certs, region, lead_time)`
Validates if supplier meets buyer's requirements
```python
valid = validate_buyer_requirements(
    "supplier-001",
    ["CE", "ISO9001"],
    "EU",
    10
)
# Returns: compliance status for each requirement
```

### 4. `calculate_quote(supplier_id, items, buyer_id)`
Generates a quote with volume and loyalty discounts
```python
quote = calculate_quote(
    "supplier-001",
    [{"product_id": "prod-001", "quantity": 500}],
    "buyer-001"
)
# Returns: line items, totals, payment terms, notes
```

### 5. `save_quote_to_db(supplier_id, quote_data)`
Persists the quote for tracking and negotiation
```python
result = save_quote_to_db("supplier-001", quote_data)
```

---

## Pricing Strategy

### Volume Discounts (Automatic)
| Quantity | Discount |
|----------|----------|
| < 100 | 0% |
| 100-499 | 5% |
| 500-999 | 10% |
| 1000+ | 15% |

### Loyalty Discounts
- **3+ previous orders** → 2% additional discount
- Otherwise → 0%

### Payment Term Incentives
- **Prepay or 7-day payment** → 3% discount
- **Standard (Net-30)** → No discount
- **Extended (Net-45)** → For quality-first negotiators

### Margin Protection
- **Minimum markup** → 12% above cost
- **Never go below** → Enforced in `calculate_quote()`

---

## Quote Response Structure

```json
{
  "quote_id": "quote-abc123",
  "supplier_id": "supplier-001",
  "supplier_name": "Berlin Electronics GmbH",
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
  "currency": "EUR",
  "created_at": "2024-04-27T10:00:00Z",
  "valid_until": "2024-05-04T10:00:00Z",
  "notes": "Quote valid for 7 days. Bulk discounts applied.",
  "status": "pending_acceptance"
}
```

---

## Running the System

### 1. **Start the Platform**
```bash
python main.py
```

The server will:
- Initialize the supplier registry
- Seed sample suppliers and products
- Start on `http://localhost:8010`

### 2. **Test an RFQ**

```bash
curl -X POST http://localhost:8010/api/rfq \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_id": "buyer-001",
    "items": [{"product_id": "prod-001", "quantity": 500}],
    "delivery_region": "EU",
    "deadline_days": 10,
    "required_certifications": ["CE", "ISO9001"]
  }'
```

### 3. **List Available Suppliers**
```bash
curl http://localhost:8010/api/suppliers?region=EU
```

### 4. **Get a Direct Quote**
```bash
curl -X POST http://localhost:8010/api/suppliers/supplier-001/quote \
  -H "Content-Type: application/json" \
  -d '{...}'  # Same RFQ format
```

---

## Sample Suppliers (Pre-seeded)

| Company | Region | Certifications | Trust Score | Specialty |
|---------|--------|-----------------|------------|-----------|
| Berlin Electronics | EU | CE, ISO9001 | 0.92 | Temperature/Pressure sensors |
| Shenzhen Parts | Asia | RoHS, ISO9001 | 0.78 | Microcontrollers, WiFi |
| Nordic Precision | EU | ISO13485, FDA | 0.88 | Medical-grade sensors |
| Chicago Industrial | US | UL, ITAR | 0.85 | ITAR-compliant products |
| Tokyo Micro | Asia | JIS, CE | 0.94 | High-precision sensors |

---

## Adding a New Supplier

### Method 1: API Registration
```bash
curl -X POST http://localhost:8010/api/suppliers/register \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": "supplier-006",
    "company_name": "New Tech Corp",
    "country": "Netherlands",
    "region": "EU",
    "certifications": ["CE", "ISO9001"],
    "contact_email": "sales@newtech.com",
    "trust_score": 0.75
  }'
```

### Method 2: Programmatic Registration
```python
from supplier.supplier_registry import SupplierRegistry

# Register supplier
SupplierRegistry.register_supplier(
    supplier_id="supplier-006",
    company_name="New Tech Corp",
    country="Netherlands",
    region="EU",
    certifications=["CE", "ISO9001"],
    capabilities=["sensors", "controllers"],
    contact_email="sales@newtech.com"
)

# Add products
SupplierRegistry.add_product_to_supplier(
    supplier_id="supplier-006",
    product_id="prod-020",
    product_name="New Sensor XYZ",
    category="new_category",
    unit_price=15.00,
    stock_quantity=2000,
    lead_time_days=7
)
```

---

## Agent Behavior & Prompts

The supplier agent follows a strict sequence when processing RFQs:

1. **Get Catalog** → Load supplier's inventory
2. **Check Inventory** → Verify stock for each item
3. **Validate Requirements** → Check certifications, region, deadline
4. **Calculate Quote** → Apply discounts and generate pricing
5. **Save Quote** → Persist to database
6. **Return Response** → JSON with quote or rejection reason

See `supplier_prompts.py` for the exact instructions given to the agent.

---

## Negotiation Styles

Suppliers can adopt different negotiation approaches:

| Style | Payment Terms | Flexibility | Best For |
|-------|---------------|------------|----------|
| **balanced** | Net-30 | Medium | Most transactions |
| **aggressive** | Net-15 | High | Volume buyers |
| **quality_first** | Net-45 | Low (margin-focused) | Premium/specialty products |

---

## Database Schema Integration

The system uses these tables:
- `suppliers` - Supplier info and metadata
- `supplier_products` - Product catalogs
- `quotes` - Generated quotes
- `orders` - Purchase orders (for negotiation context)

Make sure your `db.py` has these tables set up.

---

## Next Steps: Negotiation

Once quotes are generated, the system can:
1. **Counter-offer** - Buyer negotiates on price/terms
2. **Multi-turn dialogue** - Automated back-and-forth
3. **Concessions** - Non-price adjustments (payment terms, delivery time)
4. **Acceptance** - Final agreement and contract generation

See the negotiation agent docs for details.

---

## Troubleshooting

### Agents Not Responding to RFQs?
- Check that suppliers are registered: `GET /api/suppliers`
- Verify catalog has products: Database `supplier_products` table
- Check Gemini API key in `.env` file

### Quotes Not Generated?
- Verify `calculate_quote()` is being called
- Check minimum margin isn't violated (12% minimum)
- Ensure inventory is in stock

### Registry Empty?
- Run `python -c "from supplier.supplier_catalog import seed_suppliers; seed_suppliers()"`
- Or restart the app (seeding happens on startup)

---

## Architecture Comparison: NEXUS vs MURA

| Feature | NEXUS | MURA |
|---------|-------|------|
| **Agent Model** | Google ADK | LangGraph |
| **Supplier Architecture** | Dynamic agents | Static instances |
| **Discovery** | Registry-based | Hardcoded list |
| **Pricing** | Intelligent discounts | Manual |
| **Negotiation** | Real multi-turn | Simulated |
| **Extensibility** | Easy to add suppliers | Complex integration |

---

## Performance Considerations

- **Parallel RFQ**: Query multiple suppliers simultaneously
- **Caching**: Cache supplier catalogs for 1 hour
- **Async processing**: All agent calls are async
- **Database indexing**: Index on `supplier_id`, `category`, `region`

---

## Security Notes

- **API Key protection**: `.env` file with API keys (not in code)
- **Validation**: All RFQ inputs validated before agent invocation
- **Rate limiting**: Recommended: 100 RFQs/minute per buyer
- **Quote expiration**: All quotes expire after 7 days
- **Audit logging**: Store all quotes for compliance

---

## Demo Flow

1. **User types**: "I need 500 temperature sensors for EU, budget €2000, 10 days"
2. **System parses**: Intent Parser agent (buyer side)
3. **System discovers**: Finds 5 EU suppliers with temperature sensors
4. **System queries**: Routes RFQ to top 3 by trust score
5. **Suppliers respond**: Agents generate quotes in real-time
6. **System displays**: Ranked results with options
7. **User selects**: Best quote based on price/trust/delivery
8. **System negotiates**: Counter-offer loop if needed
9. **System contracts**: Auto-generates PO
10. **System tracks**: Monitors shipment

---

## Files Created

- ✅ `supplier/supplier_registry.py` - Registry system
- ✅ `supplier/supplier_catalog.py` - Sample data
- ✅ `supplier/QuoteAgent/agent.py` - Google ADK agent
- ✅ `supplier/QuoteAgent/supplier_tools.py` - Tools
- ✅ `supplier/QuoteAgent/supplier_prompts.py` - Instructions
- ✅ `main.py` - Enhanced with supplier endpoints

---

## Next Features (Post-MVP)

- [ ] Negotiation agent for counter-offers
- [ ] Contract generator for POs
- [ ] Order tracking with shipment updates
- [ ] Disruption monitoring (news, delays)
- [ ] Dynamic agent factory for specialized agents
- [ ] Multi-language support
- [ ] Supplier onboarding UI portal
