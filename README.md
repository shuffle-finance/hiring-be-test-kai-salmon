# Backend Developer Coding Test - Transaction Processing System

## 📋 For Candidates

**👋 Welcome to your coding test!** This repository contains everything you need to complete the Shuffle Finance backend developer assessment.

### 🚀 Quick Start

```bash
# 1. Verify your environment setup
./verify_setup.sh

# 2. Read the complete test briefing
open CODING_TEST_BRIEFING.md

# 3. Start coding in candidate-solution/
cd candidate-solution/
```

### 📖 **[READ THE FULL BRIEFING HERE →](CODING_TEST_BRIEFING.md)**

The `CODING_TEST_BRIEFING.md` file contains everything you need:
- ✅ Complete test requirements and API specifications
- ✅ Step-by-step setup and development guide
- ✅ Success criteria and scoring rubric
- ✅ Technical tips and troubleshooting help
- ✅ Submission guidelines and checklist

**⏱️ Time Allocation: 2-2.5 hours**

---

## 🎯 What You're Building

A transaction processing system that:

1. **Consumes** transaction data from the provided API (`http://localhost:8000`)
2. **Processes** messy real-world data (duplicates, state transitions, inconsistencies)
3. **Stores** clean data in PostgreSQL (schema design is up to you)
4. **Exposes** two REST endpoints:
   - `GET /users/{userId}/transactions` - All final transactions for a user
   - `GET /users/{userId}/balance` - Current account balance

## 🔧 Environment Overview

This repository provides:

- **PostgreSQL Database**: Available at `localhost:5432` for your use
- **Transaction Data API**: Serves anonymized banking data at `http://localhost:8000`
- **Validation Tools**: Automated testing to verify your implementation
- **Documentation**: Complete API specs and examples in `docs/`

## 📁 Repository Structure

```
├── CODING_TEST_BRIEFING.md     # 📖 Complete test instructions (START HERE)
├── docker-compose.yml          # Environment setup
├── candidate-solution/         # 👈 Your work goes here
│   ├── README.md              # Starter guidance
│   └── (your solution files)
├── docs/                      # API documentation
│   ├── api-spec.md            # Detailed API documentation
│   └── sample-responses.json  # Example response formats
├── validation/                # Testing tools
│   ├── test_apis.py          # Automated validation script
│   └── requirements.txt      # Validation dependencies
└── (infrastructure files)    # Database, transaction API, etc.
```

## ✅ Success Criteria Summary

- **Functional Requirements (60%)**: Both endpoints work correctly
- **Code Quality (25%)**: Clean, maintainable, well-documented code
- **System Design (15%)**: Sensible architecture and database design

## 🧪 Testing Your Solution

```bash
# Test your endpoints with our validation script
cd validation
pip install -r requirements.txt
python test_apis.py --candidate-url http://localhost:3000
```

## 💡 Quick Tips

1. **Start Simple**: Get basic functionality working first
2. **Handle Duplicates**: Multiple transactions may represent the same real transaction
3. **State Transitions**: `pending` transactions may become `booked`
4. **Database Design**: You have full control over the schema
5. **Use Any Language**: Choose what you're most comfortable with

## 🆘 Troubleshooting

**Environment Issues?**
```bash
# Reset the environment
docker compose down && docker compose up -d

# Check service status
docker compose ps
```

**Need Help?**
- Check the detailed troubleshooting section in `CODING_TEST_BRIEFING.md`
- Examine the API documentation in `docs/`
- Look at sample responses in `docs/sample-responses.json`

---

**Good luck with your coding test! 🚀**

*This test simulates real-world transaction processing challenges similar to those faced at Shuffle Finance. Focus on practical problem-solving, clean code, and delivering a working solution within the time limit.* 