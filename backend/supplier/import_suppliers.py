#!/usr/bin/env python
"""
Import Suppliers from JSON
Load suppliers and products from suppliers.json into the database
"""

import json
import sys
from pathlib import Path
from supplier.supplier_registry import SupplierRegistry


def load_suppliers_from_json(json_file: str = "supplier/suppliers.json") -> dict:
    """Load suppliers from JSON file"""
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"❌ File not found: {json_file}")
        print(f"   Make sure you're in the project root directory")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return None


def import_suppliers(json_file: str = "supplier/suppliers.json", verbose: bool = True) -> dict:
    """
    Import suppliers and products from JSON file into database
    
    Args:
        json_file: Path to JSON file (default: suppliers.json)
        verbose: Print progress messages
    
    Returns:
        Summary of import operation
    """
    
    if verbose:
        print("\n" + "="*60)
        print("  SUPPLIER IMPORT FROM JSON")
        print("="*60 + "\n")
        print(f"Loading from: {json_file}\n")
    
    # Load JSON
    data = load_suppliers_from_json(json_file)
    if not data:
        return {"success": False, "error": "Failed to load JSON"}
    
    suppliers_data = data.get("suppliers", [])
    
    if not suppliers_data:
        print("❌ No suppliers found in JSON file")
        return {"success": False, "error": "No suppliers in JSON"}
    
    if verbose:
        print(f"Found {len(suppliers_data)} suppliers\n")
    
    # Import each supplier
    registered_count = 0
    product_count = 0
    failed_suppliers = []
    
    for supplier in suppliers_data:
        supplier_id = supplier.get("supplier_id")
        company_name = supplier.get("company_name")
        
        if not supplier_id or not company_name:
            print(f"⚠️  Skipping invalid supplier: {supplier}")
            continue
        
        # Register supplier
        try:
            result = SupplierRegistry.register_supplier(
                supplier_id=supplier_id,
                company_name=company_name,
                country=supplier.get("country", "Unknown"),
                region=supplier.get("region", "Unknown"),
                certifications=supplier.get("certifications", []),
                capabilities=[],  # Will be inferred from products
                contact_email=supplier.get("contact_email", ""),
                trust_score=supplier.get("trust_score", 0.5),
                negotiation_style=supplier.get("negotiation_style", "balanced")
            )
            
            if result.get("success"):
                registered_count += 1
                if verbose:
                    print(f"✓ {company_name} ({supplier.get('region', 'N/A')})")
            else:
                failed_suppliers.append(supplier_id)
                if verbose:
                    print(f"✗ {company_name}: {result.get('error')}")
                continue
        
        except Exception as e:
            failed_suppliers.append(supplier_id)
            if verbose:
                print(f"✗ {company_name}: {str(e)}")
            continue
        
        # Add products to supplier
        products = supplier.get("products", [])
        
        if verbose and products:
            print(f"  Products:")
        
        for product in products:
            try:
                result = SupplierRegistry.add_product_to_supplier(
                    supplier_id=supplier_id,
                    product_id=product.get("product_id"),
                    product_name=product.get("product_name"),
                    category=product.get("category"),
                    unit_price=product.get("unit_price", 0),
                    stock_quantity=product.get("stock_quantity", 0),
                    lead_time_days=product.get("lead_time_days", 7),
                    certifications_required=product.get("certifications_required", [])
                )
                
                if result.get("success"):
                    product_count += 1
                    if verbose:
                        print(f"    + {product.get('product_name')} (€{product.get('unit_price')})")
            
            except Exception as e:
                if verbose:
                    print(f"    ✗ Failed to add product: {str(e)}")
                continue
        
        if verbose:
            print()
    
    # Summary
    if verbose:
        print("="*60)
        print("  IMPORT SUMMARY")
        print("="*60)
        print(f"✓ Suppliers registered: {registered_count}/{len(suppliers_data)}")
        print(f"✓ Products added: {product_count}")
        if failed_suppliers:
            print(f"⚠️  Failed suppliers: {len(failed_suppliers)}")
            for sid in failed_suppliers:
                print(f"   - {sid}")
        print()
    
    return {
        "success": len(failed_suppliers) == 0,
        "suppliers_registered": registered_count,
        "products_added": product_count,
        "failed_suppliers": failed_suppliers
    }


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Import suppliers from JSON file"
    )
    parser.add_argument(
        "--file",
        default="supplier/suppliers.json",
        help="Path to suppliers JSON file (default: supplier/suppliers.json)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output messages"
    )
    
    args = parser.parse_args()
    
    # Run import
    result = import_suppliers(
        json_file=args.file,
        verbose=not args.quiet
    )
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
