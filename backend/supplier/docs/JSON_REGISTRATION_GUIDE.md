# Supplier Registration with JSON

## 🎯 Quick Answer: Yes!

There are **3 ways** to register suppliers:

### ✅ Method 1: Auto-Load from `supplier/suppliers.json` (Easiest)

**When you start the server:**
```bash
python main.py
```

The system automatically loads suppliers from `supplier/suppliers.json` if:
1. The database is empty (first run)
2. The file exists in the project root

**No code needed!**

---

### ✅ Method 2: Manual Import Script

**Register suppliers from JSON anytime:**
```bash
python supplier/import_suppliers.py
```

**With options:**
```bash
python supplier/import_suppliers.py --file supplier/suppliers.json --quiet
```

---

### ✅ Method 3: API Registration

**Register a supplier via HTTP:**
```bash
curl -X POST http://localhost:8010/api/suppliers/register \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": "supplier-new",
    "company_name": "My Company",
    "country": "Germany",
    "region": "EU",
    "certifications": ["CE"],
    "contact_email": "sales@mycompany.com"
  }'
```

---

## 📁 Files for JSON Registration

### 1. `supplier/suppliers.json` - Main file with all suppliers
Contains 5 pre-configured suppliers with their products
- **Berlin Electronics** (EU)
- **Shenzhen Parts** (Asia)
- **Nordic Precision** (EU)
- **Chicago Industrial** (US)
- **Tokyo Micro** (Asia)

**Each supplier has:**
- ID, company name, country, region
- Certifications, contact email, trust score
- Products with prices, stock, and lead times

### 2. `suppliers_template.json` - Template for custom suppliers
Use this as a starting point to add your own suppliers

### 3. `import_suppliers.py` - Script to import from JSON
Bulk register all suppliers from JSON file

---

## 🚀 How to Add Your Own Suppliers

### Step 1: Edit `supplier/suppliers.json`
```json
{
  "suppliers": [
    {
      "supplier_id": "supplier-custom-001",
      "company_name": "Your Company",
      "country": "Country",
      "region": "EU",
      "certifications": ["CE", "ISO9001"],
      "contact_email": "sales@yourcompany.com",
      "trust_score": 0.80,
      "negotiation_style": "balanced",
      "products": [
        {
          "product_id": "prod-custom-001",
          "product_name": "Your Product",
          "category": "sensors",
          "unit_price": 15.00,
          "stock_quantity": 1000,
          "lead_time_days": 7,
          "certifications_required": ["CE"]
        }
      ]
    }
  ]
}
```

### Step 2: Import into database
```bash
python supplier/import_suppliers.py
```

**Output:**
```
============================================================
  SUPPLIER IMPORT FROM JSON
============================================================

Found 6 suppliers

✓ Your Company (EU)
  Products:
    + Your Product (€15.00)

============================================================
  IMPORT SUMMARY
============================================================
✓ Suppliers registered: 6/6
✓ Products added: 17
```

---

## 📊 JSON File Structure

### Supplier Fields

| Field | Type | Required | Example |
|-------|------|----------|---------|
| `supplier_id` | string | ✓ | `"supplier-001"` |
| `company_name` | string | ✓ | `"Berlin Electronics GmbH"` |
| `country` | string | ✓ | `"Germany"` |
| `region` | string | ✓ | `"EU"` or `"Asia"` or `"US"` |
| `certifications` | array | ✓ | `["CE", "ISO9001"]` |
| `contact_email` | string | ✓ | `"sales@company.com"` |
| `trust_score` | number | ✓ | `0.85` (0-1 scale) |
| `negotiation_style` | string | ✓ | `"balanced"` or `"aggressive"` or `"quality_first"` |
| `products` | array | ✓ | See below |

### Product Fields

| Field | Type | Required | Example |
|-------|------|----------|---------|
| `product_id` | string | ✓ | `"prod-001"` |
| `product_name` | string | ✓ | `"Temperature Sensor NTC 10K"` |
| `category` | string | ✓ | `"temperature_sensors"` |
| `unit_price` | number | ✓ | `2.50` |
| `stock_quantity` | number | ✓ | `5000` |
| `lead_time_days` | number | ✓ | `5` |
| `certifications_required` | array | ✓ | `["CE", "RoHS"]` |

---

## 🎯 Common Scenarios

### Scenario 1: Add a new supplier at startup
```json
{
  "suppliers": [
    {
      "supplier_id": "supplier-new",
      "company_name": "New Tech Ltd",
      "country": "Netherlands",
      "region": "EU",
      "certifications": ["CE"],
      "contact_email": "sales@newtech.com",
      "trust_score": 0.75,
      "negotiation_style": "balanced",
      "products": [
        {
          "product_id": "prod-new-001",
          "product_name": "New Sensor",
          "category": "sensors",
          "unit_price": 25.00,
          "stock_quantity": 500,
          "lead_time_days": 10,
          "certifications_required": ["CE"]
        }
      ]
    }
  ]
}
```

**Then start server:**
```bash
python main.py
```

### Scenario 2: Update existing supplier's products
1. Edit `supplier/suppliers.json`
2. Delete suppliers from database (or keep them)
3. Run: `python supplier/import_suppliers.py`

### Scenario 3: Bulk import from file
```bash
# Create your own supplier/suppliers.json
# Then import:
python supplier/import_suppliers.py --file supplier/suppliers.json
```

---

## 🔍 Valid Regions

```
EU
Asia
US
North America
Australia
Africa
South America
Middle East
```

---

## 🏷️ Common Certifications

```
CE           - European conformity
ISO9001      - Quality management
ISO13485     - Medical devices
ISO14001     - Environmental
FDA          - Food & Drug Administration
ITAR         - Arms/aerospace
RoHS         - Hazardous substances
UL           - Underwriters Labs
JIS          - Japanese standard
REACH        - EU chemicals
```

---

## 📂 Product Categories

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

## ✅ Verification

### Check imports worked:
```bash
curl http://localhost:8010/api/suppliers
```

Should return your suppliers.

### Check specific supplier:
```bash
curl http://localhost:8010/api/suppliers/supplier-custom-001
```

---

## 🐛 Troubleshooting

### ❌ JSON not imported on startup

**Solution:** Make sure:
1. `supplier/suppliers.json` is in project root
2. Database is empty (first run)
3. JSON file is valid (check syntax)

### ❌ "Invalid JSON" error

**Solution:** Validate JSON:
```bash
python -m json.tool supplier/suppliers.json
```

Should output formatted JSON without errors.

### ❌ Import script not found

**Solution:** Make sure you're in project root:
```bash
pwd
# Should be: C:\Users\Areej\Desktop\Projects\Nexus-Supply-Chain-Intelligence-Platform

python supplier/import_suppliers.py
```

---

## 📝 Tips

- **Start simple:** Use `suppliers_template.json` as a base
- **One product per line:** Makes debugging easier
- **Validate before importing:** Use online JSON validators
- **Keep backup:** Copy `supplier/suppliers.json` before making large changes
- **Auto-load:** Put custom suppliers in `supplier/suppliers.json` and restart server

---

## 🚀 Quick Workflow

1. **Copy template:**
   ```bash
   cp suppliers_template.json supplier/suppliers.json
   ```

2. **Edit supplier/suppliers.json** with your data

3. **Validate:**
   ```bash
   python -m json.tool supplier/suppliers.json > /dev/null && echo "Valid!"
   ```

4. **Import:**
   ```bash
   python supplier/import_suppliers.py
   ```

5. **Verify:**
   ```bash
   curl http://localhost:8010/api/suppliers
   ```

---

## 🎉 Done!

Your suppliers are now registered and ready to respond to RFQs!

**Next:** Send an RFQ:
```bash
curl -X POST http://localhost:8010/api/rfq -d '{...}'
```

---

## 📚 See Also

- `supplier/suppliers.json` - Pre-configured suppliers
- `suppliers_template.json` - Template for custom suppliers
- `import_suppliers.py` - Import script
- `API_REFERENCE.md` - API documentation
- `SUPPLIER_AGENT_README.md` - Complete guide
