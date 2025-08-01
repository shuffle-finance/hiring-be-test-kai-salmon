import { sha512 } from 'js-sha512';

type Result<T> = {
    data: T;
    error: undefined
} | {
    data: undefined;
    error: Error;
}

interface TransactionResponse {
    additionalInformation: string;
    bookingDate: string;
    entryReference: string;
    internalTransactionId?: string;
    proprietaryBankTransactionCode: string;
    remittanceInformationUnstructured: string;
    creditorName?: string;
    debtorName?: string;
    transactionAmount: {
        amount: string;
        currency: string;
    };
    transactionId?: string;
    valueDate: string;
}

interface TransactionResponsePayload {
    metadata: {
        accountId: string;
        createdAt: string;
        requisitionId: string;
        traceId: string;
    };
    payload: {
        booked?: TransactionResponse[];
        pending?: TransactionResponse[];
    }
}
interface AccountTransactionsResponse {
    account_id: string;
    pagination: {
        has_next: boolean;
        has_prev: boolean;
        page: number;
        per_page: number;
        total_count: number;
        total_pages: number;
    };
    timestamp: string;
    transactions: TransactionResponsePayload[];
}

function getShuffleId(TransactionResponse: TransactionResponse): string {
    const merchant = TransactionResponse.creditorName || TransactionResponse.debtorName || 'Unknown Merchant';
    return sha512(`${TransactionResponse.transactionAmount.amount}::${TransactionResponse.valueDate}::${merchant}`);
}

async function getAccountTransactionsPage(
    accountId: string,
    page: number = 1,
    perPage: number = 10
): Promise<AccountTransactionsResponse> {
    const response = await fetch(`http://localhost:8000/accounts/${accountId}/transactions?page=${page}&per_page=${perPage}`);

    if (!response.ok) {
        throw new Error(`Error fetching transactions: ${response.statusText}`);
    }
    
    const data: AccountTransactionsResponse = await response.json();
    
    return data;
}
type TransactionResponseWithTimestampAndStatus = TransactionResponse & { timestamp: Date, status: TransactionStatus };
type getAccountTransactionsResult = {
    transactions: TransactionResponseWithTimestampAndStatus[];
}
export async function getUnproccessedAccountTransactions(accountId: string): Promise<getAccountTransactionsResult> {
    const pageSize = 10;
    let currentPage = 1;
    let hasNextPage = true;
    const transactions: TransactionResponseWithTimestampAndStatus[] = [];
    while (hasNextPage) {
        const response = await getAccountTransactionsPage(accountId, currentPage, pageSize);
        const timestamp = new Date(response.timestamp);
        for (const transactionPayload of response.transactions) {
            const { booked, pending } = transactionPayload.payload;
            if (booked) {
                transactions.push(...booked.map(tx => {
                    const result: TransactionResponseWithTimestampAndStatus = {
                        ...tx,
                        timestamp,
                        status: 'booked'
                    };
                    return result;
                }));
            }
            if (pending) {
                transactions.push(...pending.map(tx => {
                    const result: TransactionResponseWithTimestampAndStatus = {
                        ...tx,
                        timestamp,
                        status: 'pending'
                    };
                    return result;
                }));
            }
        }
        currentPage++;
        hasNextPage = response.pagination.has_next;
    }
    return {
        transactions
    }
}

export type TransactionStatus = 'pending' | 'booked';
export interface Transaction {
    shuffleId: string;

    additionalInformation: string;
    bookingDate: Date;
    entryReference: string;
    internalTransactionId?: string | undefined;
    proprietaryBankTransactionCode: string;
    remittanceInformationUnstructured: string;
    transactionAmount: {
        amount: number;
        currency: string;
    };
    transactionId?: string | undefined;
    valueDate: Date;
    status: TransactionStatus;
    timestamp: Date; 
}
type AccountTransactions = Record<string, Transaction>; // Maps shuffleId to Transaction


export function mapTransactionResponseToTransaction(response: TransactionResponseWithTimestampAndStatus): Result<Transaction> {
    const tx: Transaction = {
        shuffleId: getShuffleId(response),
        additionalInformation: response.additionalInformation,
        bookingDate: new Date(response.bookingDate),
        entryReference: response.entryReference,
        internalTransactionId: response.internalTransactionId,
        proprietaryBankTransactionCode: response.proprietaryBankTransactionCode,
        remittanceInformationUnstructured: response.remittanceInformationUnstructured,
        transactionAmount: {
            amount: parseFloat(response.transactionAmount.amount),
            currency: response.transactionAmount.currency
        },
        transactionId: response.transactionId,
        valueDate: new Date(response.valueDate),
        timestamp: response.timestamp,
        status: response.status
    };
    if (!tx.internalTransactionId) {
        return { error: new Error('Internal transaction ID is missing'), data: undefined };
    }
    if (isNaN(tx.transactionAmount.amount)) {
        return { error: new Error('Transaction amount is not a valid number'), data: undefined };
    }
    if (isNaN(tx.bookingDate.getTime()) || isNaN(tx.valueDate.getTime()) || isNaN(tx.timestamp.getTime())) {
        return { error: new Error('Invalid date in transaction'), data: undefined };
    }
    if (tx.transactionAmount.currency != 'GBP') {
        return { error: new Error('Transaction currency is not GBP, if we want '), data: undefined };
    }
    return { data: tx, error: undefined };
}

export function mapAccountTransactionsResponse(response: getAccountTransactionsResult): AccountTransactions {
    const transactions: AccountTransactions = {};
    for (const tx of response.transactions) {
        const {data: transaction, error} = mapTransactionResponseToTransaction(tx);
        if (error) {
            continue; // Skip this transaction if there's an error
        }
        const existingTransaction = transactions[transaction.shuffleId];
        const reconsiledTransaction = existingTransaction ? reconcileTransactions(existingTransaction, transaction) : transaction;
        transactions[transaction.shuffleId] = reconsiledTransaction;
    }
    return transactions;
}

function reconcileTransactions(existing: Transaction, incoming: Transaction): Transaction {
    if (existing.status === 'booked' && incoming.status === 'pending') {
        return existing; // Keep the booked transaction
    }
    if (existing.status === 'pending' && incoming.status === 'booked') {
          return incoming; // Update to the booked transaction
    }
    if (existing.timestamp.getTime() < incoming.timestamp.getTime()) {
        return incoming; 
    }else {
        return existing; 
    }
}

export function getAccountBalance(accountTransactions: AccountTransactions): number {
    return Object.values(accountTransactions).reduce((balance, transaction) => {
        if (transaction.status === 'booked') {
            return balance + transaction.transactionAmount.amount;
        }
        return balance;
    }, 0);
}

// (async () => {
//     try {
//         const accountId = '04b3efb2-c8b1-1073-9d16-153585326359'; 
//         const {transactions} = await getUnproccessedAccountTransactions(accountId);
//         const accountTransactions = mapAccountTransactionsResponse({ transactions });
//         console.log('accountTransactions:', accountTransactions);
//     } catch (error) {
//         console.error('Error fetching transactions:', error);
//     }
// })();

