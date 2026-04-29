import sqlite3
from nexus.core.config import SQLITE_DB_PATH

def seed_nexus_data():
    print("Seeding NEXUS Supply Chain Platform data...")
    
    # Use the database defined in config
    db_path = SQLITE_DB_PATH
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create tables if they don't exist
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id TEXT PRIMARY KEY,
        company_name TEXT,
        country TEXT,
        region TEXT,
        certifications TEXT,
        contact_email TEXT,
        api_endpoint TEXT,
        trust_score REAL DEFAULT 0.5,
        negotiation_style TEXT DEFAULT 'balanced',
        is_active INTEGER DEFAULT 1,
        registered_at TEXT,
        updated_at TEXT
    );
    
    CREATE TABLE IF NOT EXISTS supplier_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id TEXT,
        product_id TEXT,
        product_name TEXT,
        category TEXT,
        unit_price REAL,
        stock_quantity INTEGER,
        lead_time_days INTEGER,
        certifications_required TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
    );
    
    CREATE TABLE IF NOT EXISTS trust_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id TEXT,
        entity_type TEXT,
        overall_score REAL,
        delivery_score REAL,
        quality_score REAL,
        supplier_dispute_rate REAL
    );

    CREATE TABLE IF NOT EXISTS negotiation_sessions (
        id TEXT PRIMARY KEY,
        supplier_id TEXT,
        buyer_id TEXT,
        status TEXT,
        initial_price REAL,
        final_price REAL,
        savings_pct REAL,
        reward REAL,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS negotiation_rounds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        round_no INTEGER,
        speaker TEXT,
        label TEXT,
        message TEXT,
        offer REAL,
        created_at TEXT,
        FOREIGN KEY (session_id) REFERENCES negotiation_sessions(id)
    );

    CREATE TABLE IF NOT EXISTS negotiation_policy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id TEXT,
        last_reward REAL,
        last_savings_pct REAL,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS purchase_orders (
        id TEXT PRIMARY KEY,
        supplier_id TEXT,
        buyer_id TEXT,
        total_amount REAL,
        currency TEXT,
        status TEXT,
        document_text TEXT,
        created_at TEXT
    );
    """)

    # 1. Seed Suppliers
    suppliers = [
        ('sup-001', 'Berlin Electronics GmbH', 'Germany', 'EU', '["CE", "ISO9001", "RoHS"]', 'sales@berlin-elec.de', None, 0.94, 'balanced', 1, '2026-01-01T10:00:00Z'),
        ('sup-002', 'Shenzhen Precision Parts', 'China', 'Asia', '["RoHS", "REACH"]', 'export@szprecision.cn', None, 0.82, 'aggressive', 1, '2026-01-05T12:00:00Z'),
        ('sup-003', 'Chicago Industrial Supply', 'USA', 'US', '["UL", "ITAR", "ISO14001"]', 'quotes@chicago-ind.com', None, 0.88, 'quality_first', 1, '2026-02-10T09:00:00Z'),
        ('sup-004', 'Tokyo Micro Components', 'Japan', 'Asia', '["CE", "ISO9001", "JIS"]', 'contact@tokyo-micro.jp', None, 0.97, 'balanced', 1, '2026-03-15T08:30:00Z'),
        ('sup-005', 'Rotterdam Logistics & Parts', 'Netherlands', 'EU', '["CE", "ISO28000"]', 'info@rotterdam-log.nl', None, 0.85, 'balanced', 1, '2026-04-01T11:00:00Z'),
        ('sup-006', 'Paris SensorWorks', 'France', 'EU', '["CE", "ISO9001"]', 'sales@paris-sensorworks.fr', None, 0.91, 'balanced', 1, '2026-04-05T09:00:00Z'),
        ('sup-007', 'Madrid Robotics Parts', 'Spain', 'EU', '["CE", "RoHS"]', 'quotes@madrid-robotics.es', None, 0.79, 'aggressive', 1, '2026-04-06T10:15:00Z'),
        ('sup-008', 'Warsaw PCB Foundry', 'Poland', 'EU', '["CE", "ISO9001", "RoHS"]', 'sales@warsaw-pcb.pl', None, 0.83, 'balanced', 1, '2026-04-07T08:40:00Z'),
        ('sup-009', 'Helsinki Embedded Systems', 'Finland', 'EU', '["CE", "ISO27001"]', 'contact@helsinki-embedded.fi', None, 0.87, 'quality_first', 1, '2026-04-08T13:05:00Z'),
        ('sup-010', 'Seoul Optics & LiDAR', 'South Korea', 'Asia', '["KC", "ISO9001"]', 'sales@seoul-optics.kr', None, 0.90, 'balanced', 1, '2026-04-09T07:20:00Z'),
        ('sup-011', 'Bangalore Microcontrollers', 'India', 'Asia', '["BIS", "ISO9001"]', 'quotes@blr-mcu.in', None, 0.80, 'aggressive', 1, '2026-04-10T11:30:00Z'),
        ('sup-012', 'Singapore Rapid Logistics', 'Singapore', 'Asia', '["ISO28000", "CE"]', 'ops@sg-rapidlog.sg', None, 0.86, 'balanced', 1, '2026-04-11T14:10:00Z'),
        ('sup-013', 'Austin Motion Systems', 'USA', 'US', '["UL", "ISO9001"]', 'sales@austin-motion.us', None, 0.89, 'balanced', 1, '2026-04-12T09:55:00Z'),
        ('sup-014', 'Toronto Sensor Labs', 'Canada', 'US', '["UL", "ISO13485"]', 'contact@toronto-sensor.ca', None, 0.84, 'quality_first', 1, '2026-04-13T16:45:00Z'),
        ('sup-015', 'Mexico City Electronics', 'Mexico', 'US', '["UL", "RoHS"]', 'quotes@mexcity-elec.mx', None, 0.76, 'aggressive', 1, '2026-04-14T12:00:00Z')
    ]
    
    cur.executemany("INSERT OR REPLACE INTO suppliers (id, company_name, country, region, certifications, contact_email, api_endpoint, trust_score, negotiation_style, is_active, registered_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)", suppliers)
    cur.execute("DELETE FROM supplier_products")
    cur.execute("DELETE FROM trust_scores")

    # 2. Seed Catalog
    catalog = [
        ('sup-001', 'prod-101', 'High-Precision Temp Sensor', 'temperature_sensors', 12.50, 5000, 5, '[]'),
        ('sup-001', 'prod-102', 'Standard Temp Probe', 'temperature_sensors', 8.20, 12000, 3, '[]'),
        ('sup-001', 'prod-111', 'EU LiDAR Module', 'lidar', 78.00, 420, 8, '["CE"]'),
        ('sup-001', 'prod-112', 'BLDC Motor 2208', 'actuators', 19.50, 850, 7, '["CE"]'),
        ('sup-001', 'prod-113', 'Industrial PCB Controller', 'pcb_boards', 14.20, 2500, 6, '["CE", "RoHS"]'),

        ('sup-002', 'prod-201', 'Miniature Temp Sensor', 'temperature_sensors', 5.40, 50000, 10, '[]'),
        ('sup-002', 'prod-211', 'Compact LiDAR Rangefinder', 'lidar', 52.00, 1500, 12, '["RoHS"]'),
        ('sup-002', 'prod-212', 'Brushless Motor Economy', 'actuators', 11.80, 12000, 14, '["RoHS"]'),
        ('sup-002', 'prod-213', 'PCB Assembly Standard', 'pcb_boards', 6.40, 30000, 11, '["RoHS", "REACH"]'),

        ('sup-003', 'prod-301', 'Aerospace Grade RTD', 'temperature_sensors', 145.00, 200, 20, '["ITAR"]'),
        ('sup-003', 'prod-311', 'ITAR LiDAR Sensor Pack', 'lidar', 210.00, 120, 18, '["ITAR", "UL"]'),
        ('sup-003', 'prod-312', 'Rugged Industrial Motor', 'actuators', 35.00, 900, 9, '["UL"]'),

        ('sup-004', 'prod-401', 'Industrial Thermistor', 'temperature_sensors', 3.10, 100000, 7, '[]'),
        ('sup-004', 'prod-411', 'Precision Micro LiDAR', 'lidar', 66.00, 2200, 10, '["CE", "JIS"]'),
        ('sup-004', 'prod-412', 'Micro Servo Actuator', 'actuators', 15.30, 6000, 8, '["CE"]'),
        ('sup-004', 'prod-413', 'Embedded MCU Board', 'microcontrollers', 9.75, 15000, 6, '["CE"]'),

        ('sup-005', 'prod-501', 'Rugged Temp Sensor', 'temperature_sensors', 18.75, 1500, 4, '[]'),
        ('sup-005', 'prod-511', 'Logistics-Ready Sensor Kit', 'lidar', 88.50, 350, 5, '["CE", "ISO28000"]'),
        ('sup-005', 'prod-512', 'EU PCB Prototype Batch', 'pcb_boards', 12.10, 5000, 5, '["CE", "ISO28000"]'),

        ('sup-006', 'prod-601', 'Precision NTC Sensor', 'temperature_sensors', 9.90, 22000, 4, '[]'),
        ('sup-006', 'prod-611', 'EU Control PCB v3', 'pcb_boards', 10.80, 8000, 6, '["CE"]'),
        ('sup-006', 'prod-612', 'Compact MCU Board', 'microcontrollers', 8.60, 12000, 7, '["CE"]'),

        ('sup-007', 'prod-701', 'Robot Joint Servo', 'actuators', 17.40, 3200, 9, '["CE"]'),
        ('sup-007', 'prod-702', 'Economy Temp Sensor', 'temperature_sensors', 6.10, 40000, 8, '[]'),

        ('sup-008', 'prod-801', '4-Layer PCB Batch', 'pcb_boards', 7.95, 25000, 10, '["RoHS"]'),
        ('sup-008', 'prod-802', '6-Layer PCB High-Speed', 'pcb_boards', 11.75, 12000, 12, '["CE", "RoHS"]'),
        ('sup-008', 'prod-803', 'Embedded MCU Board EU', 'microcontrollers', 10.20, 9000, 9, '["CE"]'),

        ('sup-009', 'prod-901', 'Secure IoT MCU Module', 'microcontrollers', 12.40, 6000, 8, '["CE"]'),
        ('sup-009', 'prod-902', 'Low-Drift Temp Sensor', 'temperature_sensors', 13.20, 5000, 6, '[]'),

        ('sup-010', 'prod-1001', 'Solid-State LiDAR Mini', 'lidar', 72.50, 900, 11, '["KC"]'),
        ('sup-010', 'prod-1002', 'Optics-Calibrated Temp Probe', 'temperature_sensors', 10.60, 16000, 7, '[]'),

        ('sup-011', 'prod-1101', 'MCU Board APAC', 'microcontrollers', 7.90, 25000, 9, '[]'),
        ('sup-011', 'prod-1111', 'PCB Assembly Economy', 'pcb_boards', 5.95, 50000, 13, '[]'),

        ('sup-012', 'prod-1201', 'LiDAR Sensor Kit (Logistics)', 'lidar', 95.00, 500, 6, '["ISO28000"]'),
        ('sup-012', 'prod-1211', 'PCB Prototype Express', 'pcb_boards', 15.50, 3000, 5, '["CE"]'),

        ('sup-013', 'prod-1301', 'High-Torque BLDC Motor', 'actuators', 28.90, 1400, 8, '["UL"]'),
        ('sup-013', 'prod-1311', 'US LiDAR Module', 'lidar', 84.00, 600, 10, '["UL"]'),

        ('sup-014', 'prod-1401', 'Medical-Grade Temp Sensor', 'temperature_sensors', 22.40, 4500, 7, '["UL"]'),
        ('sup-014', 'prod-1411', 'MCU Board (QA Focus)', 'microcontrollers', 13.80, 7000, 8, '["UL"]'),

        ('sup-015', 'prod-1501', 'Temp Sensor Standard NA', 'temperature_sensors', 7.10, 30000, 9, '[]'),
        ('sup-015', 'prod-1511', 'PCB Assembly NA', 'pcb_boards', 6.85, 28000, 12, '["RoHS"]')
    ]
    
    cur.executemany("""
        INSERT OR REPLACE INTO supplier_products (supplier_id, product_id, product_name, category, unit_price, stock_quantity, lead_time_days, certifications_required) 
        VALUES (?,?,?,?,?,?,?,?)
    """, catalog)

    # 3. Seed Trust Scores
    trust_scores = [
        ('sup-001', 'supplier', 0.94, 0.96, 0.92, 0.01),
        ('sup-002', 'supplier', 0.82, 0.78, 0.85, 0.05),
        ('sup-003', 'supplier', 0.88, 0.85, 0.95, 0.02),
        ('sup-004', 'supplier', 0.97, 0.98, 0.99, 0.00),
        ('sup-005', 'supplier', 0.85, 0.92, 0.80, 0.04),
        ('sup-006', 'supplier', 0.91, 0.93, 0.90, 0.02),
        ('sup-007', 'supplier', 0.79, 0.77, 0.81, 0.06),
        ('sup-008', 'supplier', 0.83, 0.84, 0.82, 0.04),
        ('sup-009', 'supplier', 0.87, 0.88, 0.92, 0.02),
        ('sup-010', 'supplier', 0.90, 0.89, 0.91, 0.02),
        ('sup-011', 'supplier', 0.80, 0.78, 0.80, 0.05),
        ('sup-012', 'supplier', 0.86, 0.90, 0.83, 0.03),
        ('sup-013', 'supplier', 0.89, 0.88, 0.87, 0.02),
        ('sup-014', 'supplier', 0.84, 0.86, 0.93, 0.02),
        ('sup-015', 'supplier', 0.76, 0.74, 0.78, 0.07)
    ]
    
    cur.executemany("""
        INSERT INTO trust_scores (entity_id, entity_type, overall_score, delivery_score, quality_score, supplier_dispute_rate) 
        VALUES (?,?,?,?,?,?)
    """, trust_scores)

    conn.commit()
    conn.close()
    print("NEXUS Data Seeded Successfully.")

if __name__ == "__main__":
    seed_nexus_data()
