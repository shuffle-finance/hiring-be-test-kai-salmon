#!/usr/bin/env python3
"""
Transaction API Server

Serves anonymized transaction data for the backend developer coding test.
Provides RESTful endpoints with realistic delays and pagination to simulate
real-world banking API constraints.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from functools import wraps
import threading
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for candidate applications

# Global variables for data and configuration
transaction_data: List[Dict[str, Any]] = []
accounts_cache: List[str] = []
transactions_by_account: Dict[str, List[Dict[str, Any]]] = {}

# Configuration
CONFIG = {
    'data_path': os.getenv('DATA_PATH', '/app/data/transactions.json'),
    'base_delay': float(os.getenv('BASE_DELAY', '0.1')),  # Base API delay in seconds
    'max_delay': float(os.getenv('MAX_DELAY', '0.5')),    # Maximum random delay
    'default_page_size': int(os.getenv('DEFAULT_PAGE_SIZE', '10')),
    'max_page_size': int(os.getenv('MAX_PAGE_SIZE', '100')),
    'rate_limit_delay': float(os.getenv('RATE_LIMIT_DELAY', '0.05'))  # Additional delay for rate limiting
}

class APIError(Exception):
    """Custom API error with status codes"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

def simulate_network_delay():
    """Add realistic network latency simulation"""
    base_delay = CONFIG['base_delay']
    random_variance = random.uniform(0, CONFIG['max_delay'] - base_delay)
    total_delay = base_delay + random_variance
    time.sleep(total_delay)

def rate_limit():
    """Simple rate limiting simulation"""
    time.sleep(CONFIG['rate_limit_delay'])

def error_handler(f):
    """Decorator for consistent error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            logger.warning(f"API Error: {e.message}")
            return jsonify({'error': e.message}), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function

def load_transaction_data():
    """Load and organize transaction data on startup"""
    global transaction_data, accounts_cache, transactions_by_account
    
    try:
        logger.info(f"Loading transaction data from {CONFIG['data_path']}")
        
        with open(CONFIG['data_path'], 'r', encoding='utf-8') as f:
            transaction_data = json.load(f)
        
        logger.info(f"Loaded {len(transaction_data)} transaction records")
        
        # Extract unique account IDs
        account_ids = set()
        transactions_by_account = {}
        
        for tx_record in transaction_data:
            account_id = tx_record['metadata']['accountId']
            account_ids.add(account_id)
            
            if account_id not in transactions_by_account:
                transactions_by_account[account_id] = []
            transactions_by_account[account_id].append(tx_record)
        
        # Sort accounts for deterministic results
        accounts_cache = sorted(list(account_ids))
        
        # Sort transactions by timestamp for each account
        for account_id in transactions_by_account:
            transactions_by_account[account_id].sort(
                key=lambda x: x['metadata']['createdAt']
            )
        
        logger.info(f"Organized transactions for {len(accounts_cache)} accounts")
        
        # Log some statistics
        total_pending = sum(
            len(tx['payload'].get('pending', []))
            for tx in transaction_data
        )
        total_booked = sum(
            len(tx['payload'].get('booked', []))
            for tx in transaction_data
        )
        
        logger.info(f"Dataset contains {total_pending} pending and {total_booked} booked transactions")
        
    except FileNotFoundError:
        logger.error(f"Transaction data file not found: {CONFIG['data_path']}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in transaction data file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading transaction data: {e}")
        raise

@app.route('/health', methods=['GET'])
@error_handler
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'data_loaded': len(transaction_data) > 0,
        'accounts_available': len(accounts_cache),
        'total_transaction_records': len(transaction_data)
    })

@app.route('/accounts', methods=['GET'])
@error_handler
def get_accounts():
    """Get list of all available account IDs"""
    simulate_network_delay()
    rate_limit()
    
    if not accounts_cache:
        raise APIError("No accounts available", 503)
    
    logger.info(f"Returning {len(accounts_cache)} account IDs")
    
    return jsonify({
        'accounts': accounts_cache,
        'total_count': len(accounts_cache),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/accounts/<account_id>/transactions', methods=['GET'])
@error_handler
def get_account_transactions(account_id: str):
    """Get transactions for a specific account with pagination"""
    simulate_network_delay()
    rate_limit()
    
    # Validate account exists
    if account_id not in accounts_cache:
        raise APIError(f"Account not found: {account_id}", 404)
    
    # Get pagination parameters
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', CONFIG['default_page_size']))
    except ValueError:
        raise APIError("Invalid pagination parameters", 400)
    
    if page < 1:
        raise APIError("Page number must be >= 1", 400)
    
    if per_page < 1 or per_page > CONFIG['max_page_size']:
        raise APIError(f"Page size must be between 1 and {CONFIG['max_page_size']}", 400)
    
    # Get transactions for this account
    account_transactions = transactions_by_account.get(account_id, [])
    
    # Calculate pagination
    total_count = len(account_transactions)
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    if start_index >= total_count and total_count > 0:
        raise APIError(f"Page {page} is beyond available data", 404)
    
    # Get page data
    page_transactions = account_transactions[start_index:end_index]
    
    # Calculate pagination metadata
    has_next = end_index < total_count
    has_prev = page > 1
    total_pages = (total_count + per_page - 1) // per_page
    
    logger.info(f"Returning page {page} of transactions for account {account_id[:8]}... ({len(page_transactions)} records)")
    
    response_data = {
        'transactions': page_transactions,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev
        },
        'account_id': account_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(response_data)

@app.route('/accounts/<account_id>/summary', methods=['GET'])
@error_handler
def get_account_summary(account_id: str):
    """Get summary statistics for an account"""
    simulate_network_delay()
    rate_limit()
    
    # Validate account exists
    if account_id not in accounts_cache:
        raise APIError(f"Account not found: {account_id}", 404)
    
    account_transactions = transactions_by_account.get(account_id, [])
    
    # Calculate summary statistics
    total_records = len(account_transactions)
    total_pending = sum(len(tx['payload'].get('pending', [])) for tx in account_transactions)
    total_booked = sum(len(tx['payload'].get('booked', [])) for tx in account_transactions)
    
    # Date range
    if account_transactions:
        first_transaction = account_transactions[0]['metadata']['createdAt']
        last_transaction = account_transactions[-1]['metadata']['createdAt']
    else:
        first_transaction = last_transaction = None
    
    summary = {
        'account_id': account_id,
        'total_transaction_records': total_records,
        'total_pending_transactions': total_pending,
        'total_booked_transactions': total_booked,
        'date_range': {
            'first_transaction': first_transaction,
            'last_transaction': last_transaction
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    logger.info(f"Returning summary for account {account_id[:8]}...")
    
    return jsonify(summary)

@app.route('/stats', methods=['GET'])
@error_handler
def get_api_stats():
    """Get overall API statistics"""
    simulate_network_delay()
    
    total_pending = sum(
        len(tx['payload'].get('pending', []))
        for tx in transaction_data
    )
    total_booked = sum(
        len(tx['payload'].get('booked', []))
        for tx in transaction_data
    )
    
    stats = {
        'total_accounts': len(accounts_cache),
        'total_transaction_records': len(transaction_data),
        'total_pending_transactions': total_pending,
        'total_booked_transactions': total_booked,
        'api_version': '1.0.0',
        'configuration': {
            'default_page_size': CONFIG['default_page_size'],
            'max_page_size': CONFIG['max_page_size'],
            'base_delay': CONFIG['base_delay']
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return jsonify(stats)

@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Custom 405 handler"""
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Load data when module is imported (for gunicorn workers)
try:
    load_transaction_data()
except Exception as e:
    logger.error(f"Failed to load data on import: {e}")

if __name__ == '__main__':
    try:
        logger.info("Starting Transaction API Server...")
        
        # Data already loaded on import
        
        # Start the Flask development server
        app.run(
            host='0.0.0.0',
            port=8000,
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        exit(1) 