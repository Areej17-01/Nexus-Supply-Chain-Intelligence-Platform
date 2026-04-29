#!/usr/bin/env python
"""
Quick Start & Testing Script for NEXUS Supplier Agents
Run this to test the supplier agent system end-to-end
"""

import requests
import json
from typing import Dict, List
import time


BASE_URL = "http://localhost:8010"


class SupplierAgentTester:
    """Test suite for supplier agent system"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    
    def test_health_check(self) -> bool:
        """Test that the platform is running"""
        self.print_section("1. HEALTH CHECK")
        
        try:
            response = requests.get(f"{self.base_url}/api/health")
            data = response.json()
            
            if response.status_code == 200:
                print(f"✓ Platform is healthy")
                print(f"  Status: {data['status']}")
                print(f"  Platform: {data['platform']}")
                return True
            else:
                print(f"✗ Platform returned status {response.status_code}")
                return False
        
        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            print(f"  Make sure the server is running: python main.py")
            return False
    
    def test_list_suppliers(self) -> List[Dict]:
        """Test listing all suppliers"""
        self.print_section("2. LIST SUPPLIERS")
        
        try:
            response = requests.get(f"{self.base_url}/api/suppliers")
            data = response.json()
            
            print(f"✓ Found {data['suppliers_found']} suppliers\n")
            
            for i, supplier in enumerate(data['suppliers'][:5], 1):
                print(f"{i}. {supplier['company_name']}")
                print(f"   Region: {supplier['region']} ({supplier['country']})")
                print(f"   Trust Score: {supplier['trust_score']}")
                print(f"   Certifications: {', '.join(supplier['certifications'])}\n")
            
            return data['suppliers']
        
        except Exception as e:
            print(f"✗ Error: {e}")
            return []
    
    def test_filter_suppliers(self) -> List[Dict]:
        """Test filtering suppliers by region and capability"""
        self.print_section("3. FILTER SUPPLIERS BY REGION")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/suppliers",
                params={"region": "EU", "capability": "temperature_sensors"}
            )
            data = response.json()
            
            print(f"✓ Found {data['suppliers_found']} EU suppliers with temperature sensors\n")
            
            for supplier in data['suppliers']:
                print(f"• {supplier['company_name']} (Trust: {supplier['trust_score']})")
            
            return data['suppliers']
        
        except Exception as e:
            print(f"✗ Error: {e}")
            return []
    
    def test_get_supplier_details(self, supplier_id: str) -> Dict:
        """Test getting detailed supplier information"""
        self.print_section(f"4. GET SUPPLIER DETAILS: {supplier_id}")
        
        try:
            response = requests.get(f"{self.base_url}/api/suppliers/{supplier_id}")
            data = response.json()
            
            print(f"✓ Supplier details retrieved\n")
            print(f"Company: {data['company_name']}")
            print(f"Region: {data['region']} ({data['country']})")
            print(f"Certifications: {', '.join(data['certifications'])}")
            print(f"Trust Score: {data['trust_score']}")
            print(f"Contact: {data['contact_email']}")
            
            return data
        
        except Exception as e:
            print(f"✗ Error: {e}")
            return {}
    
    def test_send_rfq(self, supplier_id: str = None) -> Dict:
        """Test sending an RFQ to suppliers"""
        self.print_section("5. SEND REQUEST FOR QUOTE (RFQ)")
        
        rfq_data = {
            "buyer_id": "buyer-test-001",
            "items": [
                {"product_id": "prod-001", "quantity": 500},
                {"product_id": "prod-002", "quantity": 100}
            ],
            "delivery_region": "EU",
            "deadline_days": 10,
            "required_certifications": ["CE", "ISO9001"],
            "negotiation_style": "balanced"
        }
        
        print(f"RFQ Details:")
        print(f"  Buyer: {rfq_data['buyer_id']}")
        print(f"  Items: {len(rfq_data['items'])} line items")
        print(f"  Delivery: {rfq_data['delivery_region']} ({rfq_data['deadline_days']} days)")
        print(f"  Required Certs: {', '.join(rfq_data['required_certifications'])}\n")
        
        try:
            print("Sending RFQ to suppliers...")
            response = requests.post(
                f"{self.base_url}/api/rfq",
                json=rfq_data
            )
            
            data = response.json()
            
            if response.status_code == 200:
                print(f"✓ RFQ successful\n")
                print(f"Status: {data['status']}")
                print(f"Suppliers Contacted: {data['suppliers_contacted']}")
                print(f"Quotes Received: {data['quotes_received']}\n")
                
                # Display quotes
                if 'quotes' in data and data['quotes']:
                    print("Quote Results:")
                    for i, quote in enumerate(data['quotes'], 1):
                        print(f"\n{i}. {quote['supplier_name']}")
                        print(f"   Supplier ID: {quote['supplier_id']}")
                        print(f"   Trust Score: {quote['supplier_trust_score']}")
                        
                        if 'quote' in quote:
                            if isinstance(quote['quote'], dict):
                                if 'subtotal' in quote['quote']:
                                    print(f"   Total: €{quote['quote']['subtotal']:.2f}")
                                    print(f"   Terms: {quote['quote'].get('payment_terms', 'N/A')}")
                
                return data
            else:
                print(f"✗ Error: {response.status_code}")
                print(f"  {data}")
                return {}
        
        except Exception as e:
            print(f"✗ Error sending RFQ: {e}")
            return {}
    
    def test_direct_quote(self, supplier_id: str) -> Dict:
        """Test getting a direct quote from a specific supplier"""
        self.print_section(f"6. GET DIRECT QUOTE FROM SUPPLIER: {supplier_id}")
        
        rfq_data = {
            "buyer_id": "buyer-test-002",
            "items": [
                {"product_id": "prod-001", "quantity": 500}
            ],
            "delivery_region": "EU",
            "deadline_days": 10,
            "required_certifications": ["CE"],
            "negotiation_style": "balanced"
        }
        
        try:
            print(f"Requesting quote from {supplier_id}...")
            response = requests.post(
                f"{self.base_url}/api/suppliers/{supplier_id}/quote",
                json=rfq_data
            )
            
            data = response.json()
            
            if response.status_code == 200:
                print(f"✓ Direct quote received\n")
                print(f"Quote ID: {data.get('quote_id', 'N/A')}")
                print(f"Supplier: {data.get('supplier_name', 'N/A')}")
                
                if 'quote' in data:
                    quote = data['quote']
                    if isinstance(quote, dict):
                        print(f"Total: €{quote.get('subtotal', 0):.2f}")
                        print(f"Payment Terms: {quote.get('payment_terms', 'N/A')}")
                        print(f"Valid Until: {quote.get('valid_until', 'N/A')}")
                
                return data
            else:
                print(f"✗ Error: {response.status_code}")
                return {}
        
        except Exception as e:
            print(f"✗ Error: {e}")
            return {}
    
    def test_register_supplier(self) -> Dict:
        """Test registering a new supplier"""
        self.print_section("7. REGISTER NEW SUPPLIER")
        
        new_supplier = {
            "supplier_id": "supplier-test-001",
            "company_name": "Test Electronics Ltd",
            "country": "Portugal",
            "region": "EU",
            "certifications": ["CE", "ISO9001", "RoHS"],
            "contact_email": "sales@testelectronics.pt",
            "trust_score": 0.80,
            "negotiation_style": "balanced"
        }
        
        print(f"Registering: {new_supplier['company_name']}")
        print(f"Region: {new_supplier['region']}")
        print(f"Certs: {', '.join(new_supplier['certifications'])}\n")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/suppliers/register",
                json=new_supplier
            )
            
            data = response.json()
            
            if data.get('success'):
                print(f"✓ Supplier registered successfully")
                print(f"  ID: {data['supplier_id']}")
                return data
            else:
                print(f"✗ Registration failed: {data.get('error')}")
                return {}
        
        except Exception as e:
            print(f"✗ Error: {e}")
            return {}
    
    def run_full_test(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("  NEXUS SUPPLIER AGENT SYSTEM - FULL TEST SUITE")
        print("="*60)
        
        # Test 1: Health check
        if not self.test_health_check():
            print("\n❌ Server is not running. Start it with: python main.py")
            return
        
        time.sleep(0.5)
        
        # Test 2: List all suppliers
        suppliers = self.test_list_suppliers()
        time.sleep(0.5)
        
        # Test 3: Filter suppliers
        filtered = self.test_filter_suppliers()
        time.sleep(0.5)
        
        # Test 4: Get supplier details
        if suppliers:
            self.test_get_supplier_details(suppliers[0]['supplier_id'])
            time.sleep(0.5)
        
        # Test 5: Send RFQ
        rfq_result = self.test_send_rfq()
        time.sleep(1)
        
        # Test 6: Direct quote
        if suppliers:
            self.test_direct_quote(suppliers[0]['supplier_id'])
            time.sleep(0.5)
        
        # Test 7: Register new supplier
        self.test_register_supplier()
        
        # Summary
        self.print_section("✅ TEST SUITE COMPLETE")
        print("All tests finished! Check the results above.\n")


def main():
    """Main entry point"""
    print("\n🚀 NEXUS Supplier Agent Testing Suite\n")
    
    tester = SupplierAgentTester()
    
    try:
        tester.run_full_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
