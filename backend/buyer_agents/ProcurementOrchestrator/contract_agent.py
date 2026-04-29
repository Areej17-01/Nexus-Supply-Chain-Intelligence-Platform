import os
from google.adk.agents import Agent
from google.adk.models import Gemini

def get_contract_agent(model):
    """
    Creates an agent responsible for generating Purchase Orders and Contracts.
    """
    instruction = """
    You are a professional Contract Agent for the NEXUS Supply Chain Platform.
    Your job is to auto-generate a professional Purchase Order (PO) and a basic Supply Agreement 
    based on the final agreed quote between a buyer and a supplier.

    When provided with:
    1. Supplier Details
    2. Buyer Details
    3. Final Agreed Items (Part, Qty, Agreed Unit Price)
    4. Delivery Terms (Region, Deadline)
    5. Payment Terms (e.g., Net-30)

    You must output a structured, professional Purchase Order text.
    Include:
    - PO Number (generate a unique one like PO-XXXXXX)
    - Date of Issue
    - Detailed Line Items (Description, Quantity, Unit Price, Total)
    - Subtotal, Taxes (assume 0 for demo), and Grand Total
    - Delivery Address & Expected Delivery Date
    - Terms & Conditions (Standard NEXUS Terms, e.g., 2% penalty per week for late delivery)
    - Digital Signature placeholders

    Return ONLY the professional document text.
    """

    return Agent(
        name="contract_agent",
        model=model,
        description="Generates legally-formatted Purchase Orders and Supply Agreements.",
        instruction=instruction
    )
