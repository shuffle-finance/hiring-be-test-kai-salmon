# Backend Developer Coding Test - Transaction Processing System

## 🎯 Overview

Welcome to the Shuffle Finance backend developer coding test! You'll be building a transaction processing system that mirrors real-world financial data challenges. This test evaluates your ability to:

- Consume and process streaming transaction data from a REST API
- Handle messy, real-world data (duplicates, state transitions, inconsistencies)
- Design database schemas and system architecture from scratch
- Build clean, maintainable APIs under time constraints

**Time Allocation**: 2-2.5 hours  
**Language/Framework**: Your choice (we recommend what you're most comfortable with)

---

## 🏗️ What You're Building

You'll create a transaction processing service that:

1. **Consumes transaction data** from our provided API
2. **Processes and cleans** the data (handling duplicates, state changes, etc.)
3. **Stores** processed data in a database (schema design is up to you)
4. **Exposes two REST endpoints** for transaction retrieval and balance calculation

### The Challenge

Real banking data is messy. You'll encounter:
- ✅ **Duplicate transactions** with different IDs
- ✅ **State transitions** (pending → booked)
- ✅ **Data inconsistencies** requiring intelligent deduplication
- ✅ **High transaction volumes** requiring efficient processing

---

## 📋 Requirements

### Required Endpoints

Your application must expose these two endpoints:

#### 1. **GET /users/{userId}/transactions**
Return all final (processed) transactions for a user, sorted by date.

**Response Format:**
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

#### 2. **GET /users/{userId}/balance**
Return the current balance for a user (sum of all final transactions).

**Response Format:**
```json
{
  "user_id": "001527b5-f40b-455f-a900-991d44067adf",
  "balance": 1247.83,
  "currency": "GBP",
  "transaction_count": 45,
  "last_updated": "2025-06-28T15:22:10Z"
}
```

### Data Processing Rules

1. **Handle Duplicates**: Multiple transactions may represent the same real transaction
2. **State Transitions**: `pending` transactions may become `booked` - keep only the final state
3. **Data Integrity**: Ensure your final dataset is consistent and accurate
4. **Performance**: Your API should respond quickly even with large datasets

---

## 🚀 Getting Started

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd be-hiring-coding-exercise

# Start the test environment
docker compose up -d

# Verify everything is running
curl http://localhost:8000/health
```

### Step 2: Explore the Data API

We provide a transaction data API at `http://localhost:8000`:

```bash
# Get list of all account IDs
curl http://localhost:8000/accounts

# Get transactions for a specific account (paginated)
curl "http://localhost:8000/accounts/001527b5-f40b-455f-a900-991d44067adf/transactions?limit=10"

# Get overall statistics
curl http://localhost:8000/stats
```

**Important**: The API serves transactions in chronological order and includes realistic delays. Plan accordingly!

### Step 3: Design Your Solution

Create your solution in the `candidate-solution/` directory:

```
candidate-solution/
├── src/              # Your source code
├── requirements.txt  # Dependencies (Python) or equivalent
├── Dockerfile        # Container setup
├── docker-compose.yml # Your service configuration
├── README.md         # Setup and run instructions
└── schema.sql        # Database schema (if applicable)
```

### Step 4: Database Access

A PostgreSQL database is available at:
- **Host**: `localhost` (or `postgres` from within Docker)
- **Port**: `5432`
- **Database**: `coding_test`
- **Username**: `test_user`
- **Password**: `test_password`

You have full control over the schema design.

---

## 📖 API Documentation

### Data API Endpoints (Provided)

| Endpoint | Description | Example |
|----------|-------------|---------|
| `GET /health` | Health check and statistics | `curl http://localhost:8000/health` |
| `GET /accounts` | List all account IDs | `curl http://localhost:8000/accounts` |
| `GET /accounts/{id}/transactions` | Get account transactions | `curl http://localhost:8000/accounts/{id}/transactions` |
| `GET /accounts/{id}/summary` | Account transaction summary | `curl http://localhost:8000/accounts/{id}/summary` |

### Query Parameters

- `limit`: Number of transactions per page (default: 50, max: 200)
- `offset`: Pagination offset (default: 0)

### Transaction Data Structure

```json
{
  "id": "txn_001527b5_1719399600_001",
  "account_id": "001527b5-f40b-455f-a900-991d44067adf",
  "amount": -12.50,
  "currency": "GBP",
  "date": "2025-06-26T10:30:00Z",
  "description": "Urban Bean Coffee",
  "status": "booked",
  "type": "card_payment",
  "creditor_name": "Urban Bean Coffee Ltd",
  "internal_reference": "REF_789012"
}
```

**Field Explanations:**
- `amount`: Negative = money out, Positive = money in
- `status`: `pending` or `booked`
- `type`: Transaction type (card_payment, bank_transfer, etc.)
- Account ID in the transaction corresponds to the user ID in your API

---

## ✅ Success Criteria

### Functional Requirements (60%)
- ✅ Both required endpoints work correctly
- ✅ Data processing handles duplicates and state transitions
- ✅ Responses match the specified format
- ✅ Balance calculations are accurate

### Code Quality (25%)
- ✅ Clean, readable, well-organized code
- ✅ Proper error handling and validation
- ✅ Appropriate use of design patterns
- ✅ Clear documentation and comments

### System Design (15%)
- ✅ Sensible database schema design
- ✅ Efficient data processing approach
- ✅ Scalable architecture decisions
- ✅ Performance considerations

---

## 🔧 Technical Tips

### Database Schema Ideas
Consider tables for:
- `users` (account information)
- `transactions` (processed, deduplicated transactions)
- `raw_transactions` (optional: for audit trail)

### Processing Strategy Options
1. **Batch Processing**: Periodically fetch and process new data
2. **Event Streaming**: Process transactions as they arrive
3. **Hybrid**: Initial batch load + incremental updates

### Deduplication Approaches
- Group by amount, date, description, account
- Use transaction references and timestamps
- Handle pending → booked state transitions

### Performance Considerations
- Database indexing on frequently queried fields
- Efficient pagination for large result sets
- Caching for balance calculations

---

## 🧪 Testing Your Solution

We provide a validation script to test your endpoints:

```bash
cd validation
pip install -r requirements.txt

# Test your endpoints (replace with your URL)
python test_apis.py --candidate-url http://localhost:3000

# Example expected output:
# ✅ Health check passed
# ✅ Transaction endpoint working
# ✅ Balance endpoint working
# ✅ Data accuracy: 98.5%
# 📊 Score: 87/100
```

---

## 📤 Submission Guidelines

### What to Include

1. **Source Code**: Complete, runnable application
2. **Documentation**: 
   - `README.md` with setup/run instructions
   - Code comments explaining key decisions
   - Database schema documentation
3. **Configuration**:
   - `Dockerfile` and/or `docker-compose.yml`
   - Dependency files (requirements.txt, package.json, etc.)
4. **Testing**: Any unit tests or integration tests you've written

### What NOT to Include
- Node modules, Python `__pycache__`, build artifacts
- IDE configuration files
- Large log files or temporary data

### Final Checklist

Before submission, ensure:
- [ ] `docker compose up -d` starts your application
- [ ] Both required endpoints respond correctly
- [ ] Your `README.md` explains how to run and test your solution
- [ ] Code is clean and well-commented
- [ ] You've tested with the provided validation script

---

## 🆘 Troubleshooting

### Common Issues

**Database Connection Problems**
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check database connectivity
docker exec -it coding-test-postgres psql -U test_user -d coding_test
```

**API Not Responding**
```bash
# Check API server status
curl http://localhost:8000/health

# View API logs
docker compose logs transaction-api
```

**Performance Issues**
- The data API includes realistic delays - this is intentional
- Focus on efficient data processing rather than API speed
- Consider batch processing strategies

### Need Help?

If you encounter setup issues:
1. Check that Docker and Docker Compose are installed
2. Ensure ports 5432 and 8000 are available
3. Try `docker compose down && docker compose up -d`

---

## 🎯 Final Notes

This test simulates real-world challenges we face at Shuffle Finance. We're looking for:

- **Problem-solving skills**: How you approach complex data processing challenges
- **Engineering judgment**: Sensible trade-offs between accuracy, performance, and code complexity
- **Production readiness**: Code that's maintainable and robust

**Remember**: Perfect is the enemy of good. Focus on delivering a working solution that handles the core requirements well, rather than trying to solve every edge case.

Good luck! 🚀

---

*Questions? Check the provided documentation in the `docs/` directory or examine the sample responses in `docs/sample-responses.json`.* 