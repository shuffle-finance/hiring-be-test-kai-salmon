import express from 'express';
import { getAccountBalance, getUnproccessedAccountTransactions, mapAccountTransactionsResponse, Transaction, TransactionStatus } from './transactions';

interface TransactionFormat {
  id: string;
  amount: number;
  currency: string;
  date?: string | undefined;
  description?: string | undefined;
  status: TransactionStatus;
  type: string;
}

interface TransactionsFormat {
    user_id: string;
    transactions: TransactionFormat[];
    count: number;
}
interface BalanceFormat {
    user_id: string;
    balance: number;
    currency: string;
    transaction_count: number;
    last_updated: string;
}

const app = express()
const port = 3000

function formatTransaction(transaction: Transaction): TransactionFormat {
    return {
        id: transaction.transactionId || transaction.internalTransactionId || '?', //TODO fix this
        amount: Number(transaction.transactionAmount.amount_cents) / 100, // Convert cents to pounds
        currency: transaction.transactionAmount.currency,
        date: transaction.valueDate.toISOString().split('T')[0], 
        description: transaction.remittanceInformationUnstructured,
        status: transaction.status,
        type: "card_payment" // TODO: figure out how to determine the type
    };
}

// #### 1. **GET /users/{userId}/transactions**
app.get('/users/:userId/transactions', async (req, res) => {
    const userId = req.params.userId;
    const response = await getUnproccessedAccountTransactions(userId);
    const transactions = mapAccountTransactionsResponse(response);

    const formattedTransactions: TransactionsFormat = {
    user_id: userId,
    transactions: transactions.map(tx => formatTransaction(tx)),
    count: transactions.length
    };

    res.json(formattedTransactions);
});

app.get('/users/:userId/transactions/:transactionId', async (req, res) => {
  const userId = req.params.userId;
    const transactionId = req.params.transactionId;
    const response = await getUnproccessedAccountTransactions(userId);
    const transactions = mapAccountTransactionsResponse(response);
    const filtered = transactions.filter(tx => tx.transactionId === transactionId);
    const formattedTransactions: TransactionsFormat = {
    user_id: userId,
    transactions: filtered
        .map(tx => formatTransaction(tx)),
    count: filtered.length
    };

    res.json(formattedTransactions);
});

// #### 2. **GET /users/{userId}/balance**
/* Return the current balance for a user (sum of all final transactions).

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
*/
app.get('/users/:userId/balance', async (req, res) => {
    const userId = req.params.userId;
    const response = await getUnproccessedAccountTransactions(userId);
    const transactions = mapAccountTransactionsResponse(response);
    const balance = getAccountBalance(transactions);
    const balanceFormat: BalanceFormat = {
        user_id: userId,
        balance: Number(balance) / 100, // Convert cents to pounds
        currency: 'GBP', // Assuming all transactions are in GBP
        transaction_count: Object.keys(transactions).length,
        last_updated: new Date().toISOString()
    };
    res.json(balanceFormat);
});

// Health
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})

