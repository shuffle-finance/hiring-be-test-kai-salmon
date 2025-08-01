# Transaction API Specification

## Base URL
```
http://localhost:8000
```

## Authentication
No authentication required for this coding test.

## Rate Limiting
- Base delay: 0.1 seconds per request
- Additional random variance: 0-0.3 seconds
- Rate limit delay: 0.05 seconds

## Response Format
All endpoints return JSON. Successful responses have HTTP status 200. Error responses include an `error` field.

---

## Endpoints

### GET /health
Health check endpoint to verify API availability.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-19T21:24:04.286764",
  "version": "1.0.0",
  "data_loaded": true,
  "accounts_available": 76,
  "total_transaction_records": 3233
}
```

**Fields:**
- `status`: Always "healthy" if API is running
- `timestamp`: Current UTC timestamp
- `version`: API version
- `data_loaded`: Whether transaction data was loaded successfully
- `accounts_available`: Number of accounts available for testing
- `total_transaction_records`: Total transaction records loaded

---

### GET /accounts
Get list of all available account IDs for testing.

**Response:**
```json
{
  "accounts": [
    "04b3efb2-c8b1-1073-9d16-153585326359",
    "05d03a99-0429-6218-7b21-efdd118914fd",
    "..."
  ],
  "total_count": 76,
  "timestamp": "2025-07-19T21:24:04.286764"
}
```

**Fields:**
- `accounts`: Array of account ID strings (UUIDs)
- `total_count`: Total number of accounts
- `timestamp`: Response generation time

---

### GET /accounts/{accountId}/transactions
Get transaction records for a specific account with pagination.

**Parameters:**
- `accountId` (path): Account UUID
- `page` (query, optional): Page number (default: 1)
- `per_page` (query, optional): Records per page (default: 10, max: 100)

**Example Request:**
```
GET /accounts/04b3efb2-c8b1-1073-9d16-153585326359/transactions?page=1&per_page=5
```

**Response:**
```json
{
  "transactions": [
    {
      "metadata": {
        "accountId": "04b3efb2-c8b1-1073-9d16-153585326359",
        "requisitionId": "884270da-3ebb-450a-a84a-d71461ef7bb2",
        "createdAt": "2025-06-26T19:06:14.142Z",
        "traceId": "e6950484-a8ba-4aaa-bf52-f8cc7fed72ba"
      },
      "payload": {
        "pending": [
          {
            "bookingDate": "2025-06-26",
            "transactionAmount": {
              "amount": "-12.99",
              "currency": "GBP"
            },
            "creditorName": "NETFLIX",
            "proprietaryBankTransactionCode": "DEB",
            "merchantCategoryCode": "4899"
          }
        ],
        "booked": [
          {
            "transactionId": "T1c50a94bb85ed1c02210801138f683c1",
            "entryReference": "NIKOLA KRESTININA,PX28N9IY152DT9P801",
            "bookingDate": "2025-06-26",
            "valueDate": "2025-06-26",
            "transactionAmount": {
              "amount": "13.00",
              "currency": "GBP"
            },
            "remittanceInformationUnstructured": "NIKOLA KRESTININA NIKOLA KRESTININA PX28N9IY152DT9P801",
            "additionalInformation": "NIKOLA KRESTININA,PX28N9IY152DT9P801",
            "proprietaryBankTransactionCode": "FPI",
            "internalTransactionId": "4a108854be20e262473bdd210da9d3d1"
          }
        ]
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 5,
    "total_count": 107,
    "total_pages": 22,
    "has_next": true,
    "has_prev": false
  },
  "account_id": "04b3efb2-c8b1-1073-9d16-153585326359",
  "timestamp": "2025-07-19T21:24:04.286764"
}
```

**Transaction Record Structure:**

#### Metadata
- `accountId`: Account UUID
- `requisitionId`: Request ID from banking provider
- `createdAt`: When this transaction record was created
- `traceId`: Trace ID for debugging

#### Payload
- `pending`: Array of pending transactions
- `booked`: Array of confirmed/booked transactions

#### Transaction Fields (Pending & Booked)
- `transactionId`: Unique transaction identifier (booked only)
- `bookingDate`: Date transaction was booked (YYYY-MM-DD)
- `valueDate`: Value date (booked only)
- `bookingDateTime`: ISO datetime string (some transactions)
- `transactionAmount.amount`: Amount as string (negative for debits)
- `transactionAmount.currency`: Currency code (e.g., "GBP")
- `creditorName`: Merchant/payee name
- `debtorName`: Payer name (some transactions)
- `remittanceInformationUnstructured`: Transaction description
- `additionalInformation`: Additional details
- `entryReference`: Bank reference
- `proprietaryBankTransactionCode`: Bank transaction type code
- `merchantCategoryCode`: MCC code (some transactions)
- `internalTransactionId`: Internal bank ID (booked only)

**Error Responses:**

404 - Account not found:
```json
{
  "error": "Account not found: invalid-account-id"
}
```

400 - Invalid pagination:
```json
{
  "error": "Page number must be >= 1"
}
```

---

### GET /accounts/{accountId}/summary
Get summary statistics for an account.

**Parameters:**
- `accountId` (path): Account UUID

**Response:**
```json
{
  "account_id": "04b3efb2-c8b1-1073-9d16-153585326359",
  "total_transaction_records": 107,
  "total_pending_transactions": 234,
  "total_booked_transactions": 1456,
  "date_range": {
    "first_transaction": "2025-06-25T23:03:51.307Z",
    "last_transaction": "2025-07-17T23:23:41.841Z"
  },
  "timestamp": "2025-07-19T21:24:04.286764"
}
```

---

### GET /stats
Get overall API statistics.

**Response:**
```json
{
  "total_accounts": 76,
  "total_transaction_records": 3233,
  "total_pending_transactions": 11379,
  "total_booked_transactions": 102130,
  "api_version": "1.0.0",
  "configuration": {
    "default_page_size": 10,
    "max_page_size": 100,
    "base_delay": 0.1
  },
  "timestamp": "2025-07-19T21:24:04.286764"
}
```

---

## Key Data Insights

### Transaction States
- **Pending**: Transactions that are authorized but not yet settled
- **Booked**: Confirmed, settled transactions
- **State Transitions**: Pending transactions may later appear as booked

### Amount Handling
- Amounts are strings to preserve precision
- Negative amounts = debits (money going out)
- Positive amounts = credits (money coming in)
- Currency is always "GBP" in this dataset

### Transaction IDs
- **Pending transactions**: May or may not have transaction IDs
- **Booked transactions**: Always have transaction IDs
- **Duplicates**: Same transaction may appear multiple times
- **Relationships**: Use amount + date + merchant to match pending → booked

### Data Quality Issues
You may encounter:
- Missing fields (some transactions don't have all fields)
- Inconsistent formats (dates, amounts)
- Duplicate transactions with slight variations
- Pending transactions that never become booked
- Booked transactions without corresponding pending

### Merchant Names
- Anonymized but realistic (AMAZON, TESCO, etc.)
- Same merchant may appear with slight variations
- Use fuzzy matching if implementing merchant analytics

### Performance Characteristics
- ~3,200 transaction records total
- ~76 accounts
- ~150 transactions per account on average
- Largest accounts have 200+ transaction records
- API includes realistic delays (0.1-0.4 seconds per request)

---

## Testing Strategy

1. **Start with one account**: Pick the first account from `/accounts`
2. **Fetch all pages**: Use pagination to get all transaction records
3. **Process data**: Extract pending and booked transactions
4. **Handle relationships**: Match pending → booked transitions
5. **Calculate balances**: Sum final transaction amounts
6. **Test edge cases**: Empty accounts, malformed data, etc.

## Common Patterns

### Pagination Loop
```python
def fetch_all_transactions(account_id):
    transactions = []
    page = 1
    
    while True:
        response = requests.get(f"/accounts/{account_id}/transactions?page={page}&per_page=50")
        data = response.json()
        
        transactions.extend(data['transactions'])
        
        if not data['pagination']['has_next']:
            break
            
        page += 1
    
    return transactions
```

### Transaction Processing
```python
def process_transaction_record(record):
    pending = record['payload'].get('pending', [])
    booked = record['payload'].get('booked', [])
    
    # Process each transaction type
    for tx in pending:
        # Handle pending transaction
        pass
        
    for tx in booked:
        # Handle booked transaction
        pass
``` 