# 🎯 JSON Supplier Registration - Quick Reference Card

## ✅ Yes, There IS a JSON System!

You now have **4 JSON-related files** for managing suppliers:

---

## 📁 The Files

### 1️⃣ `supplier/suppliers.json` (Main Database)
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

✅ **Already has 5 suppliers with 14 products**

---

### 2️⃣ `suppliers_template.json` (Template)
```json
{
  "suppliers": [
    {
      "supplier_id": "supplier-custom-001",
      "company_name": "Your Company",
      "country": "Country",
      "region": "EU",
      "certifications": ["CE"],
      "contact_email": "sales@yourcompany.com",
      "trust_score": 0.75,
      "negotiation_style": "balanced",
      "products": [
        {
          "product_id": "prod-custom-001",
          "product_name": "Your Product",
          "category": "sensors",
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

📋 **Use as reference to add your own suppliers**

---

### 3️⃣ `import_suppliers.py` (Import Script)
```bash
# Import from supplier/suppliers.json
python supplier/import_suppliers.py

# Import from custom file
python supplier/import_suppliers.py --file my_supplier/suppliers.json

# Quiet mode (no output)
python supplier/import_suppliers.py --quiet
```

🚀 **Bulk register all suppliers at once**

---

### 4️⃣ `main.py` (Auto-Load Built-In)
```python
# On startup:
# - Checks if supplier/suppliers.json exists
# - Checks if database is empty
# - Auto-loads suppliers if both true

python main.py  # ✅ Auto-loads supplier/suppliers.json
```

✨ **Zero code - just start the server**

---

## 🔄 3 Ways to Register Suppliers

### Way 1: Auto-Load on Startup (Easiest) ⭐
```bash
# 1. supplier/suppliers.json already exists
# 2. Start server
python main.py

# Done! All suppliers loaded automatically
```

### Way 2: Manual Import
```bash
# 1. Edit supplier/suppliers.json
# 2. Run import script
python supplier/import_suppliers.py

# Done! All suppliers registered
```

### Way 3: API Registration
```bash
# 1. Start server
python main.py

# 2. Send POST request
curl -X POST http://localhost:8010/api/suppliers/register \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_id": "supplier-new",
    "company_name": "New Tech",
    "country": "Netherlands",
    "region": "EU",
    "certifications": ["CE"],
    "contact_email": "sales@newtech.com",
    "trust_score": 0.80
  }'
```

---

## 📊 Pre-Configured Suppliers in `supplier/suppliers.json`

| ID | Company | Region | Trust | Products |
|----|---------|--------|-------|----------|
| 001 | Berlin Electronics | EU | 0.92 | Temp/Pressure sensors |
| 002 | Shenzhen Parts | Asia | 0.78 | MCUs, WiFi |
| 003 | Nordic Precision | EU | 0.88 | Medical sensors |
| 004 | Chicago Industrial | US | 0.85 | ITAR products |
| 005 | Tokyo Micro | Asia | 0.94 | Precision sensors |

**Total: 5 suppliers, 14 products, all ready to use**

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| `JSON_REGISTRATION_GUIDE.md` | 📖 Complete step-by-step guide |
| `JSON_EXAMPLES.md` | 📋 Visual examples & scenarios |
| `JSON_SYSTEM_OVERVIEW.md` | 🎯 Complete system overview |
| `API_REFERENCE.md` | 🔗 API endpoints |

---

## ⚡ Quick Commands

### Start with auto-load
```bash
python main.py
```

### Manual import
```bash
python supplier/import_suppliers.py
```

### Check suppliers loaded
```bash
curl http://localhost:8010/api/suppliers
```

### Validate JSON syntax
```bash
python -m json.tool supplier/suppliers.json
```

### Register single supplier (API)
```bash
curl -X POST http://localhost:8010/api/suppliers/register \
  -H "Content-Type: application/json" \
  -d '{"supplier_id": "...", ...}'
```

---

## 📝 JSON Field Reference

### Supplier Fields
- `supplier_id` ← Unique ID (e.g., "supplier-001")
- `company_name` ← Company name
- `country` ← Country of operation
- `region` ← Region (EU, Asia, US, etc.)
- `certifications` ← Array of certs (CE, ISO9001, etc.)
- `contact_email` ← Contact email
- `trust_score` ← Trust score (0-1)
- `negotiation_style` ← "balanced", "aggressive", or "quality_first"
- `products` ← Array of products

### Product Fields
- `product_id` ← Unique product ID
- `product_name` ← Product name
- `category` ← Category (temperature_sensors, etc.)
- `unit_price` ← Price in EUR
- `stock_quantity` ← Stock level
- `lead_time_days` ← Delivery days
- `certifications_required` ← Required certs

---

## ✅ Validation

### Is JSON valid?
```bash
python -m json.tool supplier/suppliers.json > /dev/null && echo "✓ Valid!"
```

### Are suppliers loaded?
```bash
curl http://localhost:8010/api/suppliers
```

### Check specific supplier
```bash
curl http://localhost:8010/api/suppliers/supplier-001
```

---

## 🚀 5-Minute Setup

### Step 1: Already done! 
✅ `supplier/suppliers.json` exists with 5 suppliers

### Step 2: Start server
```bash
python main.py
```

### Step 3: Test
```bash
curl http://localhost:8010/api/suppliers
```

**Done! Suppliers are ready.** ✨

---

## 🎯 Common Tasks

### Add new supplier
```
1. Open supplier/suppliers.json
2. Copy supplier object
3. Change supplier_id, company_name, etc.
4. Run: python supplier/import_suppliers.py
```

### Update prices
```
1. Edit unit_price in supplier/suppliers.json
2. Run: python supplier/import_suppliers.py
```

### Add more products
```
1. Find supplier in supplier/suppliers.json
2. Add to products array
3. Run: python supplier/import_suppliers.py
```

### Use custom file
```bash
python supplier/import_suppliers.py --file my_supplier/suppliers.json
```

---

## 📚 Learn More

Read these in order:
1. **`JSON_REGISTRATION_GUIDE.md`** - How to register
2. **`JSON_EXAMPLES.md`** - Visual examples
3. **`JSON_SYSTEM_OVERVIEW.md`** - Complete overview
4. **`API_REFERENCE.md`** - API endpoints

---

## 🎉 Summary

✅ You have:
- `supplier/suppliers.json` - Main database (5 suppliers pre-configured)
- `suppliers_template.json` - Template for custom suppliers  
- `import_suppliers.py` - Script to import
- Auto-load on startup - Built into `main.py`
- Full documentation - 4 guide files

**Everything is ready to use!** 🚀

---

## 🔗 File Locations

```
Project Root/
├── supplier/suppliers.json              ← Main (5 suppliers)
├── suppliers_template.json     ← Template
├── import_suppliers.py         ← Import script
├── main.py                     ← Auto-loads
├── JSON_REGISTRATION_GUIDE.md
├── JSON_EXAMPLES.md
├── JSON_SYSTEM_OVERVIEW.md
└── API_REFERENCE.md
```

---

**Start now:**
```bash
python main.py
```

**Done!** ✨
