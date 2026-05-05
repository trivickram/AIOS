"""
Mock Flask Servers for AIOS Middleware Demo

This module provides two Flask servers with different data structures:
- Source Server: Legacy customer data format
- Destination Server: Modernized user data format
"""

from flask import Flask, request, jsonify
from threading import Thread
import time

# =============================================================================
# SOURCE SERVER (Legacy Customer Data)
# =============================================================================

source_app = Flask("source_server")

@source_app.after_request
def add_source_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

# Mock legacy customer database
LEGACY_CUSTOMERS = [
    {
        "customer_id": "CUST001",
        "first_name": "John",
        "last_name": "Doe",
        "contact_num": "555-0123",
        "email_addr": "john.doe@example.com",
        "join_date": "2020-01-15",
        "status_code": "A"
    },
    {
        "customer_id": "CUST002",
        "first_name": "Jane",
        "last_name": "Smith",
        "contact_num": "555-0456",
        "email_addr": "jane.smith@example.com",
        "join_date": "2021-03-22",
        "status_code": "A"
    },
    {
        "customer_id": "CUST003",
        "first_name": "Bob",
        "last_name": "Johnson",
        "contact_num": "555-0789",
        "email_addr": "bob.j@example.com",
        "join_date": "2019-11-05",
        "status_code": "I"
    }
]

@source_app.route('/api/source', methods=['GET'])
def get_source_data():
    """
    Endpoint A: Returns legacy customer data

    Returns:
        JSON response with legacy data structure containing:
        - customer_id: Legacy customer identifier
        - first_name: Customer first name
        - last_name: Customer last name
        - contact_num: Phone number in format XXX-XXXX
        - email_addr: Email address
        - join_date: Date customer joined
        - status_code: Single letter status code (A=Active, I=Inactive)
    """
    print("📤 [SOURCE SERVER] Received GET request to /api/source")

    # Simulate some processing delay
    time.sleep(0.1)

    response = {
        "status": "success",
        "data_format": "legacy_v1",
        "customers": LEGACY_CUSTOMERS,
        "total_count": len(LEGACY_CUSTOMERS)
    }

    print(f"📤 [SOURCE SERVER] Returning {len(LEGACY_CUSTOMERS)} customer records")
    return jsonify(response), 200

@source_app.route('/api/source/add', methods=['POST'])
def add_source_data():
    """Append custom legacy customers at runtime."""
    print("📥 [SOURCE SERVER] Received POST request to /api/source/add")

    if not request.is_json:
        print("❌ [SOURCE SERVER] Error: Request is not JSON")
        return jsonify({
            "status": "error",
            "message": "Content-Type must be application/json"
        }), 400

    payload = request.get_json()
    customers = payload.get("customers")

    if customers is None:
        customers = [payload.get("customer")]

    if not customers or not isinstance(customers, list):
        return jsonify({
            "status": "error",
            "message": "Provide 'customers' (list) or 'customer' (object)"
        }), 400

    required_fields = [
        "customer_id",
        "first_name",
        "last_name",
        "contact_num",
        "email_addr",
        "join_date",
        "status_code",
    ]

    added = 0
    for idx, customer in enumerate(customers):
        if not isinstance(customer, dict):
            return jsonify({
                "status": "error",
                "message": f"Customer {idx} must be an object"
            }), 400

        missing = [field for field in required_fields if field not in customer]
        if missing:
            return jsonify({
                "status": "error",
                "message": f"Customer {idx} missing fields: {missing}"
            }), 400

        LEGACY_CUSTOMERS.append(customer)
        added += 1

    print(f"✅ [SOURCE SERVER] Added {added} customer records")
    return jsonify({
        "status": "success",
        "added": added,
        "total_count": len(LEGACY_CUSTOMERS)
    }), 201

@source_app.route('/health', methods=['GET'])
def source_health():
    return jsonify({"status": "healthy", "service": "source_server"}), 200


# =============================================================================
# DESTINATION SERVER (Modernized User Data)
# =============================================================================

destination_app = Flask("destination_server")

@destination_app.after_request
def add_destination_cors_headers(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response

# Storage for received modernized data
received_users = []

@destination_app.route('/api/destination', methods=['POST'])
def post_destination_data():
    """
    Endpoint B: Accepts modernized user data

    Expected JSON structure:
    {
        "users": [
            {
                
                "fullName": "string",
                "phoneDetails": {
                    "number": "string",
                    "formatted": "string"
                },
                "emailAddress": "string",
                "registrationDate": "string (ISO format)",
                "accountStatus": "string (active/inactive)"
            }
        ]
    }
    """
    print("📥 [DESTINATION SERVER] Received POST request to /api/destination")

    if not request.is_json:
        print("❌ [DESTINATION SERVER] Error: Request is not JSON")
        return jsonify({
            "status": "error",
            "message": "Content-Type must be application/json"
        }), 400

    data = request.get_json()

    # Validate the data structure
    if "users" not in data:
        print("❌ [DESTINATION SERVER] Error: Missing 'users' field")
        return jsonify({
            "status": "error",
            "message": "Missing required field: 'users'"
        }), 400

    users = data["users"]

    # Validate each user has the required modernized fields
    required_fields = ["fullName", "phoneDetails", "emailAddress",
                      "registrationDate", "accountStatus"]

    for idx, user in enumerate(users):
        missing_fields = [field for field in required_fields if field not in user]
        if missing_fields:
            print(f"❌ [DESTINATION SERVER] Error: User {idx} missing fields: {missing_fields}")
            return jsonify({
                "status": "error",
                "message": f"User {idx} missing required fields: {missing_fields}"
            }), 400

        # Validate phoneDetails structure
        if "number" not in user["phoneDetails"]:
            print(f"❌ [DESTINATION SERVER] Error: User {idx} missing phoneDetails.number")
            return jsonify({
                "status": "error",
                "message": f"User {idx} missing phoneDetails.number"
            }), 400

    # Store the received data
    received_users.extend(users)

    print(f"✅ [DESTINATION SERVER] Successfully received {len(users)} user records")
    print(f"📊 [DESTINATION SERVER] Total stored users: {len(received_users)}")

    return jsonify({
        "status": "success",
        "message": f"Successfully processed {len(users)} users",
        "received_count": len(users),
        "total_stored": len(received_users)
    }), 201

@destination_app.route('/api/destination/list', methods=['GET'])
def list_destination_data():
    """Helper endpoint to view all received data"""
    print(f"📋 [DESTINATION SERVER] Listing {len(received_users)} stored users")
    return jsonify({
        "status": "success",
        "users": received_users,
        "total_count": len(received_users)
    }), 200

@destination_app.route('/api/destination/clear', methods=['POST'])
def clear_destination_data():
    """Helper endpoint to clear stored data"""
    global received_users
    count = len(received_users)
    received_users = []
    print(f"🗑️ [DESTINATION SERVER] Cleared {count} stored users")
    return jsonify({
        "status": "success",
        "message": f"Cleared {count} users"
    }), 200

@destination_app.route('/health', methods=['GET'])
def destination_health():
    return jsonify({
        "status": "healthy",
        "service": "destination_server",
        "stored_users": len(received_users)
    }), 200


# =============================================================================
# SERVER RUNNER
# =============================================================================

def run_source_server(port=5001):
    """Run the source server on specified port"""
    print(f"🚀 Starting Source Server on port {port}")
    source_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_destination_server(port=5002):
    """Run the destination server on specified port"""
    print(f"🚀 Starting Destination Server on port {port}")
    destination_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_both_servers(source_port=5001, destination_port=5002):
    """Run both servers in separate threads"""
    print("=" * 70)
    print("🎯 AIOS MIDDLEWARE DEMO - FLASK SERVERS")
    print("=" * 70)

    # Start source server in a thread
    source_thread = Thread(
        target=run_source_server,
        args=(source_port,),
        daemon=True
    )
    source_thread.start()

    # Start destination server in a thread
    destination_thread = Thread(
        target=run_destination_server,
        args=(destination_port,),
        daemon=True
    )
    destination_thread.start()

    print("\n✅ Both servers are running!")
    print(f"📍 Source Server: http://localhost:{source_port}/api/source")
    print(f"📍 Destination Server: http://localhost:{destination_port}/api/destination")
    print("\nPress Ctrl+C to stop the servers\n")
    print("=" * 70)

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")


if __name__ == "__main__":
    run_both_servers()
