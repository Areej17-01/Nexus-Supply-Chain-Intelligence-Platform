"""
Supplier Catalog Seed Data
Pre-configured suppliers and their product catalogs for testing and demos
"""

from supplier.supplier_registry import SupplierRegistry


# Define suppliers
SUPPLIERS = [
    {
        "supplier_id": "supplier-001",
        "company_name": "Berlin Electronics GmbH",
        "country": "Germany",
        "region": "EU",
        "certifications": ["CE", "ISO9001", "ISO14001", "RoHS"],
        "contact_email": "sales@berlin-electronics.de",
        "trust_score": 0.92,
        "negotiation_style": "balanced"
    },
    {
        "supplier_id": "supplier-002",
        "company_name": "Shenzhen Parts Co.",
        "country": "China",
        "region": "Asia",
        "certifications": ["RoHS", "ISO9001", "CE"],
        "contact_email": "sales@shenzhenparts.cn",
        "trust_score": 0.78,
        "negotiation_style": "aggressive"
    },
    {
        "supplier_id": "supplier-003",
        "company_name": "Nordic Precision AB",
        "country": "Sweden",
        "region": "EU",
        "certifications": ["CE", "ISO9001", "ISO13485", "FDA"],
        "contact_email": "procurement@nordic-precision.se",
        "trust_score": 0.88,
        "negotiation_style": "quality_first"
    },
    {
        "supplier_id": "supplier-004",
        "company_name": "Chicago Industrial Supply",
        "country": "USA",
        "region": "US",
        "certifications": ["UL", "REACH", "ISO9001", "ITAR"],
        "contact_email": "sales@chicagoindustrial.com",
        "trust_score": 0.85,
        "negotiation_style": "balanced"
    },
    {
        "supplier_id": "supplier-005",
        "company_name": "Tokyo Micro Components",
        "country": "Japan",
        "region": "Asia",
        "certifications": ["CE", "ISO9001", "JIS", "RoHS"],
        "contact_email": "sales@tokyo-micro.jp",
        "trust_score": 0.94,
        "negotiation_style": "quality_first"
    },
]


# Define product catalogs for each supplier
SUPPLIER_CATALOGS = {
    "supplier-001": [  # Berlin Electronics
        {
            "product_id": "prod-001",
            "product_name": "Temperature Sensor NTC 10K",
            "category": "temperature_sensors",
            "unit_price": 2.50,
            "stock_quantity": 5000,
            "lead_time_days": 5,
            "certifications_required": ["CE", "RoHS"]
        },
        {
            "product_id": "prod-002",
            "product_name": "Pressure Transducer 0-10 Bar",
            "category": "pressure_sensors",
            "unit_price": 15.00,
            "stock_quantity": 1200,
            "lead_time_days": 7,
            "certifications_required": ["CE", "ISO9001"]
        },
        {
            "product_id": "prod-003",
            "product_name": "Humidity Sensor DHT22",
            "category": "humidity_sensors",
            "unit_price": 5.75,
            "stock_quantity": 3000,
            "lead_time_days": 5,
            "certifications_required": ["CE", "RoHS"]
        },
    ],
    
    "supplier-002": [  # Shenzhen Parts
        {
            "product_id": "prod-004",
            "product_name": "Temperature Sensor DS18B20",
            "category": "temperature_sensors",
            "unit_price": 1.80,
            "stock_quantity": 10000,
            "lead_time_days": 14,
            "certifications_required": ["RoHS"]
        },
        {
            "product_id": "prod-005",
            "product_name": "Microcontroller STM32F4",
            "category": "microcontrollers",
            "unit_price": 8.50,
            "stock_quantity": 8000,
            "lead_time_days": 10,
            "certifications_required": ["RoHS"]
        },
        {
            "product_id": "prod-006",
            "product_name": "WiFi Module ESP32",
            "category": "wireless_modules",
            "unit_price": 12.00,
            "stock_quantity": 4500,
            "lead_time_days": 12,
            "certifications_required": ["CE", "RoHS"]
        },
    ],
    
    "supplier-003": [  # Nordic Precision
        {
            "product_id": "prod-007",
            "product_name": "Precision Pressure Sensor (Medical Grade)",
            "category": "pressure_sensors",
            "unit_price": 45.00,
            "stock_quantity": 500,
            "lead_time_days": 10,
            "certifications_required": ["ISO13485", "FDA", "CE"]
        },
        {
            "product_id": "prod-008",
            "product_name": "Temperature Probe RTD Pt100",
            "category": "temperature_sensors",
            "unit_price": 28.00,
            "stock_quantity": 800,
            "lead_time_days": 7,
            "certifications_required": ["ISO13485", "CE"]
        },
    ],
    
    "supplier-004": [  # Chicago Industrial
        {
            "product_id": "prod-009",
            "product_name": "Temperature Sensor (ITAR-compliant)",
            "category": "temperature_sensors",
            "unit_price": 22.00,
            "stock_quantity": 600,
            "lead_time_days": 8,
            "certifications_required": ["ITAR", "UL"]
        },
        {
            "product_id": "prod-010",
            "product_name": "Industrial Pressure Gauge",
            "category": "pressure_sensors",
            "unit_price": 35.00,
            "stock_quantity": 400,
            "lead_time_days": 6,
            "certifications_required": ["UL", "REACH"]
        },
        {
            "product_id": "prod-011",
            "product_name": "Flow Meter Industrial Grade",
            "category": "flow_sensors",
            "unit_price": 120.00,
            "stock_quantity": 200,
            "lead_time_days": 14,
            "certifications_required": ["UL", "REACH"]
        },
    ],
    
    "supplier-005": [  # Tokyo Micro
        {
            "product_id": "prod-012",
            "product_name": "Precision Temperature Sensor (0.1°C accuracy)",
            "category": "temperature_sensors",
            "unit_price": 18.50,
            "stock_quantity": 2000,
            "lead_time_days": 7,
            "certifications_required": ["JIS", "CE", "RoHS"]
        },
        {
            "product_id": "prod-013",
            "product_name": "High-Precision Pressure Transducer",
            "category": "pressure_sensors",
            "unit_price": 52.00,
            "stock_quantity": 400,
            "lead_time_days": 10,
            "certifications_required": ["JIS", "ISO9001", "CE"]
        },
        {
            "product_id": "prod-014",
            "product_name": "Humidity + Temperature Combo Sensor",
            "category": "humidity_sensors",
            "unit_price": 8.20,
            "stock_quantity": 3500,
            "lead_time_days": 6,
            "certifications_required": ["CE", "RoHS", "JIS"]
        },
    ],
}


def seed_suppliers():
    """
    Populate the supplier registry and catalogs.
    Call this once at startup to initialize the system.
    
    Returns:
        Summary of seeded suppliers
    """
    
    registered_count = 0
    product_count = 0
    
    print("\n=== Seeding Supplier Registry ===\n")
    
    # Register all suppliers
    for supplier in SUPPLIERS:
        result = SupplierRegistry.register_supplier(
            supplier_id=supplier["supplier_id"],
            company_name=supplier["company_name"],
            country=supplier["country"],
            region=supplier["region"],
            certifications=supplier["certifications"],
            capabilities=[],  # Will be inferred from products
            contact_email=supplier["contact_email"],
            trust_score=supplier["trust_score"],
            negotiation_style=supplier["negotiation_style"]
        )
        
        if result.get("success"):
            registered_count += 1
            print(f"✓ Registered {supplier['company_name']} ({supplier['region']})")
        else:
            print(f"✗ Failed to register {supplier['company_name']}: {result.get('error')}")
    
    # Add products to each supplier's catalog
    for supplier_id, products in SUPPLIER_CATALOGS.items():
        for product in products:
            result = SupplierRegistry.add_product_to_supplier(
                supplier_id=supplier_id,
                product_id=product["product_id"],
                product_name=product["product_name"],
                category=product["category"],
                unit_price=product["unit_price"],
                stock_quantity=product["stock_quantity"],
                lead_time_days=product["lead_time_days"],
                certifications_required=product.get("certifications_required", [])
            )
            
            if result.get("success"):
                product_count += 1
                print(f"  + {product['product_name']} (€{product['unit_price']})")
    
    print(f"\n=== Seed Complete ===")
    print(f"Suppliers registered: {registered_count}")
    print(f"Products added: {product_count}\n")
    
    return {
        "suppliers_registered": registered_count,
        "products_added": product_count
    }


if __name__ == "__main__":
    # Can run directly to seed
    seed_suppliers()
