"""
RAGAS Evaluation Test Dataset
Contains sample documents, queries, and ground truth answers for benchmarking.
"""

# Sample documents (simulating PDFs indexed in Qdrant)
DOCUMENTS = [
    {
        "id": 1,
        "name": "supplier_contract.pdf",
        "content": """
        SUPPLIER SERVICE AGREEMENT
        
        Payment Terms: Net 30 days from invoice date. Late payments incur 1.5% monthly interest.
        Delivery: Standard delivery within 5-7 business days. Expedited delivery available for 15% surcharge.
        Quality Guarantee: All products guaranteed defect-free for 12 months from delivery.
        Minimum Order: Minimum order quantity is 100 units per order.
        Discount Schedule: 5% discount for orders 500-999 units, 10% for 1000+ units.
        Cancellation Policy: Orders can be cancelled within 24 hours of placement for full refund.
        """
    },
    {
        "id": 2,
        "name": "company_policy.pdf",
        "content": """
        COMPANY EXPENSE POLICY
        
        Travel Reimbursement:
        - Flights: Economy class only, approval required for first class
        - Hotels: Maximum $150/night for domestic, $200/night for international
        - Meals: Up to $50/day, with receipts required
        - Ground Transportation: Uber/taxi acceptable, personal vehicle at 0.58/mile
        
        Procurement Rules:
        - Purchases under $500: Team lead approval only
        - Purchases $500-$5000: Department manager approval required
        - Purchases over $5000: CFO approval and board notification required
        - All purchases require competitive quotes for amounts over $1000
        
        Report Deadline: All expense reports must be submitted within 30 days of purchase.
        """
    },
    {
        "id": 3,
        "name": "customer_data.pdf",
        "content": """
        Q2 2024 CUSTOMER ANALYTICS REPORT
        
        Customer Satisfaction: 87% of customers reported satisfaction with our services.
        Net Promoter Score: NPS improved from 42 to 58 compared to Q1.
        
        Product Performance:
        - Product A: 12,450 units sold, 94% quality rating
        - Product B: 8,920 units sold, 89% quality rating
        - Product C: 5,670 units sold, 91% quality rating
        
        Revenue Breakdown:
        - North America: 45% of revenue ($2.1M)
        - Europe: 30% of revenue ($1.4M)
        - Asia-Pacific: 25% of revenue ($1.15M)
        
        Top Customers:
        1. Acme Corp: $450,000 annual spend
        2. TechVision Ltd: $320,000 annual spend
        3. Global Supplies Inc: $280,000 annual spend
        """
    },
    {
        "id": 4,
        "name": "product_spec.pdf",
        "content": """
        PRODUCT SPECIFICATION: XR-2000 Advanced Widget
        
        Technical Specifications:
        - Dimensions: 250mm x 150mm x 80mm
        - Weight: 2.5kg
        - Power: 120W max consumption, 220V input
        - Operating Temperature: -10°C to 50°C
        - Storage Temperature: -20°C to 60°C
        
        Features:
        - 24-hour operation capability
        - Built-in diagnostic sensors
        - Wireless connectivity (Bluetooth 5.0, WiFi 6)
        - Emergency shutdown system
        - Noise level: 65dB at full operation
        
        Warranty: 24-month full replacement warranty, parts only after 24 months.
        Support: 24/7 phone support available, email response within 4 hours.
        """
    }
]

# Evaluation queries with ground truth answers
EVALUATION_SET = [
    {
        "query": "What are the payment terms in our supplier contract?",
        "ground_truth": "Net 30 days from invoice date. Late payments incur 1.5% monthly interest.",
        "document_id": 1,
        "type": "factual"
    },
    {
        "query": "What is the hotel reimbursement limit for international travel?",
        "ground_truth": "The maximum hotel reimbursement is $200 per night for international travel.",
        "document_id": 2,
        "type": "factual"
    },
    {
        "query": "How much approval is needed for a $2,000 purchase?",
        "ground_truth": "Purchases between $500-$5000 require department manager approval. Additionally, competitive quotes are required for amounts over $1000.",
        "document_id": 2,
        "type": "procedural"
    },
    {
        "query": "What was our customer satisfaction rate in Q2 2024?",
        "ground_truth": "87% of customers reported satisfaction with our services.",
        "document_id": 3,
        "type": "factual"
    },
    {
        "query": "Which region generated the most revenue?",
        "ground_truth": "North America generated 45% of revenue ($2.1M), making it the highest revenue region.",
        "document_id": 3,
        "type": "analytical"
    },
    {
        "query": "What is the operating temperature range for the XR-2000 widget?",
        "ground_truth": "The XR-2000 operating temperature range is -10°C to 50°C.",
        "document_id": 4,
        "type": "factual"
    },
    {
        "query": "What connectivity options does the XR-2000 have?",
        "ground_truth": "The XR-2000 has Bluetooth 5.0 and WiFi 6 wireless connectivity.",
        "document_id": 4,
        "type": "factual"
    },
    {
        "query": "What is the minimum order quantity for our supplier?",
        "ground_truth": "The minimum order quantity is 100 units per order.",
        "document_id": 1,
        "type": "factual"
    },
    {
        "query": "Is there a discount for large orders?",
        "ground_truth": "Yes, there is a 5% discount for orders of 500-999 units, and 10% discount for orders of 1000 or more units.",
        "document_id": 1,
        "type": "factual"
    },
    {
        "query": "What are the top 3 customers by annual spending?",
        "ground_truth": "1. Acme Corp ($450,000), 2. TechVision Ltd ($320,000), 3. Global Supplies Inc ($280,000)",
        "document_id": 3,
        "type": "ranking"
    }
]

# Simulated document chunks (what would be retrieved from Qdrant)
CHUNKS = [
    {"document_id": 1, "text": "Payment Terms: Net 30 days from invoice date. Late payments incur 1.5% monthly interest.", "score": 0.95},
    {"document_id": 1, "text": "Delivery: Standard delivery within 5-7 business days. Expedited delivery available for 15% surcharge.", "score": 0.92},
    {"document_id": 1, "text": "Minimum Order: Minimum order quantity is 100 units per order.", "score": 0.94},
    {"document_id": 1, "text": "Discount Schedule: 5% discount for orders 500-999 units, 10% for 1000+ units.", "score": 0.93},
    {"document_id": 2, "text": "Hotels: Maximum $150/night for domestic, $200/night for international", "score": 0.96},
    {"document_id": 2, "text": "Purchases $500-$5000: Department manager approval required", "score": 0.91},
    {"document_id": 2, "text": "All purchases require competitive quotes for amounts over $1000", "score": 0.88},
    {"document_id": 3, "text": "Customer Satisfaction: 87% of customers reported satisfaction with our services.", "score": 0.97},
    {"document_id": 3, "text": "North America: 45% of revenue ($2.1M)", "score": 0.94},
    {"document_id": 3, "text": "Top Customers: 1. Acme Corp: $450,000 annual spend, 2. TechVision Ltd: $320,000 annual spend, 3. Global Supplies Inc: $280,000 annual spend", "score": 0.92},
    {"document_id": 4, "text": "Operating Temperature: -10°C to 50°C", "score": 0.98},
    {"document_id": 4, "text": "Wireless connectivity (Bluetooth 5.0, WiFi 6)", "score": 0.95},
]
