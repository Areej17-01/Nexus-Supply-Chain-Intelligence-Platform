# JSON Supplier Registration - Visual Reference

## 3 Files to Know About

```
📁 Project Root
├── supplier/suppliers.json              ← Main file (AUTO-LOADED on startup)
├── suppliers_template.json     ← Template for custom suppliers
└── import_suppliers.py         ← Script to import anytime
```

---

## 🔄 Workflow Options

### Option A: Auto-Load (Easiest)
```
1. Add suppliers to supplier/suppliers.json
2. Start server: python main.py
3. Done! Suppliers loaded automatically
```

### Option B: Manual Import
```
1. Add suppliers to supplier/suppliers.json
2. Run: python supplier/import_suppliers.py
3. Done! Suppliers loaded from script
```

### Option C: API Registration
```
1. Server running: python main.py
2. Send POST to /api/suppliers/register
3. Done! Supplier registered via API
```

---

## 📋 JSON Structure Explained

### Complete Supplier Example
```json
{
  "suppliers": [
    {
      "supplier_id": "supplier-001",
      "company_name": "Berlin Electronics GmbH",
      "country": "Germany",
      "region": "EU",
      "certifications": ["CE", "ISO9001"],
      "contact_email": "sales@berlin-electronics.de",
      "trust_score": 0.92,
      "negotiation_style": "balanced",
      "products": [
        {
          "product_id": "prod-001",
          "product_name": "Temperature Sensor NTC 10K",
          "category": "temperature_sensors",
          "unit_price": 2.50,
          "stock_quantity": 5000,
          "lead_time_days": 5,
          "certifications_required": ["CE", "RoHS"]
        }
      ]
    }
  ]
}
```

### What Each Field Means

```
supplier_id              ← Unique identifier (use in queries)
                          Example: "supplier-001"

company_name             ← Official company name
                          Example: "Berlin Electronics GmbH"

country                  ← Country of operation
                          Example: "Germany"

region                   ← Geographic region (used for filtering)
                          Options: EU, Asia, US, etc.

certifications          ← What they're certified for
                          Example: ["CE", "ISO9001"]

contact_email           ← How to reach the supplier
                          Example: "sales@company.com"

trust_score             ← Reputation score (0-1)
                          0 = new, 1.0 = highly trusted

negotiation_style       ← How they negotiate prices
                          Options: "balanced", "aggressive", 
                          "quality_first"

products               ← Array of products they supply
                          (see product fields below)

┌─────────────────────────────────────────────────┐
│ PRODUCT FIELDS                                  │
├─────────────────────────────────────────────────┤
product_id              ← Unique product identifier
                          Example: "prod-001"

product_name            ← What is the product
                          Example: "Temperature Sensor"

category                ← Product category (for discovery)
                          Example: "temperature_sensors"

unit_price              ← Price per unit (EUR)
                          Example: 2.50

stock_quantity          ← How many in stock
                          Example: 5000

lead_time_days          ← Days to deliver
                          Example: 5

certifications_required ← Certs needed for this product
                          Example: ["CE", "RoHS"]
```

---

## 📝 Before/After Examples

### Example 1: Simple Supplier
```json
{
  "suppliers": [
    {
      "supplier_id": "supplier-simple",
      "company_name": "Simple Supply Corp",
      "country": "Portugal",
      "region": "EU",
      "certifications": ["CE"],
      "contact_email": "hello@simple.pt",
      "trust_score": 0.70,
      "negotiation_style": "balanced",
      "products": [
        {
          "product_id": "prod-sensor-1",
          "product_name": "Basic Temperature Sensor",
          "category": "temperature_sensors",
          "unit_price": 5.00,
          "stock_quantity": 2000,
          "lead_time_days": 7,
          "certifications_required": ["CE"]
        }
      ]
    }
  ]
}
```

### Example 2: Premium Supplier
```json
{
  "suppliers": [
    {
      "supplier_id": "supplier-premium",
      "company_name": "Premium Tech Solutions",
      "country": "Switzerland",
      "region": "EU",
      "certifications": ["CE", "ISO9001", "ISO13485", "FDA"],
      "contact_email": "premium@tech.ch",
      "trust_score": 0.95,
      "negotiation_style": "quality_first",
      "products": [
        {
          "product_id": "prod-medical-001",
          "product_name": "Medical-Grade Pressure Sensor",
          "category": "pressure_sensors",
          "unit_price": 85.00,
          "stock_quantity": 500,
          "lead_time_days": 3,
          "certifications_required": ["CE", "ISO13485", "FDA"]
        }
      ]
    }
  ]
}
```

### Example 3: Aerospace Supplier
```json
{
  "suppliers": [
    {
      "supplier_id": "supplier-aerospace",
      "company_name": "AeroTech Industries",
      "country": "USA",
      "region": "US",
      "certifications": ["ITAR", "UL", "ISO9001"],
      "contact_email": "sales@aerotech.com",
      "trust_score": 0.92,
      "negotiation_style": "balanced",
      "products": [
        {
          "product_id": "prod-itar-001",
          "product_name": "ITAR-Compliant Gyroscope",
          "category": "sensors",
          "unit_price": 250.00,
          "stock_quantity": 100,
          "lead_time_days": 14,
          "certifications_required": ["ITAR", "UL"]
        }
      ]
    }
  ]
}
```

---

## 🎯 Step-by-Step: Add Your Supplier

### Step 1: Open `supplier/suppliers.json`
```
Find the "suppliers": [ array
```

### Step 2: Copy this template
```json
{
  "supplier_id": "supplier-YourID",
  "company_name": "Your Company Name",
  "country": "Your Country",
  "region": "Your Region",
  "certifications": ["YOUR", "CERTS"],
  "contact_email": "your@email.com",
  "trust_score": 0.80,
  "negotiation_style": "balanced",
  "products": [
    {
      "product_id": "prod-001",
      "product_name": "Your Product",
      "category": "your_category",
      "unit_price": 0.00,
      "stock_quantity": 0,
      "lead_time_days": 0,
      "certifications_required": ["CERTS"]
    }
  ]
}
```

### Step 3: Fill in your data
```json
{
  "supplier_id": "supplier-mycompany",           ← Your ID
  "company_name": "My Company Inc",              ← Your name
  "country": "Netherlands",                      ← Your country
  "region": "EU",                                ← Your region
  "certifications": ["CE", "ISO9001"],           ← Your certs
  "contact_email": "sales@mycompany.nl",         ← Your email
  "trust_score": 0.85,                           ← Your trust (0-1)
  "negotiation_style": "balanced",               ← Your style
  "products": [
    {
      "product_id": "prod-mycompany-001",
      "product_name": "My Awesome Sensor",
      "category": "temperature_sensors",
      "unit_price": 15.50,
      "stock_quantity": 10000,
      "lead_time_days": 5,
      "certifications_required": ["CE"]
    }
  ]
}
```

### Step 4: Add to the array
```json
{
  "suppliers": [
    { ... existing supplier 1 ... },
    { ... existing supplier 2 ... },
    { ... YOUR NEW SUPPLIER ... }    ← Add here
  ]
}
```

### Step 5: Save and import
```bash
python supplier/import_suppliers.py
```

**Output:**
```
✓ My Company Inc (EU)
  Products:
    + My Awesome Sensor (€15.50)
```

---

## 🔍 Quick Reference

### Region Options
```
EU              European Union
Asia            Asia-Pacific region
US              United States
North America   USA + Canada + Mexico
Australia       Australia
Africa          African continent
South America   South America
Middle East     Middle East region
```

### Negotiation Styles
```
balanced        Standard pricing & terms
aggressive      Lower prices, stricter terms (Net-15)
quality_first   Higher prices, flexible terms (Net-45)
```

### Common Categories
```
temperature_sensors
pressure_sensors
humidity_sensors
flow_sensors
wireless_modules
microcontrollers
sensors
electronics
industrial_parts
```

---

## ✅ Validation Checklist

Before importing, check:

- [ ] JSON is valid (no syntax errors)
- [ ] All suppliers have unique `supplier_id`
- [ ] All products have unique `product_id` (within supplier)
- [ ] `region` is a valid region
- [ ] `unit_price` is a number (e.g., 2.50, not "€2.50")
- [ ] `stock_quantity` is a number (e.g., 5000)
- [ ] `lead_time_days` is a number (e.g., 5)
- [ ] All certifications are real (CE, ISO9001, etc.)
- [ ] Email addresses are valid format

**Validate with:**
```bash
python -m json.tool supplier/suppliers.json > /dev/null && echo "✓ Valid JSON!"
```

---

## 🚀 Import Methods

### Method 1: Auto-load on startup
```bash
python main.py
# Automatically loads supplier/suppliers.json if database is empty
```

### Method 2: Import script
```bash
python supplier/import_suppliers.py
# Imports from supplier/suppliers.json

# Or import from custom file:
python supplier/import_suppliers.py --file custom_supplier/suppliers.json
```

### Method 3: Via API
```bash
curl -X POST http://localhost:8010/api/suppliers/register \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": "...",
    "company_name": "...",
    ...
  }'
```

---

## 🎓 Examples by Industry

### Scenario: Electronics Components
```json
{
  "supplier_id": "supplier-electronics",
  "company_name": "Electronics World Ltd",
  "country": "Taiwan",
  "region": "Asia",
  "certifications": ["RoHS", "ISO9001"],
  "contact_email": "sales@elecworld.tw",
  "trust_score": 0.82,
  "negotiation_style": "aggressive",
  "products": [
    {
      "product_id": "prod-mcu-001",
      "product_name": "Microcontroller ARM Cortex-M4",
      "category": "microcontrollers",
      "unit_price": 12.00,
      "stock_quantity": 50000,
      "lead_time_days": 10,
      "certifications_required": ["RoHS"]
    }
  ]
}
```

### Scenario: Medical Devices
```json
{
  "supplier_id": "supplier-medical",
  "company_name": "MedTech Solutions",
  "country": "Sweden",
  "region": "EU",
  "certifications": ["CE", "ISO13485", "FDA"],
  "contact_email": "procurement@medtech.se",
  "trust_score": 0.95,
  "negotiation_style": "quality_first",
  "products": [
    {
      "product_id": "prod-med-sensor-001",
      "product_name": "Cardiac Monitor ECG Sensor",
      "category": "medical_sensors",
      "unit_price": 180.00,
      "stock_quantity": 200,
      "lead_time_days": 7,
      "certifications_required": ["CE", "ISO13485", "FDA"]
    }
  ]
}
```

### Scenario: Aerospace Components
```json
{
  "supplier_id": "supplier-aerospace",
  "company_name": "SkyParts Corp",
  "country": "USA",
  "region": "US",
  "certifications": ["ITAR", "AS9100", "ISO9001"],
  "contact_email": "sales@skyparts.com",
  "trust_score": 0.90,
  "negotiation_style": "balanced",
  "products": [
    {
      "product_id": "prod-aero-001",
      "product_name": "Altitude Sensor (ITAR-restricted)",
      "category": "sensors",
      "unit_price": 950.00,
      "stock_quantity": 50,
      "lead_time_days": 21,
      "certifications_required": ["ITAR", "AS9100"]
    }
  ]
}
```

---

## 🎉 You're Ready!

Now you have:
- ✅ `supplier/suppliers.json` - Pre-configured suppliers
- ✅ `suppliers_template.json` - Template for your suppliers
- ✅ `import_suppliers.py` - Script to import
- ✅ Auto-loading on startup
- ✅ API registration endpoint

**Start using it:**
```bash
python main.py
```

Then test:
```bash
curl http://localhost:8010/api/suppliers
```

---

## 📚 See Also
- `JSON_REGISTRATION_GUIDE.md` - Detailed guide
- `supplier/suppliers.json` - Working example
- `suppliers_template.json` - Your template
- `API_REFERENCE.md` - API endpoints
