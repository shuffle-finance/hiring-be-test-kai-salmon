import { distance } from 'fastest-levenshtein';

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
    description?: string;
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

    additionalInformation: string;
    bookingDate: Date;
    entryReference: string;
    internalTransactionId?: string | undefined;
    proprietaryBankTransactionCode: string;
    remittanceInformationUnstructured: string;
    transactionAmount: {
        amount_cents: bigint;
        currency: string;
    };
    transactionId?: string | undefined;
    valueDate: Date;
    creditorName?: string;
    debtorName?: string;
    status: TransactionStatus;
    timestamp: Date; 
    description: string | undefined;
}
type AccountTransactions = Transaction[]


export function mapTransactionResponseToTransaction(response: TransactionResponseWithTimestampAndStatus): Result<Transaction> {
    let amount_cents: bigint;
    try {
        const amount = parseFloat(response.transactionAmount.amount) * 100
        amount_cents = BigInt(Math.round(amount));
    }catch(e){
        return { error: new Error('Transaction amount is not a valid number'), data: undefined}
    }
    
    const tx: Transaction = {
        additionalInformation: response.additionalInformation,
        bookingDate: new Date(response.bookingDate),
        entryReference: response.entryReference,
        internalTransactionId: response.internalTransactionId,
        proprietaryBankTransactionCode: response.proprietaryBankTransactionCode,
        remittanceInformationUnstructured: response.remittanceInformationUnstructured,
        transactionAmount: {
            amount_cents,
            currency: response.transactionAmount.currency
        },
        transactionId: response.transactionId,
        valueDate: new Date(response.valueDate),
        timestamp: response.timestamp,
        status: response.status,
        description: response.description ?? undefined,
    };
    if (!tx.internalTransactionId) {
        return { error: new Error('Internal transaction ID is missing'), data: undefined };
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
    const transactions: AccountTransactions = [];
    for (const tx of response.transactions) {
        const {data: transaction, error} = mapTransactionResponseToTransaction(tx);
        if (error) {
            continue; // Skip this transaction if there's an error
        }
        const existingTransaction = transactions.find(tx => areTransactionsFuzzyMatch(tx, transaction));
        const reconsiledTransaction = existingTransaction ? reconcileTransactions(existingTransaction, transaction) : transaction;
        transactions.push(reconsiledTransaction);
    }
    return transactions;
}

type KeysMatching<T, V> = {[K in keyof T]-?: T[K] extends V ? K : never}[keyof T];

function areTransactionsFuzzyMatch(tx1: Transaction, tx2: Transaction): boolean {
    const SIMILARITY_THRESHOLD = 1000; 
    const AMOUNT_DIST_WEIGHT = 0.1; // Distance for each cent difference
    const keysToCompare: KeysMatching<Transaction, string|undefined>[] = [
        'additionalInformation',
        'entryReference',
        'internalTransactionId',
        'proprietaryBankTransactionCode',
        'remittanceInformationUnstructured',
        'transactionId',
        'description',
        'creditorName',
        'debtorName'
    ];
    let totalDistance = Math.abs(Number(tx1.transactionAmount.amount_cents - tx2.transactionAmount.amount_cents)) * AMOUNT_DIST_WEIGHT;
    for (const key of keysToCompare) {
        const value1 = tx1[key];
        const value2 = tx2[key];
        if(!value1 || !value2) {
            continue; 
        }
        const dist = distance(value1, value2);
        totalDistance += dist;
    }

    return totalDistance < SIMILARITY_THRESHOLD;
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

export function getAccountBalance(accountTransactions: AccountTransactions): BigInt {
    return Object.values(accountTransactions).reduce((balance, transaction) => {
        if (transaction.status === 'booked') {
            return balance + transaction.transactionAmount.amount_cents;
        }
        return balance;
    }, 0n);
}
