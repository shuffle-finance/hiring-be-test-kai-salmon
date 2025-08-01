#!/usr/bin/env python3
"""
Transaction Data Anonymization Script

Parses the raw_transactions directory structure and anonymizes sensitive data
while maintaining the complexity and relationships of real banking transactions.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
import hashlib
import random
import uuid
from dataclasses import dataclass, asdict
from decimal import Decimal

@dataclass
class TransactionFile:
    """Represents a single transaction file with metadata"""
    filepath: str
    account_id: str
    year: int
    month: int
    day: int
    timestamp: str
    
class TransactionParser:
    """Parses and processes raw transaction files"""
    
    def __init__(self, raw_transactions_dir: str = "raw_transactions"):
        self.raw_transactions_dir = Path(raw_transactions_dir)
        self.transaction_files: List[TransactionFile] = []
        self.all_transactions: List[Dict[str, Any]] = []
        
    def discover_transaction_files(self) -> List[TransactionFile]:
        """
        Discovers all transaction JSON files in the directory structure.
        Expected structure: raw_transactions/year=YYYY/month=MM/day=DD/account_id=UUID/transactions_TIMESTAMP.json
        """
        print(f"Scanning directory: {self.raw_transactions_dir}")
        
        if not self.raw_transactions_dir.exists():
            raise FileNotFoundError(f"Directory not found: {self.raw_transactions_dir}")
        
        transaction_files = []
        
        # Walk through the year/month/day/account_id structure
        for year_dir in self.raw_transactions_dir.glob("year=*"):
            year = int(year_dir.name.split("=")[1])
            
            for month_dir in year_dir.glob("month=*"):
                month = int(month_dir.name.split("=")[1])
                
                for day_dir in month_dir.glob("day=*"):
                    day = int(day_dir.name.split("=")[1])
                    
                    for account_dir in day_dir.glob("account_id=*"):
                        account_id = account_dir.name.split("=")[1]
                        
                        # Find all transaction JSON files in this account directory
                        for json_file in account_dir.glob("transactions_*.json"):
                            # Extract timestamp from filename
                            timestamp_match = re.search(r'transactions_(.+)\.json$', json_file.name)
                            if timestamp_match:
                                timestamp = timestamp_match.group(1)
                                
                                transaction_file = TransactionFile(
                                    filepath=str(json_file),
                                    account_id=account_id,
                                    year=year,
                                    month=month,
                                    day=day,
                                    timestamp=timestamp
                                )
                                transaction_files.append(transaction_file)
        
        print(f"Found {len(transaction_files)} transaction files")
        self.transaction_files = transaction_files
        return transaction_files
    
    def load_transaction_data(self) -> List[Dict[str, Any]]:
        """
        Loads all transaction data from discovered files.
        Returns list of raw transaction objects.
        """
        all_transactions = []
        
        for tx_file in self.transaction_files:
            try:
                with open(tx_file.filepath, 'r', encoding='utf-8') as f:
                    transaction_data = json.load(f)
                    
                    # Add file metadata to help with processing
                    transaction_data['_file_info'] = asdict(tx_file)
                    all_transactions.append(transaction_data)
                    
            except Exception as e:
                print(f"Error loading {tx_file.filepath}: {e}")
                continue
        
        print(f"Loaded {len(all_transactions)} transaction records")
        self.all_transactions = all_transactions
        return all_transactions
    
    def analyze_data_structure(self) -> Dict[str, Any]:
        """
        Analyzes the structure and content of transaction data to understand
        what needs to be anonymized and what patterns exist.
        """
        analysis = {
            'total_files': len(self.transaction_files),
            'total_transactions': len(self.all_transactions),
            'account_ids': set(),
            'date_range': {'min': None, 'max': None},
            'transaction_types': set(),
            'creditor_names': set(),
            'currencies': set(),
            'amount_range': {'min': None, 'max': None},
            'pending_vs_booked': {'pending': 0, 'booked': 0},
            'transaction_id_patterns': set(),
            'sample_transactions': [],
            'state_transitions': {'pending_to_booked': [], 'duplicates': []},
            'transaction_relationships': {}
        }
        
        for tx_data in self.all_transactions:
            # Account IDs
            account_id = tx_data['metadata']['accountId']
            analysis['account_ids'].add(account_id)
            
            # Date range
            created_at = tx_data['metadata']['createdAt']
            if analysis['date_range']['min'] is None or created_at < analysis['date_range']['min']:
                analysis['date_range']['min'] = created_at
            if analysis['date_range']['max'] is None or created_at > analysis['date_range']['max']:
                analysis['date_range']['max'] = created_at
            
            # Analyze payload
            payload = tx_data['payload']
            
            # Pending transactions
            for pending_tx in payload.get('pending', []):
                analysis['pending_vs_booked']['pending'] += 1
                self._analyze_transaction(pending_tx, analysis)
            
            # Booked transactions  
            for booked_tx in payload.get('booked', []):
                analysis['pending_vs_booked']['booked'] += 1
                self._analyze_transaction(booked_tx, analysis)
            
            # Keep some samples for reference
            if len(analysis['sample_transactions']) < 5:
                analysis['sample_transactions'].append(tx_data)
        
        # Analyze transaction relationships and state transitions
        self._analyze_transaction_relationships(analysis)
        
        # Convert sets to lists for JSON serialization
        analysis['account_ids'] = list(analysis['account_ids'])
        analysis['transaction_types'] = list(analysis['transaction_types'])
        analysis['creditor_names'] = list(analysis['creditor_names'])
        analysis['currencies'] = list(analysis['currencies'])
        analysis['transaction_id_patterns'] = list(analysis['transaction_id_patterns'])
        
        return analysis
    
    def _analyze_transaction_relationships(self, analysis: Dict[str, Any]):
        """Analyze relationships between transactions (pending → booked, duplicates)"""
        # Group transactions by account and analyze patterns
        transactions_by_account = {}
        
        for tx_data in self.all_transactions:
            account_id = tx_data['metadata']['accountId']
            if account_id not in transactions_by_account:
                transactions_by_account[account_id] = []
            transactions_by_account[account_id].append(tx_data)
        
        # For each account, look for state transitions and duplicates
        for account_id, account_transactions in transactions_by_account.items():
            # Sort by timestamp to understand chronology
            account_transactions.sort(key=lambda x: x['metadata']['createdAt'])
            
            # Track all transactions by ID and characteristics
            pending_transactions = {}
            booked_transactions = {}
            
            for tx_data in account_transactions:
                payload = tx_data['payload']
                
                # Collect pending transactions
                for pending_tx in payload.get('pending', []):
                    tx_key = self._create_transaction_key(pending_tx)
                    if tx_key not in pending_transactions:
                        pending_transactions[tx_key] = []
                    pending_transactions[tx_key].append({
                        'transaction': pending_tx,
                        'timestamp': tx_data['metadata']['createdAt'],
                        'file_info': tx_data.get('_file_info', {})
                    })
                
                # Collect booked transactions
                for booked_tx in payload.get('booked', []):
                    tx_key = self._create_transaction_key(booked_tx)
                    if tx_key not in booked_transactions:
                        booked_transactions[tx_key] = []
                    booked_transactions[tx_key].append({
                        'transaction': booked_tx,
                        'timestamp': tx_data['metadata']['createdAt'],
                        'file_info': tx_data.get('_file_info', {})
                    })
            
            # Look for pending → booked transitions
            for tx_key, pending_list in pending_transactions.items():
                if tx_key in booked_transactions:
                    booked_list = booked_transactions[tx_key]
                    
                    # Found potential state transition
                    earliest_pending = min(pending_list, key=lambda x: x['timestamp'])
                    earliest_booked = min(booked_list, key=lambda x: x['timestamp'])
                    
                    if earliest_pending['timestamp'] <= earliest_booked['timestamp']:
                        analysis['state_transitions']['pending_to_booked'].append({
                            'account_id': account_id,
                            'transaction_key': tx_key,
                            'pending_first_seen': earliest_pending['timestamp'],
                            'booked_first_seen': earliest_booked['timestamp'],
                            'pending_count': len(pending_list),
                            'booked_count': len(booked_list)
                        })
            
            # Look for duplicates (same transaction appearing multiple times)
            for tx_key, tx_list in {**pending_transactions, **booked_transactions}.items():
                if len(tx_list) > 1:
                    analysis['state_transitions']['duplicates'].append({
                        'account_id': account_id,
                        'transaction_key': tx_key,
                        'occurrence_count': len(tx_list),
                        'timestamps': [tx['timestamp'] for tx in tx_list]
                    })
    
    def _create_transaction_key(self, transaction: Dict[str, Any]) -> str:
        """Create a unique key for a transaction based on its characteristics"""
        # Use multiple fields to create a unique identifier
        key_parts = []
        
        # Transaction ID (if available)
        if 'transactionId' in transaction:
            key_parts.append(f"id:{transaction['transactionId']}")
        
        # Amount and currency
        if 'transactionAmount' in transaction:
            amount = transaction['transactionAmount'].get('amount', '')
            currency = transaction['transactionAmount'].get('currency', '')
            key_parts.append(f"amount:{amount}:{currency}")
        
        # Booking date
        if 'bookingDate' in transaction:
            key_parts.append(f"date:{transaction['bookingDate']}")
        
        # Creditor name
        if 'creditorName' in transaction:
            key_parts.append(f"creditor:{transaction['creditorName']}")
        
        # If no identifying fields, use a hash of the entire transaction
        if not key_parts:
            tx_str = json.dumps(transaction, sort_keys=True)
            return f"hash:{hashlib.md5(tx_str.encode()).hexdigest()}"
        
        return "|".join(key_parts)
    
    def _analyze_transaction(self, transaction: Dict[str, Any], analysis: Dict[str, Any]):
        """Helper method to analyze individual transaction data"""
        # Transaction types
        if 'proprietaryBankTransactionCode' in transaction:
            analysis['transaction_types'].add(transaction['proprietaryBankTransactionCode'])
        
        # Creditor names
        if 'creditorName' in transaction:
            analysis['creditor_names'].add(transaction['creditorName'])
        
        # Currency
        if 'transactionAmount' in transaction and 'currency' in transaction['transactionAmount']:
            analysis['currencies'].add(transaction['transactionAmount']['currency'])
        
        # Amount range
        if 'transactionAmount' in transaction and 'amount' in transaction['transactionAmount']:
            amount = float(transaction['transactionAmount']['amount'])
            if analysis['amount_range']['min'] is None or amount < analysis['amount_range']['min']:
                analysis['amount_range']['min'] = amount
            if analysis['amount_range']['max'] is None or amount > analysis['amount_range']['max']:
                analysis['amount_range']['max'] = amount
        
        # Transaction ID patterns
        if 'transactionId' in transaction:
            # Extract pattern (first 10 chars to identify format)
            tx_id = transaction['transactionId']
            pattern = tx_id[:10] if len(tx_id) >= 10 else tx_id
            analysis['transaction_id_patterns'].add(pattern)

class TransactionAnonymizer:
    """Handles anonymization of sensitive transaction data"""
    
    def __init__(self, seed: int = 42):
        """Initialize with deterministic seed for consistent anonymization"""
        random.seed(seed)
        
        # Mapping caches for consistent anonymization
        self.account_id_map = {}
        self.creditor_name_map = {}
        self.reference_map = {}
        self.transaction_id_map = {}
        self.transaction_key_map = {}  # Preserve transaction relationships
        
        # Fake merchant names for realistic substitution
        self.fake_merchants = [
            "AMAZON", "TESCO", "SAINSBURY'S", "ASDA", "MORRISONS", "WAITROSE",
            "MARKS & SPENCER", "JOHN LEWIS", "NEXT", "H&M", "ZARA", "PRIMARK",
            "STARBUCKS", "COSTA COFFEE", "MCDONALD'S", "KFC", "SUBWAY", "GREGGS",
            "SPOTIFY", "NETFLIX", "DISNEY+", "AMAZON PRIME", "APPLE", "GOOGLE",
            "VODAFONE", "EE", "O2", "THREE", "BT", "SKY", "VIRGIN MEDIA",
            "SHELL", "BP", "ESSO", "TEXACO", "SAINSBURY'S PETROL", "TESCO PETROL",
            "UBER", "DELIVEROO", "JUST EAT", "BOLT", "CITY MAPPER", "TFL",
            "BOOTS", "SUPERDRUG", "HOLLAND & BARRETT", "SPECSAVERS", "VISION EXPRESS",
            "ARGOS", "CURRYS", "SCREWFIX", "B&Q", "HOMEBASE", "IKEA",
            "PIZZA EXPRESS", "NANDOS", "WAGAMAMA", "YO! SUSHI", "LEON", "PRET A MANGER",
            "CINEMA CITY", "ODEON", "VUE CINEMAS", "GYM GROUP", "PURE GYM", "DAVID LLOYD",
            "LLOYDS BANK", "BARCLAYS", "HSBC", "NATWEST", "SANTANDER", "TSB",
            "PAYPAL", "REVOLUT", "MONZO", "STARLING BANK", "WISE", "KLARNA"
        ]
        
        # Common transaction reference patterns
        self.reference_patterns = [
            "REF{:08d}", "TXN{:06d}", "PAY{:07d}", "INV{:05d}", 
            "ORD{:06d}", "PMT{:08d}", "TRF{:07d}", "DD{:06d}"
        ]
        
        # Personal name components for realistic anonymization
        self.first_names = [
            "JAMES", "JOHN", "ROBERT", "MICHAEL", "WILLIAM", "DAVID", "RICHARD", "JOSEPH",
            "THOMAS", "CHRISTOPHER", "CHARLES", "DANIEL", "MATTHEW", "ANTHONY", "MARK",
            "SARAH", "JESSICA", "JENNIFER", "ASHLEY", "EMMA", "OLIVIA", "ELIZABETH", 
            "SOPHIE", "CHARLOTTE", "LUCY", "HANNAH", "GRACE", "ELLIE", "CHLOE", "EMILY"
        ]
        
        self.surnames = [
            "SMITH", "JONES", "TAYLOR", "WILLIAMS", "BROWN", "DAVIES", "EVANS", "WILSON",
            "THOMAS", "ROBERTS", "JOHNSON", "LEWIS", "WALKER", "ROBINSON", "THOMPSON",
            "WHITE", "WATSON", "JACKSON", "WRIGHT", "GREEN", "HARRIS", "COOPER", "KING",
            "LEE", "MARTIN", "CLARKE", "JAMES", "MORGAN", "HUGHES", "EDWARDS", "HILL"
        ]
    
    def anonymize_account_id(self, original_id: str) -> str:
        """Convert account ID to consistent fake UUID"""
        if original_id not in self.account_id_map:
            # Create deterministic UUID based on original ID
            hash_obj = hashlib.md5(original_id.encode())
            fake_uuid = str(uuid.UUID(hash_obj.hexdigest()))
            self.account_id_map[original_id] = fake_uuid
        return self.account_id_map[original_id]
    
    def anonymize_transaction_id(self, original_id: str) -> str:
        """Convert transaction ID to realistic fake ID maintaining format"""
        if original_id not in self.transaction_id_map:
            if original_id.startswith('T'):
                # Format: T + hex string
                fake_id = 'T' + hashlib.md5(original_id.encode()).hexdigest()[:31]
            elif original_id.startswith('tx_'):
                # Format: tx_ + alphanumeric
                fake_id = 'tx_' + hashlib.md5(original_id.encode()).hexdigest()[:20]
            elif len(original_id) > 50:
                # Long hex string format
                fake_id = hashlib.sha256(original_id.encode()).hexdigest()
            else:
                # Generic format
                fake_id = 'TXN' + hashlib.md5(original_id.encode()).hexdigest()[:16]
            
            self.transaction_id_map[original_id] = fake_id
        return self.transaction_id_map[original_id]
    
    def anonymize_creditor_name(self, original_name: str) -> str:
        """Replace creditor names with realistic fake merchants"""
        if not original_name:
            return original_name
            
        if original_name not in self.creditor_name_map:
            # Use hash to deterministically select fake merchant
            hash_val = int(hashlib.md5(original_name.encode()).hexdigest(), 16)
            fake_merchant = self.fake_merchants[hash_val % len(self.fake_merchants)]
            
            # Add location suffix if original had one
            if any(city in original_name.upper() for city in ['LONDON', 'MANCHESTER', 'BIRMINGHAM', 'LEEDS', 'GLASGOW']):
                cities = ['LONDON', 'MANCHESTER', 'BIRMINGHAM', 'LEEDS', 'GLASGOW', 'BRISTOL', 'LIVERPOOL']
                fake_city = cities[hash_val % len(cities)]
                fake_merchant = f"{fake_merchant} {fake_city}"
            
            self.creditor_name_map[original_name] = fake_merchant
        
        return self.creditor_name_map[original_name]
    
    def anonymize_personal_name(self, original_name: str) -> str:
        """Replace personal names in references"""
        if not original_name:
            return original_name
            
        # Generate fake name based on hash
        hash_val = int(hashlib.md5(original_name.encode()).hexdigest(), 16)
        first_name = self.first_names[hash_val % len(self.first_names)]
        surname = self.surnames[(hash_val // 100) % len(self.surnames)]
        
        return f"{first_name} {surname}"
    
    def anonymize_reference(self, original_ref: str) -> str:
        """Anonymize transaction references while maintaining structure"""
        if not original_ref:
            return original_ref
            
        if original_ref not in self.reference_map:
            # Detect and preserve reference patterns
            ref_upper = original_ref.upper()
            
            # Check for personal names
            if any(name in ref_upper for name in ['MR ', 'MRS ', 'MISS ', 'MS ']):
                fake_ref = self.anonymize_personal_name(original_ref)
            # Check for account numbers or references
            elif re.search(r'[A-Z]{2}\d{2}[A-Z0-9]{4}', original_ref):
                # Bank account pattern - replace with fake
                fake_ref = re.sub(r'[A-Z]{2}\d{2}[A-Z0-9]{4}', 'GB29FAKE0123456789', original_ref)
            # Check for card references
            elif re.search(r'\d{4}', original_ref):
                # Replace 4-digit sequences with fake ones
                hash_val = int(hashlib.md5(original_ref.encode()).hexdigest(), 16)
                fake_digits = f"{hash_val % 10000:04d}"
                fake_ref = re.sub(r'\d{4}', fake_digits, original_ref)
            else:
                # Generic reference replacement
                hash_val = int(hashlib.md5(original_ref.encode()).hexdigest(), 16)
                pattern = self.reference_patterns[hash_val % len(self.reference_patterns)]
                fake_ref = pattern.format(hash_val % 100000000)
            
            self.reference_map[original_ref] = fake_ref
        
        return self.reference_map[original_ref]
    
    def anonymize_amount(self, original_amount: str, variance_percent: float = 0.1) -> str:
        """Slightly alter amounts to prevent identification while maintaining realism"""
        try:
            amount = float(original_amount)
            
            # Add small random variance based on amount hash (deterministic)
            hash_val = int(hashlib.md5(original_amount.encode()).hexdigest(), 16)
            variance = (hash_val % 1000) / 1000.0 * variance_percent * 2 - variance_percent
            
            # Apply variance
            new_amount = amount * (1 + variance)
            
            # Round to 2 decimal places for currency
            return f"{new_amount:.2f}"
            
        except (ValueError, TypeError):
            return original_amount
    
    def anonymize_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize a single transaction object while preserving relationships"""
        anonymized = transaction.copy()
        
        # Create transaction key for relationship tracking before anonymization
        original_key = self._create_transaction_key(transaction)
        
        # Anonymize transaction ID while preserving relationships
        if 'transactionId' in anonymized:
            anonymized['transactionId'] = self.anonymize_transaction_id(anonymized['transactionId'])
        
        # Anonymize creditor name
        if 'creditorName' in anonymized:
            anonymized['creditorName'] = self.anonymize_creditor_name(anonymized['creditorName'])
        
        # Anonymize debtor name
        if 'debtorName' in anonymized:
            anonymized['debtorName'] = self.anonymize_personal_name(anonymized['debtorName'])
        
        # Anonymize references
        if 'remittanceInformationUnstructured' in anonymized:
            anonymized['remittanceInformationUnstructured'] = self.anonymize_reference(
                anonymized['remittanceInformationUnstructured']
            )
        
        if 'additionalInformation' in anonymized:
            anonymized['additionalInformation'] = self.anonymize_reference(
                anonymized['additionalInformation']
            )
        
        if 'entryReference' in anonymized:
            anonymized['entryReference'] = self.anonymize_reference(
                anonymized['entryReference']
            )
        
        # Anonymize amounts with small variance
        if 'transactionAmount' in anonymized and 'amount' in anonymized['transactionAmount']:
            anonymized['transactionAmount']['amount'] = self.anonymize_amount(
                anonymized['transactionAmount']['amount']
            )
        
        # Anonymize internal transaction ID
        if 'internalTransactionId' in anonymized:
            anonymized['internalTransactionId'] = hashlib.md5(
                anonymized['internalTransactionId'].encode()
            ).hexdigest()
        
        # Store anonymized transaction key for relationship preservation
        anonymized_key = self._create_transaction_key(anonymized)
        self.transaction_key_map[original_key] = anonymized_key
        
        return anonymized
    
    def _create_transaction_key(self, transaction: Dict[str, Any]) -> str:
        """Create a unique key for a transaction based on its characteristics"""
        # Use multiple fields to create a unique identifier
        key_parts = []
        
        # Transaction ID (if available)
        if 'transactionId' in transaction:
            key_parts.append(f"id:{transaction['transactionId']}")
        
        # Amount and currency
        if 'transactionAmount' in transaction:
            amount = transaction['transactionAmount'].get('amount', '')
            currency = transaction['transactionAmount'].get('currency', '')
            key_parts.append(f"amount:{amount}:{currency}")
        
        # Booking date
        if 'bookingDate' in transaction:
            key_parts.append(f"date:{transaction['bookingDate']}")
        
        # Creditor name
        if 'creditorName' in transaction:
            key_parts.append(f"creditor:{transaction['creditorName']}")
        
        # If no identifying fields, use a hash of the entire transaction
        if not key_parts:
            tx_str = json.dumps(transaction, sort_keys=True)
            return f"hash:{hashlib.md5(tx_str.encode()).hexdigest()}"
        
        return "|".join(key_parts)
    
    def anonymize_transaction_file(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize a complete transaction file"""
        anonymized = transaction_data.copy()
        
        # Anonymize metadata
        if 'metadata' in anonymized:
            metadata = anonymized['metadata'].copy()
            metadata['accountId'] = self.anonymize_account_id(metadata['accountId'])
            
            # Anonymize requisition ID
            if 'requisitionId' in metadata:
                metadata['requisitionId'] = str(uuid.uuid4())
            
            # Anonymize trace ID  
            if 'traceId' in metadata:
                metadata['traceId'] = str(uuid.uuid4())
            
            anonymized['metadata'] = metadata
        
        # Anonymize payload transactions
        if 'payload' in anonymized:
            payload = anonymized['payload'].copy()
            
            # Anonymize pending transactions
            if 'pending' in payload:
                payload['pending'] = [
                    self.anonymize_transaction(tx) for tx in payload['pending']
                ]
            
            # Anonymize booked transactions
            if 'booked' in payload:
                payload['booked'] = [
                    self.anonymize_transaction(tx) for tx in payload['booked']
                ]
            
            anonymized['payload'] = payload
        
        return anonymized

def process_and_anonymize_data():
    """Complete data processing and anonymization workflow"""
    print("=== Transaction Data Processing & Anonymization ===")
    
    # Step 1: Parse and analyze
    parser = TransactionParser()
    transaction_files = parser.discover_transaction_files()
    all_transactions = parser.load_transaction_data()
    analysis = parser.analyze_data_structure()
    
    print(f"Loaded {len(all_transactions)} transaction records from {len(transaction_files)} files")
    print(f"Covering {len(analysis['account_ids'])} unique accounts")
    
    # Step 2: Anonymize data
    print("\n=== Anonymizing Transaction Data ===")
    anonymizer = TransactionAnonymizer(seed=42)
    
    anonymized_transactions = []
    for i, tx_data in enumerate(all_transactions):
        if i % 500 == 0:
            print(f"Processed {i}/{len(all_transactions)} transactions...")
        
        # Remove file info before anonymization
        clean_tx_data = {k: v for k, v in tx_data.items() if k != '_file_info'}
        anonymized_tx = anonymizer.anonymize_transaction_file(clean_tx_data)
        anonymized_transactions.append(anonymized_tx)
    
    print(f"Anonymized {len(anonymized_transactions)} transaction records")
    
    # Step 3: Save anonymized data
    os.makedirs('data', exist_ok=True)
    
    # Save complete anonymized dataset
    with open('data/transactions.json', 'w') as f:
        json.dump(anonymized_transactions, f, indent=2, ensure_ascii=False)
    
    # Save analysis for reference
    with open('data/analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    # Save anonymization mappings for debugging
    mappings = {
        'account_id_map': anonymizer.account_id_map,
        'anonymization_stats': {
            'accounts_anonymized': len(anonymizer.account_id_map),
            'creditors_anonymized': len(anonymizer.creditor_name_map),
            'references_anonymized': len(anonymizer.reference_map),
            'transaction_ids_anonymized': len(anonymizer.transaction_id_map),
            'transaction_relationships_preserved': len(anonymizer.transaction_key_map)
        },
        'relationship_analysis': {
            'pending_to_booked_transitions': len(analysis.get('state_transitions', {}).get('pending_to_booked', [])),
            'duplicate_transactions': len(analysis.get('state_transitions', {}).get('duplicates', [])),
            'total_unique_transaction_keys': len(set(anonymizer.transaction_key_map.keys()))
        }
    }
    
    with open('data/anonymization_mappings.json', 'w') as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Anonymization Complete ===")
    print(f"✅ Created anonymized dataset: data/transactions.json")
    print(f"✅ Original analysis saved: data/analysis.json") 
    print(f"✅ Anonymization mappings: data/anonymization_mappings.json")
    print(f"\nAnonymization Statistics:")
    print(f"  - {mappings['anonymization_stats']['accounts_anonymized']} account IDs anonymized")
    print(f"  - {mappings['anonymization_stats']['creditors_anonymized']} creditor names anonymized")
    print(f"  - {mappings['anonymization_stats']['references_anonymized']} references anonymized")
    print(f"  - {mappings['anonymization_stats']['transaction_ids_anonymized']} transaction IDs anonymized")
    print(f"  - {mappings['anonymization_stats']['transaction_relationships_preserved']} transaction relationships preserved")
    print(f"\nRelationship Analysis:")
    print(f"  - {mappings['relationship_analysis']['pending_to_booked_transitions']} pending → booked transitions detected")
    print(f"  - {mappings['relationship_analysis']['duplicate_transactions']} duplicate transaction patterns found")
    print(f"  - {mappings['relationship_analysis']['total_unique_transaction_keys']} unique transaction signatures")
    
    # Create sample for testing
    sample_size = min(50, len(anonymized_transactions))
    sample_transactions = anonymized_transactions[:sample_size]
    
    with open('data/transactions_sample.json', 'w') as f:
        json.dump(sample_transactions, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sample dataset created: data/transactions_sample.json ({sample_size} records)")
    
    return anonymized_transactions, analysis

def main():
    """Main function with choice of analysis or full processing"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--analyze-only':
        # Just run analysis
        parser = TransactionParser()
        transaction_files = parser.discover_transaction_files()
        all_transactions = parser.load_transaction_data()
        analysis = parser.analyze_data_structure()
        
        print(f"\n=== Data Analysis ===")
        print(f"Total Files: {analysis['total_files']}")
        print(f"Total Transaction Records: {analysis['total_transactions']}")
        print(f"Unique Accounts: {len(analysis['account_ids'])}")
        print(f"Date Range: {analysis['date_range']['min']} to {analysis['date_range']['max']}")
        print(f"Pending Transactions: {analysis['pending_vs_booked']['pending']}")
        print(f"Booked Transactions: {analysis['pending_vs_booked']['booked']}")
        print(f"Currencies: {analysis['currencies']}")
        print(f"Amount Range: £{analysis['amount_range']['min']} to £{analysis['amount_range']['max']}")
        print(f"Transaction Types: {len(analysis['transaction_types'])} types")
        print(f"Unique Merchants: {len(analysis['creditor_names'])} merchants")
    else:
        # Run full processing and anonymization
        process_and_anonymize_data()

if __name__ == "__main__":
    main() 