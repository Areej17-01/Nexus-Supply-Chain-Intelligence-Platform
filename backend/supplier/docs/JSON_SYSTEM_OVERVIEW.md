# JSON Supplier Registration System - Complete Overview

## 🎯 Summary

Yes! There are **3 JSON files + 1 script** for managing suppliers:

| File | Purpose | When to Use |
|------|---------|-----------|
| `supplier/suppliers.json` | Main supplier database | Add your suppliers here |
| `suppliers_template.json` | Template for custom suppliers | Reference when adding new suppliers |
| `import_suppliers.py` | Script to import from JSON | Run to bulk-register suppliers |
| **Auto-load on startup** | Built into `main.py` | Just start the server |

---

## 📁 File Locations

```
Nexus-Supply-Chain-Intelligence-Platform/
├── supplier/suppliers.json              ← Main file (5 suppliers pre-configured)
├── suppliers_template.json     ← Template (use as reference)
├── import_suppliers.py         ← Import script
├── main.py                     ← Auto-loads supplier/suppliers.json on startup
├── JSON_REGISTRATION_GUIDE.md  ← How to register suppliers
├── JSON_EXAMPLES.md            ← Visual examples
└── API_REFERENCE.md            ← API endpoints
```

---

## 🔄 Complete Workflow

### Flow 1: Start Server (Auto-Load)
```
Start: python main.py
         ↓
Check: Is database empty?
         ↓
    YES → Load supplier/suppliers.json
         ↓
    Platform Ready ✓
```

### Flow 2: Manual Import
```
Edit: supplier/suppliers.json
         ↓
Run: python supplier/import_suppliers.py
         ↓
Database Updated ✓
```

### Flow 3: API Registration
```
Server: python main.py
         ↓
API: POST /api/suppliers/register
         ↓
Database Updated ✓
```

---

## 📊 File Comparison

### `supplier/suppliers.json` (Main Database)
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
          "product_name": "Temperature Sensor",
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

**Status:** ✅ Ready to use
**Contains:** 5 suppliers, 14 products
**Update:** Edit and run `python supplier/import_suppliers.py`

---

### `suppliers_template.json` (Template)
```json
{
  "suppliers": [
    {
      "supplier_id": "supplier-custom-001",
      "company_name": "Your Company Name Ltd",
      "country": "Country Name",
      "region": "EU",
      "certifications": ["CE", "ISO9001"],
      "contact_email": "sales@yourcompany.com",
      "trust_score": 0.75,
      "negotiation_style": "balanced",
      "products": [
        {
          "product_id": "prod-custom-001",
          "product_name": "Your Product Name",
          "category": "product_category",
          "unit_price": 10.00,
          "stock_quantity": 1000,
          "lead_time_days": 7,
          "certifications_required": ["CE"]
        }
      ]
    }
  ]
}
```

**Status:** 📋 Template only
**Contains:** 1 example supplier
**Use:** Copy to create custom suppliers

---

## 🚀 Quick Start (3 Options)

### Option A: Auto-Load (No Code)
```bash
# 1. Start server
python main.py

# That's it! supplier/suppliers.json auto-loaded
```

### Option B: Manual Import
```bash
# 1. Edit supplier/suppliers.json
# 2. Run import script
python supplier/import_suppliers.py

# 3. Optional: verify
curl http://localhost:8010/api/suppliers
```

### Option C: API Registration
```bash
# 1. Start server
python main.py

# 2. Register via API
curl -X POST http://localhost:8010/api/suppliers/register \
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

## 📋 Common Tasks

### Task 1: Add a New Supplier
```bash
# 1. Open supplier/suppliers.json
# 2. Add to "suppliers" array:
{
  "supplier_id": "supplier-new",
  "company_name": "New Company",
  "country": "Netherlands",
  "region": "EU",
  "certifications": ["CE"],
  "contact_email": "sales@newcompany.com",
  "trust_score": 0.80,
  "negotiation_style": "balanced",
  "products": [
    {
      "product_id": "prod-new-001",
      "product_name": "New Product",
      "category": "sensors",
      "unit_price": 25.00,
      "stock_quantity": 1000,
      "lead_time_days": 7,
      "certifications_required": ["CE"]
    }
  ]
}

# 3. Save and import
python supplier/import_suppliers.py
```

### Task 2: Update Supplier Prices
```bash
# 1. Edit supplier/suppliers.json
# Change: "unit_price": 2.50  →  "unit_price": 3.00

# 2. Reimport
python supplier/import_suppliers.py
```

### Task 3: Add More Products
```bash
# 1. Find supplier in supplier/suppliers.json
# 2. Add to "products" array:
{
  "product_id": "prod-002",
  "product_name": "Another Product",
  "category": "sensors",
  "unit_price": 15.00,
  "stock_quantity": 2000,
  "lead_time_days": 5,
  "certifications_required": ["CE"]
}

# 3. Reimport
python supplier/import_suppliers.py
```

### Task 4: Backup Suppliers
```bash
# Copy supplier/suppliers.json to backup
cp supplier/suppliers.json suppliers_backup.json
```

### Task 5: Load Different Supplier Set
```bash
# 1. Create new file: my_supplier/suppliers.json
# 2. Import from custom file
python supplier/import_suppliers.py --file my_supplier/suppliers.json
```

---

## ✅ Validation

### Check JSON Syntax
```bash
python -m json.tool supplier/suppliers.json
```

**Output if valid:**
```json
{
  "suppliers": [...]
}
```

**Output if invalid:**
```
json.decoder.JSONDecodeError: Expecting ':' at line X column Y
```

---

### Check Suppliers Imported
```bash
curl http://localhost:8010/api/suppliers
```

**Output:**
```json
{
  "suppliers_found": 5,
  "suppliers": [
    {
      "supplier_id": "supplier-001",
      "company_name": "Berlin Electronics GmbH",
      ...
    }
  ]
}
```

---

## 🔍 Data Structure

### Complete Hierarchy
```
supplier/suppliers.json
└── suppliers[]
    ├── supplier_id
    ├── company_name
    ├── country
    ├── region
    ├── certifications[]
    ├── contact_email
    ├── trust_score
    ├── negotiation_style
    └── products[]
        ├── product_id
        ├── product_name
        ├── category
        ├── unit_price
        ├── stock_quantity
        ├── lead_time_days
        └── certifications_required[]
```

---

## 📈 Pre-configured Suppliers

`supplier/suppliers.json` comes with 5 ready-to-use suppliers:

```
1. Berlin Electronics (EU)
   - Products: Temperature, Pressure, Humidity sensors
   - Trust: 0.92
   
2. Shenzhen Parts (Asia)
   - Products: Microcontrollers, WiFi modules
   - Trust: 0.78
   
3. Nordic Precision (EU)
   - Products: Medical-grade sensors
   - Trust: 0.88
   
4. Chicago Industrial (US)
   - Products: ITAR-compliant sensors
   - Trust: 0.85
   
5. Tokyo Micro (Asia)
   - Products: Precision sensors
   - Trust: 0.94
```

**All have real products with prices and inventory levels.**

---

## 🎯 Use Cases

### Use Case 1: Demo
```bash
# Use pre-configured supplier/suppliers.json
python main.py
# Then run RFQ tests
```

### Use Case 2: Custom Suppliers
```bash
# Edit supplier/suppliers.json with your suppliers
# Run: python supplier/import_suppliers.py
```

### Use Case 3: Bulk Import
```bash
# Have multiple supplier JSON files
# Import each: python supplier/import_suppliers.py --file file.json
```

### Use Case 4: Production
```bash
# Combine JSON with API registration
# Use supplier/suppliers.json for core suppliers
# Use API for dynamic registration
```

---

## 🔧 Advanced

### Import with Quiet Output
```bash
python supplier/import_suppliers.py --quiet
```

### Import and Exit with Code
```bash
python supplier/import_suppliers.py --file supplier/suppliers.json
echo $?  # Returns 0 if success, 1 if failed
```

### Debug Import Issues
```bash
# Verbose output (default)
python supplier/import_suppliers.py

# Check which suppliers failed
# Check server logs in main.py
```

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `JSON_REGISTRATION_GUIDE.md` | Step-by-step guide |
| `JSON_EXAMPLES.md` | Visual examples |
| `API_REFERENCE.md` | API endpoints |
| `SUPPLIER_AGENT_README.md` | Full system guide |
| `SUPPLIER_AGENT_GUIDE.md` | Technical details |

---

## 🚀 Next Steps

### 1. Explore Pre-configured Data
```bash
# Start server and list suppliers
python main.py
# In another terminal:
curl http://localhost:8010/api/suppliers
```

### 2. Send Test RFQ
```bash
curl -X POST http://localhost:8010/api/rfq \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_id": "buyer-001",
    "items": [{"product_id": "prod-001", "quantity": 500}],
    "delivery_region": "EU",
    "deadline_days": 10
  }'
```

### 3. Add Your Suppliers
```bash
# Edit supplier/suppliers.json
# Add your company data
# Run: python supplier/import_suppliers.py
```

---

## ✨ Summary

You have **4 ways** to manage suppliers:

1. ✅ **Auto-load**: Just start server (`python main.py`)
2. ✅ **Import script**: Run `python supplier/import_suppliers.py`
3. ✅ **API registration**: POST to `/api/suppliers/register`
4. ✅ **JSON files**: Edit `supplier/suppliers.json` directly

**All work together seamlessly!**

---

## 📞 Troubleshooting

| Problem | Solution |
|---------|----------|
| Suppliers not loading | Check `supplier/suppliers.json` exists in project root |
| JSON syntax error | Run `python -m json.tool supplier/suppliers.json` |
| Import script not found | Make sure you're in project root directory |
| Database seems empty | Run `python supplier/import_suppliers.py` manually |
| Can't update prices | Edit `supplier/suppliers.json`, then run import script |

---

## 🎉 You're All Set!

Choose your preferred method and start using the supplier system:

```bash
# Option 1: Just start (auto-loads supplier/suppliers.json)
python main.py

# Option 2: Manual import
python supplier/import_suppliers.py

# Option 3: Use API
curl -X POST http://localhost:8010/api/suppliers/register ...
```

**Happy supplying! 🚀**
