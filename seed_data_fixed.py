from db import get_conn
"""
seed_data.py
Run this once to populate all 11 tables with realistic mock data.
Covers all 5 buyer agents:
  - Procurement Intent Parser
  - Supplier Discovery Agent
  - Macro Intelligence Agent
  - Risk Assessment Agent
  - Negotiation Agent

Usage:
    python seed_data.py
"""

import json
from datetime import datetime, timedelta

def seed():
    conn = get_conn()
    c = conn.cursor()

    # ------------------------------------------------------------------
    # TABLE 1: buyers
    # ------------------------------------------------------------------
    buyers = [
        {
            "id": "buyer-001",
            "company_name": "Volta Systems GmbH",
            "country": "Germany",
            "region": "EU",
            "industry": "Industrial Automation",
            "negotiation_style": "balanced",
            "is_active": 1,
            "registered_at": "2023-06-01T09%(00)s%(00Z)s"
        },
        {
            "id": "buyer-002",
            "company_name": "Nordic Precision AB",
            "country": "Sweden",
            "region": "EU",
            "industry": "Medical Devices",
            "negotiation_style": "quality_first",
            "is_active": 1,
            "registered_at": "2023-08-15T10%(00)s%(00Z)s"
        },
        {
            "id": "buyer-003",
            "company_name": "Gulf Tech Industries",
            "country": "UAE",
            "region": "Middle East",
            "industry": "Oil & Gas Instrumentation",
            "negotiation_style": "aggressive",
            "is_active": 1,
            "registered_at": "2023-11-20T08%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO buyers
        (id, company_name, country, region, industry, negotiation_style, is_active, registered_at)
        VALUES (%(id)s, %(company_name)s, %(country)s, %(region)s, %(industry)s, %(negotiation_style)s, %(is_active)s, %(registered_at)s)
    """, buyers)

    # ------------------------------------------------------------------
    # TABLE 2: suppliers
    # ------------------------------------------------------------------
    suppliers = [
        {
            "id": "sup-001",
            "name": "Berlin Electronics GmbH",
            "country": "Germany",
            "region": "EU",
            "categories": json.dumps(["temperature_sensors", "NTC_thermistors", "RTD_sensors"]),
            "certifications": json.dumps(["CE", "ISO9001", "RoHS"]),
            "capacity_per_month": 50000,
            "min_order_qty": 100,
            "avg_lead_time_days": 8,
            "endpoint": "http://localhost%(8001)s",
            "is_active": 1,
            "registered_at": "2023-05-10T08%(00)s%(00Z)s"
        },
        {
            "id": "sup-002",
            "name": "Tokyo Micro Components",
            "country": "Japan",
            "region": "Asia",
            "categories": json.dumps(["temperature_sensors", "precision_sensors", "MCU_modules"]),
            "certifications": json.dumps(["CE", "ISO9001", "JEDEC", "RoHS"]),
            "capacity_per_month": 80000,
            "min_order_qty": 50,
            "avg_lead_time_days": 14,
            "endpoint": "http://localhost%(8002)s",
            "is_active": 1,
            "registered_at": "2023-05-15T09%(00)s%(00Z)s"
        },
        {
            "id": "sup-003",
            "name": "Chicago Industrial Supply",
            "country": "USA",
            "region": "North America",
            "categories": json.dumps(["pressure_sensors", "temperature_sensors", "industrial_sensors"]),
            "certifications": json.dumps(["UL", "REACH", "ISO9001", "CE"]),
            "capacity_per_month": 30000,
            "min_order_qty": 200,
            "avg_lead_time_days": 10,
            "endpoint": "http://localhost%(8003)s",
            "is_active": 1,
            "registered_at": "2023-06-01T10%(00)s%(00Z)s"
        },
        {
            "id": "sup-004",
            "name": "Shenzhen Parts Co.",
            "country": "China",
            "region": "Asia",
            "categories": json.dumps(["MCU_modules", "passive_components", "temperature_sensors"]),
            "certifications": json.dumps(["RoHS", "CE"]),
            "capacity_per_month": 200000,
            "min_order_qty": 500,
            "avg_lead_time_days": 18,
            "endpoint": "http://localhost%(8004)s",
            "is_active": 1,
            "registered_at": "2023-07-01T07%(00)s%(00Z)s"
        },
        {
            "id": "sup-005",
            "name": "Rotterdam Trade Partners",
            "country": "Netherlands",
            "region": "EU",
            "categories": json.dumps(["temperature_sensors", "flow_sensors", "pressure_sensors"]),
            "certifications": json.dumps(["CE", "ISO9001", "ATEX", "RoHS"]),
            "capacity_per_month": 25000,
            "min_order_qty": 100,
            "avg_lead_time_days": 7,
            "endpoint": "http://localhost%(8005)s",
            "is_active": 1,
            "registered_at": "2023-07-20T11%(00)s%(00Z)s"
        },
        {
            "id": "sup-006",
            "name": "Seoul Sensor Works",
            "country": "South Korea",
            "region": "Asia",
            "categories": json.dumps(["precision_sensors", "RTD_sensors", "temperature_sensors"]),
            "certifications": json.dumps(["CE", "ISO9001", "KS", "RoHS"]),
            "capacity_per_month": 40000,
            "min_order_qty": 100,
            "avg_lead_time_days": 12,
            "endpoint": "http://localhost%(8006)s",
            "is_active": 1,
            "registered_at": "2023-09-05T09%(00)s%(00Z)s"
        },
        {
            "id": "sup-007",
            "name": "Milan Precision Parts Srl",
            "country": "Italy",
            "region": "EU",
            "categories": json.dumps(["pressure_sensors", "industrial_sensors", "flow_sensors"]),
            "certifications": json.dumps(["CE", "ISO9001", "ATEX", "REACH"]),
            "capacity_per_month": 15000,
            "min_order_qty": 50,
            "avg_lead_time_days": 9,
            "endpoint": "http://localhost%(8007)s",
            "is_active": 1,
            "registered_at": "2023-10-01T08%(30)s%(00Z)s"
        },
        {
            "id": "sup-008",
            "name": "Mumbai Components Ltd",
            "country": "India",
            "region": "Asia",
            "categories": json.dumps(["passive_components", "temperature_sensors", "industrial_sensors"]),
            "certifications": json.dumps(["CE", "RoHS", "BIS"]),
            "capacity_per_month": 60000,
            "min_order_qty": 300,
            "avg_lead_time_days": 16,
            "endpoint": "http://localhost%(8008)s",
            "is_active": 1,
            "registered_at": "2023-11-01T07%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO suppliers
        (id, name, country, region, categories, certifications,
         capacity_per_month, min_order_qty, avg_lead_time_days,
         endpoint, is_active, registered_at)
        VALUES (%(id)s, %(name)s, %(country)s, %(region)s, %(categories)s, %(certifications)s,
                %(capacity_per_month)s, %(min_order_qty)s, %(avg_lead_time_days)s,
                %(endpoint)s, %(is_active)s, %(registered_at)s)
    """, suppliers)

    # ------------------------------------------------------------------
    # TABLE 3: orders
    # ------------------------------------------------------------------
    orders = [
        {
            "id": "ord-001",
            "buyer_id": "buyer-001",
            "status": "delivered",
            "priority": "standard",
            "delivery_region": "EU",
            "delivery_deadline": "2024-10-15",
            "total_budget_ceiling": 1000.00,
            "total_agreed_value_eur": 720.00,
            "negotiation_style": "balanced",
            "contract_id": "ctr-001",
            "created_at": "2024-09-28T08%(00)s%(00Z)s",
            "confirmed_at": "2024-09-30T14%(00)s%(00Z)s",
            "closed_at": "2024-10-14T10%(00)s%(00Z)s"
        },
        {
            "id": "ord-002",
            "buyer_id": "buyer-001",
            "status": "delivered",
            "priority": "urgent",
            "delivery_region": "EU",
            "delivery_deadline": "2024-07-20",
            "total_budget_ceiling": 600.00,
            "total_agreed_value_eur": 438.00,
            "negotiation_style": "aggressive",
            "contract_id": "ctr-002",
            "created_at": "2024-07-01T09%(00)s%(00Z)s",
            "confirmed_at": "2024-07-03T11%(00)s%(00Z)s",
            "closed_at": "2024-07-19T15%(00)s%(00Z)s"
        },
        {
            "id": "ord-003",
            "buyer_id": "buyer-001",
            "status": "disputed",
            "priority": "standard",
            "delivery_region": "North America",
            "delivery_deadline": "2024-08-10",
            "total_budget_ceiling": 1000.00,
            "total_agreed_value_eur": 910.00,
            "negotiation_style": "balanced",
            "contract_id": "ctr-003",
            "created_at": "2024-07-20T08%(00)s%(00Z)s",
            "confirmed_at": "2024-07-22T10%(00)s%(00Z)s",
            "closed_at": "2024-08-20T09%(00)s%(00Z)s"
        },
        {
            "id": "ord-004",
            "buyer_id": "buyer-002",
            "status": "delivered",
            "priority": "standard",
            "delivery_region": "EU",
            "delivery_deadline": "2024-11-30",
            "total_budget_ceiling": 3000.00,
            "total_agreed_value_eur": 2640.00,
            "negotiation_style": "quality_first",
            "contract_id": "ctr-004",
            "created_at": "2024-11-01T09%(00)s%(00Z)s",
            "confirmed_at": "2024-11-05T14%(00)s%(00Z)s",
            "closed_at": "2024-11-28T11%(00)s%(00Z)s"
        },
        {
            "id": "ord-005",
            "buyer_id": "buyer-001",
            "status": "negotiating",
            "priority": "standard",
            "delivery_region": "EU",
            "delivery_deadline": "2025-03-01",
            "total_budget_ceiling": 1200.00,
            "total_agreed_value_eur": None,
            "negotiation_style": "balanced",
            "contract_id": None,
            "created_at": "2025-01-20T08%(00)s%(00Z)s",
            "confirmed_at": None,
            "closed_at": None
        }
    ]

    c.executemany("""
        INSERT INTO orders
        (id, buyer_id, status, priority, delivery_region, delivery_deadline,
         total_budget_ceiling, total_agreed_value_eur, negotiation_style,
         contract_id, created_at, confirmed_at, closed_at)
        VALUES (%(id)s, %(buyer_id)s, %(status)s, %(priority)s, %(delivery_region)s, %(delivery_deadline)s,
                %(total_budget_ceiling)s, %(total_agreed_value_eur)s, %(negotiation_style)s,
                %(contract_id)s, %(created_at)s, %(confirmed_at)s, %(closed_at)s)
    """, orders)

    # ------------------------------------------------------------------
    # TABLE 4: order_line_items
    # ------------------------------------------------------------------
    line_items = [
        # ord-001: NTC Thermistors from sup-001
        {
            "id": "li-001",
            "order_id": "ord-001",
            "supplier_id": "sup-001",
            "product_name": "temperature sensor",
            "product_category": "temperature_sensors",
            "quantity": 500,
            "target_unit_price": 1.40,
            "max_unit_price": 1.65,
            "min_quality_tier": "certified",
            "agent_instruction": "bargain hard, close below 1.50 if possible",
            "resolved_product_name": "NTC Thermistor 10kΩ",
            "required_certifications": json.dumps(["CE", "RoHS"]),
            "key_specs": json.dumps({"resistance": "10k", "tolerance": "1%", "temp_range": "-40 to 125C"}),
            "intent_confidence_score": 0.91,
            "status": "agreed",
            "agreed_unit_price": 1.44,
            "agreed_lead_time_days": 7,
            "agreed_payment_terms": "Net-15",
            "created_at": "2024-09-28T08%(00)s%(00Z)s"
        },
        # ord-002: NTC Thermistors urgent repeat
        {
            "id": "li-002",
            "order_id": "ord-002",
            "supplier_id": "sup-001",
            "product_name": "NTC thermistor 10k",
            "product_category": "temperature_sensors",
            "quantity": 300,
            "target_unit_price": 1.38,
            "max_unit_price": 1.60,
            "min_quality_tier": "certified",
            "agent_instruction": "push hard on price, we have history with this supplier",
            "resolved_product_name": "NTC Thermistor 10kΩ",
            "required_certifications": json.dumps(["CE", "RoHS"]),
            "key_specs": json.dumps({"resistance": "10k", "tolerance": "1%", "temp_range": "-40 to 125C"}),
            "intent_confidence_score": 0.97,
            "status": "agreed",
            "agreed_unit_price": 1.46,
            "agreed_lead_time_days": 8,
            "agreed_payment_terms": "Net-30",
            "created_at": "2024-07-01T09%(00)s%(00Z)s"
        },
        # ord-003: Pressure sensors from sup-003 (late delivery dispute)
        {
            "id": "li-003",
            "order_id": "ord-003",
            "supplier_id": "sup-003",
            "product_name": "pressure sensor 0 to 10 bar",
            "product_category": "pressure_sensors",
            "quantity": 100,
            "target_unit_price": 8.50,
            "max_unit_price": 9.80,
            "min_quality_tier": "certified",
            "agent_instruction": "need IP67 rated, delivery by Aug 10 is hard deadline",
            "resolved_product_name": "Industrial Pressure Sensor 0-10bar",
            "required_certifications": json.dumps(["CE", "ISO9001"]),
            "key_specs": json.dumps({"range": "0-10bar", "output": "4-20mA", "protection": "IP67"}),
            "intent_confidence_score": 0.88,
            "status": "agreed",
            "agreed_unit_price": 9.10,
            "agreed_lead_time_days": 10,
            "agreed_payment_terms": "Net-30",
            "created_at": "2024-07-20T08%(00)s%(00Z)s"
        },
        # ord-004: RTD sensors for Nordic Precision (medical, quality first)
        {
            "id": "li-004",
            "order_id": "ord-004",
            "supplier_id": "sup-001",
            "product_name": "RTD PT100",
            "product_category": "RTD_sensors",
            "quantity": 800,
            "target_unit_price": 3.20,
            "max_unit_price": 3.80,
            "min_quality_tier": "premium_certified",
            "agent_instruction": "quality and cert compliance is priority over price",
            "resolved_product_name": "RTD PT100 Sensor",
            "required_certifications": json.dumps(["CE", "ISO9001", "RoHS"]),
            "key_specs": json.dumps({"type": "PT100", "class": "A", "protection": "IP65"}),
            "intent_confidence_score": 0.95,
            "status": "agreed",
            "agreed_unit_price": 3.30,
            "agreed_lead_time_days": 8,
            "agreed_payment_terms": "Net-30",
            "created_at": "2024-11-01T09%(00)s%(00Z)s"
        },
        # ord-005: active negotiation (used by live agents)
        {
            "id": "li-005",
            "order_id": "ord-005",
            "supplier_id": None,
            "product_name": "temperature sensor",
            "product_category": "temperature_sensors",
            "quantity": 600,
            "target_unit_price": 1.42,
            "max_unit_price": 1.68,
            "min_quality_tier": "certified",
            "agent_instruction": "close fast, copper prices are rising",
            "resolved_product_name": "NTC Thermistor 10kΩ",
            "required_certifications": json.dumps(["CE", "RoHS"]),
            "key_specs": json.dumps({"resistance": "10k", "tolerance": "1%", "temp_range": "-40 to 125C"}),
            "intent_confidence_score": 0.90,
            "status": "negotiating",
            "agreed_unit_price": None,
            "agreed_lead_time_days": None,
            "agreed_payment_terms": None,
            "created_at": "2025-01-20T08%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO order_line_items
        (id, order_id, supplier_id, product_name, product_category, quantity,
         target_unit_price, max_unit_price, min_quality_tier, agent_instruction,
         resolved_product_name, required_certifications, key_specs,
         intent_confidence_score, status, agreed_unit_price,
         agreed_lead_time_days, agreed_payment_terms, created_at)
        VALUES (%(id)s, %(order_id)s, %(supplier_id)s, %(product_name)s, %(product_category)s, %(quantity)s,
                %(target_unit_price)s, %(max_unit_price)s, %(min_quality_tier)s, %(agent_instruction)s,
                %(resolved_product_name)s, %(required_certifications)s, %(key_specs)s,
                %(intent_confidence_score)s, %(status)s, %(agreed_unit_price)s,
                %(agreed_lead_time_days)s, %(agreed_payment_terms)s, %(created_at)s)
    """, line_items)

    # ------------------------------------------------------------------
    # TABLE 5: supplier_catalog
    # ------------------------------------------------------------------
    catalog = [
        # sup-001 Berlin Electronics
        {
            "id": "cat-001", "supplier_id": "sup-001",
            "product_name": "NTC Thermistor 10kΩ",
            "product_category": "temperature_sensors",
            "base_unit_price": 1.52, "currency": "EUR",
            "stock_available": 12000, "lead_time_days": 7, "min_order_qty": 100,
            "specs": json.dumps({"resistance": "10k", "tolerance": "1%", "temp_range": "-40 to 125C", "package": "SMD 0402"}),
            "is_available": 1, "updated_at": "2025-01-18T06%(00)s%(00Z)s"
        },
        {
            "id": "cat-002", "supplier_id": "sup-001",
            "product_name": "RTD PT100 Sensor Class B",
            "product_category": "RTD_sensors",
            "base_unit_price": 3.40, "currency": "EUR",
            "stock_available": 3000, "lead_time_days": 8, "min_order_qty": 50,
            "specs": json.dumps({"type": "PT100", "class": "B", "protection": "IP65", "output": "2-wire"}),
            "is_available": 1, "updated_at": "2025-01-18T06%(00)s%(00Z)s"
        },
        {
            "id": "cat-003", "supplier_id": "sup-001",
            "product_name": "RTD PT100 Sensor Class A",
            "product_category": "RTD_sensors",
            "base_unit_price": 3.85, "currency": "EUR",
            "stock_available": 1500, "lead_time_days": 10, "min_order_qty": 50,
            "specs": json.dumps({"type": "PT100", "class": "A", "protection": "IP65", "output": "3-wire"}),
            "is_available": 1, "updated_at": "2025-01-18T06%(00)s%(00Z)s"
        },
        # sup-002 Tokyo Micro
        {
            "id": "cat-004", "supplier_id": "sup-002",
            "product_name": "NTC Thermistor 10kΩ High Precision",
            "product_category": "temperature_sensors",
            "base_unit_price": 1.48, "currency": "EUR",
            "stock_available": 20000, "lead_time_days": 14, "min_order_qty": 50,
            "specs": json.dumps({"resistance": "10k", "tolerance": "0.5%", "temp_range": "-55 to 150C", "package": "SMD 0603"}),
            "is_available": 1, "updated_at": "2025-01-17T06%(00)s%(00Z)s"
        },
        {
            "id": "cat-005", "supplier_id": "sup-002",
            "product_name": "ARM Cortex-M4 MCU Module",
            "product_category": "MCU_modules",
            "base_unit_price": 4.20, "currency": "EUR",
            "stock_available": 5000, "lead_time_days": 18, "min_order_qty": 50,
            "specs": json.dumps({"core": "ARM Cortex-M4", "flash": "256KB", "ram": "64KB", "interface": "SPI/I2C/UART"}),
            "is_available": 1, "updated_at": "2025-01-17T06%(00)s%(00Z)s"
        },
        # sup-003 Chicago Industrial
        {
            "id": "cat-006", "supplier_id": "sup-003",
            "product_name": "Industrial Pressure Sensor 0-10bar",
            "product_category": "pressure_sensors",
            "base_unit_price": 9.20, "currency": "EUR",
            "stock_available": 1200, "lead_time_days": 10, "min_order_qty": 200,
            "specs": json.dumps({"range": "0-10bar", "output": "4-20mA", "protection": "IP67", "accuracy": "0.25%FS"}),
            "is_available": 1, "updated_at": "2025-01-15T06%(00)s%(00Z)s"
        },
        {
            "id": "cat-007", "supplier_id": "sup-003",
            "product_name": "NTC Thermistor 10kΩ Industrial",
            "product_category": "temperature_sensors",
            "base_unit_price": 1.65, "currency": "EUR",
            "stock_available": 4000, "lead_time_days": 10, "min_order_qty": 200,
            "specs": json.dumps({"resistance": "10k", "tolerance": "2%", "temp_range": "-40 to 125C", "package": "Through-hole"}),
            "is_available": 1, "updated_at": "2025-01-15T06%(00)s%(00Z)s"
        },
        # sup-004 Shenzhen
        {
            "id": "cat-008", "supplier_id": "sup-004",
            "product_name": "NTC Thermistor 10kΩ Standard",
            "product_category": "temperature_sensors",
            "base_unit_price": 0.92, "currency": "EUR",
            "stock_available": 150000, "lead_time_days": 18, "min_order_qty": 500,
            "specs": json.dumps({"resistance": "10k", "tolerance": "5%", "temp_range": "-20 to 105C", "package": "SMD 0402"}),
            "is_available": 1, "updated_at": "2025-01-10T06%(00)s%(00Z)s"
        },
        # sup-005 Rotterdam
        {
            "id": "cat-009", "supplier_id": "sup-005",
            "product_name": "NTC Thermistor 10kΩ ATEX",
            "product_category": "temperature_sensors",
            "base_unit_price": 2.10, "currency": "EUR",
            "stock_available": 3000, "lead_time_days": 7, "min_order_qty": 100,
            "specs": json.dumps({"resistance": "10k", "tolerance": "1%", "temp_range": "-40 to 125C", "certification": "ATEX Zone 1"}),
            "is_available": 1, "updated_at": "2025-01-18T06%(00)s%(00Z)s"
        },
        {
            "id": "cat-010", "supplier_id": "sup-005",
            "product_name": "Flow Sensor Electromagnetic DN25",
            "product_category": "flow_sensors",
            "base_unit_price": 148.00, "currency": "EUR",
            "stock_available": 200, "lead_time_days": 14, "min_order_qty": 10,
            "specs": json.dumps({"type": "electromagnetic", "size": "DN25", "output": "4-20mA", "protection": "IP68"}),
            "is_available": 1, "updated_at": "2025-01-18T06%(00)s%(00Z)s"
        },
        # sup-006 Seoul
        {
            "id": "cat-011", "supplier_id": "sup-006",
            "product_name": "RTD PT1000 Precision Sensor",
            "product_category": "RTD_sensors",
            "base_unit_price": 4.10, "currency": "EUR",
            "stock_available": 5000, "lead_time_days": 12, "min_order_qty": 100,
            "specs": json.dumps({"type": "PT1000", "class": "A", "protection": "IP67", "accuracy": "±0.1C"}),
            "is_available": 1, "updated_at": "2025-01-16T06%(00)s%(00Z)s"
        },
        # sup-007 Milan
        {
            "id": "cat-012", "supplier_id": "sup-007",
            "product_name": "Industrial Pressure Sensor 0-16bar ATEX",
            "product_category": "pressure_sensors",
            "base_unit_price": 14.50, "currency": "EUR",
            "stock_available": 500, "lead_time_days": 9, "min_order_qty": 50,
            "specs": json.dumps({"range": "0-16bar", "output": "4-20mA", "protection": "IP67", "certification": "ATEX Zone 2"}),
            "is_available": 1, "updated_at": "2025-01-17T06%(00)s%(00Z)s"
        },
        # sup-008 Mumbai
        {
            "id": "cat-013", "supplier_id": "sup-008",
            "product_name": "NTC Thermistor 10kΩ Standard",
            "product_category": "temperature_sensors",
            "base_unit_price": 1.10, "currency": "EUR",
            "stock_available": 30000, "lead_time_days": 16, "min_order_qty": 300,
            "specs": json.dumps({"resistance": "10k", "tolerance": "3%", "temp_range": "-30 to 110C", "package": "SMD 0603"}),
            "is_available": 1, "updated_at": "2025-01-12T06%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO supplier_catalog
        (id, supplier_id, product_name, product_category, base_unit_price,
         currency, stock_available, lead_time_days, min_order_qty,
         specs, is_available, updated_at)
        VALUES (%(id)s, %(supplier_id)s, %(product_name)s, %(product_category)s, %(base_unit_price)s,
                %(currency)s, %(stock_available)s, %(lead_time_days)s, %(min_order_qty)s,
                %(specs)s, %(is_available)s, %(updated_at)s)
    """, catalog)

    # ------------------------------------------------------------------
    # TABLE 6: negotiation_history
    # ------------------------------------------------------------------
    neg_history = [
        # ord-001 li-001 — 3 rounds, closed
        {
            "id": "neg-001", "order_id": "ord-001", "order_line_item_id": "li-001",
            "buyer_id": "buyer-001", "supplier_id": "sup-001", "round_number": 1,
            "initiated_by": "buyer_agent",
            "buyer_offer": 1.40, "supplier_offer": 1.52,
            "buyer_message": "We request 500 units of NTC Thermistor 10kΩ at €1.40. Based on market average of €1.50, this reflects our volume commitment and our relationship history with you.",
            "supplier_message": "Our base price is €1.52 per unit for this specification. We can discuss further.",
            "concession_offered": None,
            "macro_signals_active": json.dumps(["sig-001"]),
            "round_status": "countered",
            "hitl_reason": None, "hitl_resolved_at": None, "hitl_decision": None,
            "created_at": "2024-09-29T09%(00)s%(00Z)s"
        },
        {
            "id": "neg-002", "order_id": "ord-001", "order_line_item_id": "li-001",
            "buyer_id": "buyer-001", "supplier_id": "sup-001", "round_number": 2,
            "initiated_by": "buyer_agent",
            "buyer_offer": 1.44, "supplier_offer": 1.48,
            "buyer_message": "We can move to €1.44 and offer Net-15 payment terms instead of standard Net-30. Our two prior orders closed at €1.44 and €1.46. We are consistent buyers.",
            "supplier_message": "We can come down to €1.48 with Net-15 terms accepted.",
            "concession_offered": json.dumps({"type": "payment_terms", "value": "Net-15"}),
            "macro_signals_active": json.dumps(["sig-001"]),
            "round_status": "countered",
            "hitl_reason": None, "hitl_resolved_at": None, "hitl_decision": None,
            "created_at": "2024-09-29T11%(00)s%(00Z)s"
        },
        {
            "id": "neg-003", "order_id": "ord-001", "order_line_item_id": "li-001",
            "buyer_id": "buyer-001", "supplier_id": "sup-001", "round_number": 3,
            "initiated_by": "buyer_agent",
            "buyer_offer": 1.44, "supplier_offer": 1.44,
            "buyer_message": "We will commit to a repeat order within 60 days if you match €1.44 with Net-15.",
            "supplier_message": "Accepted. €1.44 per unit, Net-15, 500 units, delivery in 7 days.",
            "concession_offered": json.dumps({"type": "volume_commitment", "value": "repeat_order_60_days"}),
            "macro_signals_active": json.dumps(["sig-001"]),
            "round_status": "accepted",
            "hitl_reason": None, "hitl_resolved_at": None, "hitl_decision": None,
            "created_at": "2024-09-29T14%(00)s%(00Z)s"
        },
        # ord-002 li-002 — 4 rounds, harder negotiation
        {
            "id": "neg-004", "order_id": "ord-002", "order_line_item_id": "li-002",
            "buyer_id": "buyer-001", "supplier_id": "sup-001", "round_number": 1,
            "initiated_by": "buyer_agent",
            "buyer_offer": 1.38, "supplier_offer": 1.52,
            "buyer_message": "Requesting 300 units at €1.38. Previous order closed at €1.44. We are asking for volume continuity pricing.",
            "supplier_message": "Base price remains €1.52.",
            "concession_offered": None,
            "macro_signals_active": None,
            "round_status": "countered",
            "hitl_reason": None, "hitl_resolved_at": None, "hitl_decision": None,
            "created_at": "2024-07-02T09%(00)s%(00Z)s"
        },
        {
            "id": "neg-005", "order_id": "ord-002", "order_line_item_id": "li-002",
            "buyer_id": "buyer-001", "supplier_id": "sup-001", "round_number": 2,
            "initiated_by": "buyer_agent",
            "buyer_offer": 1.42, "supplier_offer": 1.50,
            "buyer_message": "We can offer €1.42 with Net-30 unchanged.",
            "supplier_message": "We can do €1.50.",
            "concession_offered": None,
            "macro_signals_active": None,
            "round_status": "countered",
            "hitl_reason": None, "hitl_resolved_at": None, "hitl_decision": None,
            "created_at": "2024-07-02T11%(00)s%(00Z)s"
        },
        {
            "id": "neg-006", "order_id": "ord-002", "order_line_item_id": "li-002",
            "buyer_id": "buyer-001", "supplier_id": "sup-001", "round_number": 3,
            "initiated_by": "buyer_agent",
            "buyer_offer": 1.45, "supplier_offer": 1.47,
            "buyer_message": "Final stretch — €1.45 is our strong preference.",
            "supplier_message": "€1.47 is our best offer at this quantity.",
            "concession_offered": None,
            "macro_signals_active": None,
            "round_status": "countered",
            "hitl_reason": None, "hitl_resolved_at": None, "hitl_decision": None,
            "created_at": "2024-07-02T14%(00)s%(00Z)s"
        },
        {
            "id": "neg-007", "order_id": "ord-002", "order_line_item_id": "li-002",
            "buyer_id": "buyer-001", "supplier_id": "sup-001", "round_number": 4,
            "initiated_by": "buyer_agent",
            "buyer_offer": 1.46, "supplier_offer": 1.46,
            "buyer_message": "We accept €1.46 to close this today.",
            "supplier_message": "Agreed at €1.46. Net-30.",
            "concession_offered": None,
            "macro_signals_active": None,
            "round_status": "accepted",
            "hitl_reason": None, "hitl_resolved_at": None, "hitl_decision": None,
            "created_at": "2024-07-02T16%(00)s%(00Z)s"
        },
        # ord-005 li-005 — active round 1 (live negotiation for agents)
        {
            "id": "neg-008", "order_id": "ord-005", "order_line_item_id": "li-005",
            "buyer_id": "buyer-001", "supplier_id": "sup-001", "round_number": 1,
            "initiated_by": "buyer_agent",
            "buyer_offer": 1.42, "supplier_offer": 1.52,
            "buyer_message": "We are requesting 600 units at €1.42. Copper prices are rising — we want to lock in before further increases. Our three prior orders with you average €1.45.",
            "supplier_message": "Current price is €1.52 per unit.",
            "concession_offered": None,
            "macro_signals_active": json.dumps(["sig-001", "sig-002"]),
            "round_status": "countered",
            "hitl_reason": None, "hitl_resolved_at": None, "hitl_decision": None,
            "created_at": "2025-01-21T09%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO negotiation_history
        (id, order_id, order_line_item_id, buyer_id, supplier_id, round_number,
         initiated_by, buyer_offer, supplier_offer, buyer_message, supplier_message,
         concession_offered, macro_signals_active, round_status,
         hitl_reason, hitl_resolved_at, hitl_decision, created_at)
        VALUES (%(id)s, %(order_id)s, %(order_line_item_id)s, %(buyer_id)s, %(supplier_id)s, %(round_number)s,
                %(initiated_by)s, %(buyer_offer)s, %(supplier_offer)s, %(buyer_message)s, %(supplier_message)s,
                %(concession_offered)s, %(macro_signals_active)s, %(round_status)s,
                %(hitl_reason)s, %(hitl_resolved_at)s, %(hitl_decision)s, %(created_at)s)
    """, neg_history)

    # ------------------------------------------------------------------
    # TABLE 7: macro_signals
    # ------------------------------------------------------------------
    macro_signals = [
        {
            "id": "sig-001",
            "signal_type": "commodity",
            "affected_category": "temperature_sensors",
            "severity": "medium",
            "direction": "price_up",
            "headline": "Copper prices up 8.2% this week — component cost pressure incoming",
            "detail": "LME copper spot hit $9,840/tonne. Components with copper content (NTC thermistors, RTDs, wiring) will see 5-10% cost pressure within 2-3 weeks as suppliers reprice inventory.",
            "recommendation": "Close open RFQs for copper-content components immediately. Do not delay for additional negotiation rounds.",
            "source": "commodity_feed",
            "valid_until": "2025-02-15",
            "created_at": "2025-01-18T06%(00)s%(00Z)s"
        },
        {
            "id": "sig-002",
            "signal_type": "logistics",
            "affected_category": "EU_logistics",
            "severity": "medium",
            "direction": "delay_risk",
            "headline": "Rotterdam port congestion — 3 to 5 day delays on EU shipments",
            "detail": "Rotterdam port congestion index at 78/100. EU-bound surface freight experiencing 3-5 business day delays. Affects suppliers in Netherlands, Germany, Belgium.",
            "recommendation": "Build 5-day delivery buffer into any EU supplier contracts. Request air freight option or alternative routing for critical path items.",
            "source": "port_monitoring",
            "valid_until": "2025-02-20",
            "created_at": "2025-01-19T07%(00)s%(00Z)s"
        },
        {
            "id": "sig-003",
            "signal_type": "geopolitical",
            "affected_category": "Asia_suppliers",
            "severity": "low",
            "direction": "supply_risk",
            "headline": "Taiwan Strait shipping insurance premiums up 12%",
            "detail": "Shipping insurance premiums for Taiwan Strait routes increased 12% over past 30 days. Most component shipments from Japan and South Korea remain unaffected operationally, but monitoring is recommended for critical sourcing.",
            "recommendation": "For critical components sourced from Taiwan or coastal Japan, qualify a European or US alternative as backup.",
            "source": "geopolitical_feed",
            "valid_until": "2025-03-01",
            "created_at": "2025-01-15T08%(00)s%(00Z)s"
        },
        {
            "id": "sig-004",
            "signal_type": "supplier_health",
            "affected_category": "North_America_suppliers",
            "severity": "low",
            "direction": "supply_risk",
            "headline": "Chicago Industrial Supply — Q4 earnings miss, watch closely",
            "detail": "Chicago Industrial Supply (sup-003) reported Q4 revenue 14% below forecast. No immediate operational risk, but financial distress signals warrant increased monitoring. Credit rating agency placed on watch negative.",
            "recommendation": "For new orders with Chicago Industrial, request partial payment on delivery instead of full Net-30. Qualify an EU backup supplier for pressure sensors.",
            "source": "manual",
            "valid_until": "2025-03-15",
            "created_at": "2025-01-10T09%(00)s%(00Z)s"
        },
        {
            "id": "sig-005",
            "signal_type": "commodity",
            "affected_category": "MCU_modules",
            "severity": "high",
            "direction": "price_down",
            "headline": "MCU chip oversupply — prices falling 12-15% over next 6 weeks",
            "detail": "TSMC and Samsung both increased fab capacity for ARM Cortex-M series. Platform demand data shows 23% drop in MCU RFQ volume. Spot prices are already down 8% from Q3 peak.",
            "recommendation": "Delay MCU module purchases 3-4 weeks if not urgent. Negotiate hard — suppliers have excess inventory and need to move it.",
            "source": "commodity_feed",
            "valid_until": "2025-03-01",
            "created_at": "2025-01-17T07%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO macro_signals
        (id, signal_type, affected_category, severity, direction,
         headline, detail, recommendation, source, valid_until, created_at)
        VALUES (%(id)s, %(signal_type)s, %(affected_category)s, %(severity)s, %(direction)s,
                %(headline)s, %(detail)s, %(recommendation)s, %(source)s, %(valid_until)s, %(created_at)s)
    """, macro_signals)

    # ------------------------------------------------------------------
    # TABLE 8: fulfillment_events
    # ------------------------------------------------------------------
    fulfillment_events = [
        # ord-001 li-001 — clean delivery
        {"id": "fe-001", "order_id": "ord-001", "order_line_item_id": "li-001", "supplier_id": "sup-001", "buyer_id": "buyer-001", "event_type": "order_confirmed", "scheduled_at": "2024-09-30T00%(00)s%(00Z)s", "happened_at": "2024-09-30T14%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": None, "recorded_by": "platform", "notes": "Order confirmed after negotiation closed.", "metadata": None, "created_at": "2024-09-30T14%(00)s%(00Z)s"},
        {"id": "fe-002", "order_id": "ord-001", "order_line_item_id": "li-001", "supplier_id": "sup-001", "buyer_id": "buyer-001", "event_type": "production_started", "scheduled_at": "2024-10-01T00%(00)s%(00Z)s", "happened_at": "2024-10-01T08%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": None, "recorded_by": "supplier_agent", "notes": None, "metadata": None, "created_at": "2024-10-01T08%(00)s%(00Z)s"},
        {"id": "fe-003", "order_id": "ord-001", "order_line_item_id": "li-001", "supplier_id": "sup-001", "buyer_id": "buyer-001", "event_type": "quality_check_passed", "scheduled_at": "2024-10-05T00%(00)s%(00Z)s", "happened_at": "2024-10-05T10%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": None, "recorded_by": "supplier_agent", "notes": "All 500 units passed CE compliance check.", "metadata": None, "created_at": "2024-10-05T10%(00)s%(00Z)s"},
        {"id": "fe-004", "order_id": "ord-001", "order_line_item_id": "li-001", "supplier_id": "sup-001", "buyer_id": "buyer-001", "event_type": "shipped", "scheduled_at": "2024-10-06T00%(00)s%(00Z)s", "happened_at": "2024-10-06T12%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": "DHL-DE-4492817", "recorded_by": "carrier_api", "notes": None, "metadata": json.dumps({"carrier": "DHL", "service": "Express"}), "created_at": "2024-10-06T12%(00)s%(00Z)s"},
        {"id": "fe-005", "order_id": "ord-001", "order_line_item_id": "li-001", "supplier_id": "sup-001", "buyer_id": "buyer-001", "event_type": "delivered", "scheduled_at": "2024-10-15T00%(00)s%(00Z)s", "happened_at": "2024-10-13T14%(00)s%(00Z)s", "delay_days": -2, "tracking_reference": "DHL-DE-4492817", "recorded_by": "carrier_api", "notes": "Delivered 2 days early.", "metadata": None, "created_at": "2024-10-13T14%(00)s%(00Z)s"},

        # ord-002 li-002 — clean, on time
        {"id": "fe-006", "order_id": "ord-002", "order_line_item_id": "li-002", "supplier_id": "sup-001", "buyer_id": "buyer-001", "event_type": "order_confirmed", "scheduled_at": "2024-07-03T00%(00)s%(00Z)s", "happened_at": "2024-07-03T11%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": None, "recorded_by": "platform", "notes": None, "metadata": None, "created_at": "2024-07-03T11%(00)s%(00Z)s"},
        {"id": "fe-007", "order_id": "ord-002", "order_line_item_id": "li-002", "supplier_id": "sup-001", "buyer_id": "buyer-001", "event_type": "shipped", "scheduled_at": "2024-07-10T00%(00)s%(00Z)s", "happened_at": "2024-07-10T09%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": "UPS-001-77634821", "recorded_by": "carrier_api", "notes": None, "metadata": json.dumps({"carrier": "UPS", "service": "Standard"}), "created_at": "2024-07-10T09%(00)s%(00Z)s"},
        {"id": "fe-008", "order_id": "ord-002", "order_line_item_id": "li-002", "supplier_id": "sup-001", "buyer_id": "buyer-001", "event_type": "delivered", "scheduled_at": "2024-07-20T00%(00)s%(00Z)s", "happened_at": "2024-07-19T15%(00)s%(00Z)s", "delay_days": -1, "tracking_reference": "UPS-001-77634821", "recorded_by": "carrier_api", "notes": "1 day early.", "metadata": None, "created_at": "2024-07-19T15%(00)s%(00Z)s"},

        # ord-003 li-003 — LATE delivery, dispute
        {"id": "fe-009", "order_id": "ord-003", "order_line_item_id": "li-003", "supplier_id": "sup-003", "buyer_id": "buyer-001", "event_type": "order_confirmed", "scheduled_at": "2024-07-22T00%(00)s%(00Z)s", "happened_at": "2024-07-22T10%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": None, "recorded_by": "platform", "notes": None, "metadata": None, "created_at": "2024-07-22T10%(00)s%(00Z)s"},
        {"id": "fe-010", "order_id": "ord-003", "order_line_item_id": "li-003", "supplier_id": "sup-003", "buyer_id": "buyer-001", "event_type": "shipped", "scheduled_at": "2024-07-30T00%(00)s%(00Z)s", "happened_at": "2024-08-03T11%(00)s%(00Z)s", "delay_days": 4, "tracking_reference": "FEDEX-US-88421093", "recorded_by": "carrier_api", "notes": "Supplier shipped 4 days late citing production backlog.", "metadata": None, "created_at": "2024-08-03T11%(00)s%(00Z)s"},
        {"id": "fe-011", "order_id": "ord-003", "order_line_item_id": "li-003", "supplier_id": "sup-003", "buyer_id": "buyer-001", "event_type": "delivered", "scheduled_at": "2024-08-10T00%(00)s%(00Z)s", "happened_at": "2024-08-15T13%(00)s%(00Z)s", "delay_days": 5, "tracking_reference": "FEDEX-US-88421093", "recorded_by": "carrier_api", "notes": "5 days late. Buyer production line impacted.", "metadata": None, "created_at": "2024-08-15T13%(00)s%(00Z)s"},
        {"id": "fe-012", "order_id": "ord-003", "order_line_item_id": "li-003", "supplier_id": "sup-003", "buyer_id": "buyer-001", "event_type": "dispute_opened", "scheduled_at": None, "happened_at": "2024-08-16T09%(00)s%(00Z)s", "delay_days": None, "tracking_reference": None, "recorded_by": "buyer_agent", "notes": "Dispute opened: 5-day late delivery caused €2,800 production line downtime.", "metadata": json.dumps({"dispute_value_eur": 2800, "claim_type": "consequential_loss"}), "created_at": "2024-08-16T09%(00)s%(00Z)s"},
        {"id": "fe-013", "order_id": "ord-003", "order_line_item_id": "li-003", "supplier_id": "sup-003", "buyer_id": "buyer-001", "event_type": "dispute_resolved", "scheduled_at": None, "happened_at": "2024-08-20T09%(00)s%(00Z)s", "delay_days": None, "tracking_reference": None, "recorded_by": "platform", "notes": "Resolved: supplier issued €500 credit note. Partial settlement accepted.", "metadata": json.dumps({"resolution": "partial_credit", "credit_eur": 500}), "created_at": "2024-08-20T09%(00)s%(00Z)s"},

        # ord-004 li-004 Nordic Precision — clean
        {"id": "fe-014", "order_id": "ord-004", "order_line_item_id": "li-004", "supplier_id": "sup-001", "buyer_id": "buyer-002", "event_type": "order_confirmed", "scheduled_at": "2024-11-05T00%(00)s%(00Z)s", "happened_at": "2024-11-05T14%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": None, "recorded_by": "platform", "notes": None, "metadata": None, "created_at": "2024-11-05T14%(00)s%(00Z)s"},
        {"id": "fe-015", "order_id": "ord-004", "order_line_item_id": "li-004", "supplier_id": "sup-001", "buyer_id": "buyer-002", "event_type": "quality_check_passed", "scheduled_at": "2024-11-15T00%(00)s%(00Z)s", "happened_at": "2024-11-15T10%(00)s%(00Z)s", "delay_days": 0, "tracking_reference": None, "recorded_by": "supplier_agent", "notes": "800 units — all Class A tolerance confirmed.", "metadata": None, "created_at": "2024-11-15T10%(00)s%(00Z)s"},
        {"id": "fe-016", "order_id": "ord-004", "order_line_item_id": "li-004", "supplier_id": "sup-001", "buyer_id": "buyer-002", "event_type": "delivered", "scheduled_at": "2024-11-30T00%(00)s%(00Z)s", "happened_at": "2024-11-28T11%(00)s%(00Z)s", "delay_days": -2, "tracking_reference": "DHL-DE-5519234", "recorded_by": "carrier_api", "notes": "2 days early.", "metadata": None, "created_at": "2024-11-28T11%(00)s%(00Z)s"}
    ]

    c.executemany("""
        INSERT INTO fulfillment_events
        (id, order_id, order_line_item_id, supplier_id, buyer_id,
         event_type, scheduled_at, happened_at, delay_days,
         tracking_reference, recorded_by, notes, metadata, created_at)
        VALUES (%(id)s, %(order_id)s, %(order_line_item_id)s, %(supplier_id)s, %(buyer_id)s,
                %(event_type)s, %(scheduled_at)s, %(happened_at)s, %(delay_days)s,
                %(tracking_reference)s, %(recorded_by)s, %(notes)s, %(metadata)s, %(created_at)s)
    """, fulfillment_events)

    # ------------------------------------------------------------------
    # TABLE 9: platform_reviews
    # ------------------------------------------------------------------
    reviews = [
        # ord-001: buyer reviews sup-001 — excellent
        {
            "id": "rev-001", "order_id": "ord-001",
            "reviewer_id": "buyer-001", "reviewer_type": "buyer",
            "reviewee_id": "sup-001", "reviewee_type": "supplier",
            "quality_score": 5, "delivery_score": 5,
            "communication_score": 5, "quote_accuracy_score": 5,
            "payment_score": None, "spec_clarity_score": None, "professionalism_score": None,
            "overall_score": 5,
            "written_review": "Excellent supplier. Delivered 2 days early, all units passed incoming inspection. Will prioritize for future orders.",
            "is_dispute": 0, "dispute_resolution": None,
            "created_at": "2024-10-14T16%(00)s%(00Z)s"
        },
        # sup-001 reviews buyer-001 — positive
        {
            "id": "rev-002", "order_id": "ord-001",
            "reviewer_id": "sup-001", "reviewer_type": "supplier",
            "reviewee_id": "buyer-001", "reviewee_type": "buyer",
            "quality_score": None, "delivery_score": None,
            "communication_score": None, "quote_accuracy_score": None,
            "payment_score": 5, "spec_clarity_score": 4, "professionalism_score": 5,
            "overall_score": 5,
            "written_review": "Reliable buyer. Clear specs, paid early, professional negotiation style.",
            "is_dispute": 0, "dispute_resolution": None,
            "created_at": "2024-10-15T09%(00)s%(00Z)s"
        },
        # ord-002: buyer reviews sup-001
        {
            "id": "rev-003", "order_id": "ord-002",
            "reviewer_id": "buyer-001", "reviewer_type": "buyer",
            "reviewee_id": "sup-001", "reviewee_type": "supplier",
            "quality_score": 5, "delivery_score": 5,
            "communication_score": 4, "quote_accuracy_score": 5,
            "payment_score": None, "spec_clarity_score": None, "professionalism_score": None,
            "overall_score": 5,
            "written_review": "Consistent quality again. Negotiation took 4 rounds this time but supplier was firm and fair.",
            "is_dispute": 0, "dispute_resolution": None,
            "created_at": "2024-07-20T10%(00)s%(00Z)s"
        },
        # ord-003: buyer reviews sup-003 — negative (late, dispute)
        {
            "id": "rev-004", "order_id": "ord-003",
            "reviewer_id": "buyer-001", "reviewer_type": "buyer",
            "reviewee_id": "sup-003", "reviewee_type": "supplier",
            "quality_score": 4, "delivery_score": 1,
            "communication_score": 3, "quote_accuracy_score": 4,
            "payment_score": None, "spec_clarity_score": None, "professionalism_score": None,
            "overall_score": 2,
            "written_review": "Product quality acceptable but 5-day late delivery caused real damage to our line. Dispute only partially resolved. Use with caution for time-sensitive orders.",
            "is_dispute": 1, "dispute_resolution": "Supplier issued €500 credit note. Partial settlement.",
            "created_at": "2024-08-21T10%(00)s%(00Z)s"
        },
        # sup-003 reviews buyer-001
        {
            "id": "rev-005", "order_id": "ord-003",
            "reviewer_id": "sup-003", "reviewer_type": "supplier",
            "reviewee_id": "buyer-001", "reviewee_type": "buyer",
            "quality_score": None, "delivery_score": None,
            "communication_score": None, "quote_accuracy_score": None,
            "payment_score": 4, "spec_clarity_score": 4, "professionalism_score": 3,
            "overall_score": 3,
            "written_review": "Buyer paid on time but escalated dispute aggressively for a delay that was partially caused by ambiguous delivery window.",
            "is_dispute": 1, "dispute_resolution": "Issued €500 credit note.",
            "created_at": "2024-08-22T09%(00)s%(00Z)s"
        },
        # ord-004: Nordic Precision reviews sup-001
        {
            "id": "rev-006", "order_id": "ord-004",
            "reviewer_id": "buyer-002", "reviewer_type": "buyer",
            "reviewee_id": "sup-001", "reviewee_type": "supplier",
            "quality_score": 5, "delivery_score": 5,
            "communication_score": 5, "quote_accuracy_score": 5,
            "payment_score": None, "spec_clarity_score": None, "professionalism_score": None,
            "overall_score": 5,
            "written_review": "Class A PT100 sensors passed all our medical-grade incoming inspection. Zero defects. Preferred supplier status.",
            "is_dispute": 0, "dispute_resolution": None,
            "created_at": "2024-11-29T11%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO platform_reviews
        (id, order_id, reviewer_id, reviewer_type, reviewee_id, reviewee_type,
         quality_score, delivery_score, communication_score, quote_accuracy_score,
         payment_score, spec_clarity_score, professionalism_score,
         overall_score, written_review, is_dispute, dispute_resolution, created_at)
        VALUES (%(id)s, %(order_id)s, %(reviewer_id)s, %(reviewer_type)s, %(reviewee_id)s, %(reviewee_type)s,
                %(quality_score)s, %(delivery_score)s, %(communication_score)s, %(quote_accuracy_score)s,
                %(payment_score)s, %(spec_clarity_score)s, %(professionalism_score)s,
                %(overall_score)s, %(written_review)s, %(is_dispute)s, %(dispute_resolution)s, %(created_at)s)
    """, reviews)

    # ------------------------------------------------------------------
    # TABLE 10: trust_scores
    # ------------------------------------------------------------------
    trust_scores = [
        # sup-001 Berlin Electronics — high performer
        {
            "id": "ts-001", "entity_id": "sup-001", "entity_type": "supplier",
            "delivery_score": 0.97, "quality_score": 0.98,
            "communication_score": 0.93, "quote_accuracy_score": 0.96,
            "fulfillment_rate": 1.0, "supplier_dispute_rate": 0.0,
            "payment_score": None, "spec_clarity_score": None,
            "close_rate": None, "buyer_dispute_rate": None,
            "overall_score": 0.96, "total_transactions": 4,
            "score_confidence": "medium", "previous_score": 0.94,
            "score_trend": "rising", "last_calculated": "2024-11-29T12%(00)s%(00Z)s"
        },
        # sup-003 Chicago Industrial — poor delivery record
        {
            "id": "ts-002", "entity_id": "sup-003", "entity_type": "supplier",
            "delivery_score": 0.40, "quality_score": 0.80,
            "communication_score": 0.60, "quote_accuracy_score": 0.80,
            "fulfillment_rate": 0.90, "supplier_dispute_rate": 0.50,
            "payment_score": None, "spec_clarity_score": None,
            "close_rate": None, "buyer_dispute_rate": None,
            "overall_score": 0.64, "total_transactions": 1,
            "score_confidence": "low", "previous_score": 0.75,
            "score_trend": "falling", "last_calculated": "2024-08-21T12%(00)s%(00Z)s"
        },
        # sup-002 Tokyo Micro — no history yet, neutral
        {
            "id": "ts-003", "entity_id": "sup-002", "entity_type": "supplier",
            "delivery_score": None, "quality_score": None,
            "communication_score": None, "quote_accuracy_score": None,
            "fulfillment_rate": None, "supplier_dispute_rate": None,
            "payment_score": None, "spec_clarity_score": None,
            "close_rate": None, "buyer_dispute_rate": None,
            "overall_score": 0.50, "total_transactions": 0,
            "score_confidence": "low", "previous_score": None,
            "score_trend": "stable", "last_calculated": "2025-01-01T00%(00)s%(00Z)s"
        },
        # sup-004 Shenzhen — no history
        {
            "id": "ts-004", "entity_id": "sup-004", "entity_type": "supplier",
            "delivery_score": None, "quality_score": None,
            "communication_score": None, "quote_accuracy_score": None,
            "fulfillment_rate": None, "supplier_dispute_rate": None,
            "payment_score": None, "spec_clarity_score": None,
            "close_rate": None, "buyer_dispute_rate": None,
            "overall_score": 0.50, "total_transactions": 0,
            "score_confidence": "low", "previous_score": None,
            "score_trend": "stable", "last_calculated": "2025-01-01T00%(00)s%(00Z)s"
        },
        # sup-005 Rotterdam — no history
        {
            "id": "ts-005", "entity_id": "sup-005", "entity_type": "supplier",
            "delivery_score": None, "quality_score": None,
            "communication_score": None, "quote_accuracy_score": None,
            "fulfillment_rate": None, "supplier_dispute_rate": None,
            "payment_score": None, "spec_clarity_score": None,
            "close_rate": None, "buyer_dispute_rate": None,
            "overall_score": 0.50, "total_transactions": 0,
            "score_confidence": "low", "previous_score": None,
            "score_trend": "stable", "last_calculated": "2025-01-01T00%(00)s%(00Z)s"
        },
        # buyer-001 Volta Systems — strong buyer
        {
            "id": "ts-006", "entity_id": "buyer-001", "entity_type": "buyer",
            "delivery_score": None, "quality_score": None,
            "communication_score": None, "quote_accuracy_score": None,
            "fulfillment_rate": None, "supplier_dispute_rate": None,
            "payment_score": 0.97, "spec_clarity_score": 0.88,
            "close_rate": 0.80, "buyer_dispute_rate": 0.20,
            "overall_score": 0.87, "total_transactions": 5,
            "score_confidence": "medium", "previous_score": 0.91,
            "score_trend": "falling", "last_calculated": "2024-11-29T12%(00)s%(00Z)s"
        },
        # buyer-002 Nordic Precision — excellent buyer
        {
            "id": "ts-007", "entity_id": "buyer-002", "entity_type": "buyer",
            "delivery_score": None, "quality_score": None,
            "communication_score": None, "quote_accuracy_score": None,
            "fulfillment_rate": None, "supplier_dispute_rate": None,
            "payment_score": 1.0, "spec_clarity_score": 0.95,
            "close_rate": 0.90, "buyer_dispute_rate": 0.0,
            "overall_score": 0.95, "total_transactions": 2,
            "score_confidence": "low", "previous_score": 0.93,
            "score_trend": "rising", "last_calculated": "2024-11-29T12%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO trust_scores
        (id, entity_id, entity_type,
         delivery_score, quality_score, communication_score,
         quote_accuracy_score, fulfillment_rate, supplier_dispute_rate,
         payment_score, spec_clarity_score, close_rate, buyer_dispute_rate,
         overall_score, total_transactions, score_confidence,
         previous_score, score_trend, last_calculated)
        VALUES (%(id)s, %(entity_id)s, %(entity_type)s,
                %(delivery_score)s, %(quality_score)s, %(communication_score)s,
                %(quote_accuracy_score)s, %(fulfillment_rate)s, %(supplier_dispute_rate)s,
                %(payment_score)s, %(spec_clarity_score)s, %(close_rate)s, %(buyer_dispute_rate)s,
                %(overall_score)s, %(total_transactions)s, %(score_confidence)s,
                %(previous_score)s, %(score_trend)s, %(last_calculated)s)
    """, trust_scores)

    # ------------------------------------------------------------------
    # TABLE 11: supplier_buyer_relationship
    # ------------------------------------------------------------------
    relationships = [
        # buyer-001 <> sup-001 — strong established relationship
        {
            "id": "sbr-001",
            "supplier_id": "sup-001", "buyer_id": "buyer-001",
            "total_orders": 3, "total_value_eur": 1858.00,
            "first_order_date": "2024-07-01", "last_order_date": "2024-09-28",
            "avg_order_frequency_days": 45,
            "avg_negotiation_rounds": 3.33,
            "avg_discount_achieved": 4.6,
            "buyer_typical_payment_terms": "Net-15",
            "supplier_flexibility_score": 0.82,
            "hitl_frequency": 0,
            "supplier_on_time_rate": 1.0,
            "buyer_payment_on_time_rate": 1.0,
            "relationship_tier": "established",
            "dispute_count": 0, "last_dispute_date": None,
            "updated_at": "2024-10-14T16%(00)s%(00Z)s"
        },
        # buyer-001 <> sup-003 — at risk (dispute, late delivery)
        {
            "id": "sbr-002",
            "supplier_id": "sup-003", "buyer_id": "buyer-001",
            "total_orders": 1, "total_value_eur": 910.00,
            "first_order_date": "2024-07-20", "last_order_date": "2024-07-20",
            "avg_order_frequency_days": None,
            "avg_negotiation_rounds": 2.0,
            "avg_discount_achieved": 3.2,
            "buyer_typical_payment_terms": "Net-30",
            "supplier_flexibility_score": 0.55,
            "hitl_frequency": 0,
            "supplier_on_time_rate": 0.0,
            "buyer_payment_on_time_rate": 1.0,
            "relationship_tier": "at_risk",
            "dispute_count": 1, "last_dispute_date": "2024-08-16",
            "updated_at": "2024-08-21T10%(00)s%(00Z)s"
        },
        # buyer-002 <> sup-001 — developing
        {
            "id": "sbr-003",
            "supplier_id": "sup-001", "buyer_id": "buyer-002",
            "total_orders": 1, "total_value_eur": 2640.00,
            "first_order_date": "2024-11-01", "last_order_date": "2024-11-01",
            "avg_order_frequency_days": None,
            "avg_negotiation_rounds": 2.0,
            "avg_discount_achieved": 4.1,
            "buyer_typical_payment_terms": "Net-30",
            "supplier_flexibility_score": 0.70,
            "hitl_frequency": 0,
            "supplier_on_time_rate": 1.0,
            "buyer_payment_on_time_rate": 1.0,
            "relationship_tier": "developing",
            "dispute_count": 0, "last_dispute_date": None,
            "updated_at": "2024-11-29T12%(00)s%(00Z)s"
        }
    ]

    c.executemany("""
        INSERT INTO supplier_buyer_relationship
        (id, supplier_id, buyer_id, total_orders, total_value_eur,
         first_order_date, last_order_date, avg_order_frequency_days,
         avg_negotiation_rounds, avg_discount_achieved, buyer_typical_payment_terms,
         supplier_flexibility_score, hitl_frequency,
         supplier_on_time_rate, buyer_payment_on_time_rate,
         relationship_tier, dispute_count, last_dispute_date, updated_at)
        VALUES (%(id)s, %(supplier_id)s, %(buyer_id)s, %(total_orders)s, %(total_value_eur)s,
                %(first_order_date)s, %(last_order_date)s, %(avg_order_frequency_days)s,
                %(avg_negotiation_rounds)s, %(avg_discount_achieved)s, %(buyer_typical_payment_terms)s,
                %(supplier_flexibility_score)s, %(hitl_frequency)s,
                %(supplier_on_time_rate)s, %(buyer_payment_on_time_rate)s,
                %(relationship_tier)s, %(dispute_count)s, %(last_dispute_date)s, %(updated_at)s)
    """, relationships)

    conn.commit()
    conn.close()
    print("✅ All 11 tables seeded successfully.")
    print("\nSummary:")
    print("  buyers:                      3 rows")
    print("  suppliers:                   8 rows")
    print("  orders:                      5 rows (1 active for live agents)")
    print("  order_line_items:            5 rows (1 active)")
    print("  supplier_catalog:           13 rows")
    print("  negotiation_history:         8 rows (1 active round)")
    print("  macro_signals:               5 rows (2 critical, 3 monitoring)")
    print("  fulfillment_events:         16 rows (clean + late + dispute)")
    print("  platform_reviews:            6 rows (bilateral)")
    print("  trust_scores:                7 rows (suppliers + buyers)")
    print("  supplier_buyer_relationship: 3 rows")


if __name__ == "__main__":
    seed()