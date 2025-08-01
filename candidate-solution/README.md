# 🚀 Your Solution Goes Here

This is your workspace for the transaction processing coding test. Build your solution in this directory using any programming language and framework you prefer.

## 📋 Quick Start Checklist

- [ ] Choose your tech stack (Python/Flask, Node.js/Express, Go, Java, etc.)
- [ ] Design your database schema
- [ ] Implement data consumption from the transaction API
- [ ] Process and deduplicate transaction data
- [ ] Build the two required endpoints
- [ ] Test with the validation script

## 🎯 Required Endpoints

Your application **must** expose these two endpoints:

### 1. `GET /users/{userId}/transactions`
Return all final (processed) transactions for a user, sorted by date.

**Example Response:**
```json
{
  "user_id": "001527b5-f40b-455f-a900-991d44067adf",
  "transactions": [
    {
      "id": "unique-transaction-id",
      "amount": -12.50,
      "currency": "GBP",
      "date": "2025-06-26T10:30:00Z",
      "description": "Coffee Shop Purchase",
      "status": "booked",
      "type": "card_payment"
    }
  ],
  "count": 1
}
```

### 2. `GET /users/{userId}/balance`
Return the current balance for a user (sum of all final transactions).

**Example Response:**
```json
{
  "user_id": "001527b5-f40b-455f-a900-991d44067adf",
  "balance": 1247.83,
  "currency": "GBP",
  "transaction_count": 45,
  "last_updated": "2025-06-28T15:22:10Z"
}
```

## 🗄️ Database Connection

PostgreSQL is available with these credentials:

- **Host**: `postgres` (from Docker containers) or `localhost` (from host machine)
- **Port**: `5432`
- **Database**: `coding_test`
- **Username**: `test_user`
- **Password**: `test_password`

**Connection Examples:**
```bash
# PostgreSQL URL format
postgresql://test_user:test_password@postgres:5432/coding_test

# From host machine
postgresql://test_user:test_password@localhost:5432/coding_test
```

## 📁 Suggested Project Structure

### Python/Flask Example
```
candidate-solution/
├── app.py                    # Main Flask application
├── models/
│   ├── __init__.py
│   ├── transaction.py        # Transaction model/schema
│   └── database.py          # Database connection
├── services/
│   ├── __init__.py
│   ├── data_processor.py    # Handle duplicates, state transitions
│   ├── transaction_fetcher.py # Consume transaction API
│   └── balance_calculator.py # Calculate user balances
├── routes/
│   ├── __init__.py
│   ├── transactions.py      # Transaction endpoints
│   └── health.py           # Health check (optional)
├── requirements.txt         # Dependencies
├── Dockerfile              # Container setup (optional)
├── schema.sql              # Database schema
└── README.md               # Your setup instructions
```

### Node.js/Express Example
```
candidate-solution/
├── index.js                 # Main Express app
├── models/
│   ├── Transaction.js       # Transaction model
│   └── Database.js         # Database connection
├── services/
│   ├── dataProcessor.js    # Handle duplicates, state transitions
│   ├── transactionFetcher.js # Consume transaction API
│   └── balanceCalculator.js # Calculate user balances
├── routes/
│   ├── transactions.js     # Transaction endpoints
│   └── health.js          # Health check (optional)
├── package.json            # Dependencies
├── Dockerfile             # Container setup (optional)
├── schema.sql             # Database schema
└── README.md              # Your setup instructions
```

## 💡 Implementation Tips

### 1. Data Processing Strategy
- **Fetch all accounts** from `http://localhost:8000/accounts`
- **Paginate through transactions** for each account
- **Handle duplicates** by grouping similar transactions
- **Manage state transitions** (pending → booked)

### 2. Database Schema Ideas
```sql
-- Example schema (adapt as needed)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE transactions (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    date TIMESTAMP NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL,
    type VARCHAR(50),
    raw_data JSONB,  -- Store original transaction data
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX idx_transactions_status ON transactions(status);
```

### 3. Deduplication Logic
Consider grouping transactions by:
- Account ID + Amount + Date + Description
- Internal transaction references
- Timestamp proximity for pending/booked pairs

### 4. Error Handling
- Handle API rate limits gracefully
- Validate incoming data
- Return proper HTTP status codes
- Log errors for debugging

## 🧪 Testing Your Solution

### Manual Testing
```bash
# Test your endpoints (replace port with your application's port)
curl http://localhost:3000/users/001527b5-f40b-455f-a900-991d44067adf/transactions
curl http://localhost:3000/users/001527b5-f40b-455f-a900-991d44067adf/balance
```

### Automated Validation
```bash
cd ../validation
pip install -r requirements.txt
python test_apis.py --candidate-url http://localhost:3000
```

## 📝 Documentation Requirements

Create a `README.md` in your solution that includes:

1. **Setup Instructions**: How to run your application
2. **API Documentation**: Endpoint descriptions and examples
3. **Database Schema**: Your table structures and relationships
4. **Design Decisions**: Why you chose your approach
5. **Known Issues**: Any limitations or assumptions

### Example Documentation Template
```markdown
# Transaction Processing Service

## Setup and Run

[Instructions to start your application]

## API Endpoints

[Document your endpoints with examples]

## Database Schema

[Describe your database design]

## Design Decisions

[Explain your approach to deduplication, state transitions, etc.]

## Testing

[How to test your implementation]
```

## 🔍 Data Sources

- **Transaction API**: `http://localhost:8000/accounts/{id}/transactions`
- **Account List**: `http://localhost:8000/accounts`
- **API Documentation**: `../docs/api-spec.md`
- **Sample Responses**: `../docs/sample-responses.json`

## ✅ Success Criteria

- ✅ Both endpoints return valid JSON responses
- ✅ Transaction data is correctly processed and deduplicated
- ✅ Balance calculations are accurate
- ✅ Code is clean, readable, and well-documented
- ✅ Application handles errors gracefully

## 🆘 Need Help?

- Check the main `CODING_TEST_BRIEFING.md` for detailed requirements
- Look at `../docs/api-spec.md` for API documentation
- Examine `../docs/sample-responses.json` for response examples
- Run `../verify_setup.sh` to ensure your environment is working

Good luck! 🚀

---

*Remember: Focus on delivering a working solution that handles the core requirements well. Perfect is the enemy of good!* 