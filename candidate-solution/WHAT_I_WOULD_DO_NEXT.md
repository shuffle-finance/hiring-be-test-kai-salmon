
# Things that I would do next, were I to spend another few hours on this assignment

  

## Optimize the correctness `areTransactionsFuzzyMatch` using an iterate test driven approach

Currently the settings `areTransactionsFuzzyMatch` (The threshold, the impact of the amount, and the keys used) were all arbitrarily chosen using exactly one example `transactionId`. As `transactionId` was not used within `areTransactionsFuzzyMatch`, I could tweak the values until my singular test transaction became deduplicated. 

This, however, is not very elegant or reliable. To configure this to maximize correctness, I would scour the existing data by hand to find examples of 1) non-identical transaction pairs which should be matched, and 2) similar but clearly distinct transaction pairs. With my true-positives and false-positives in hand, I could create a large test suite which I could then tweak by-hand these values to maximize passing tests. (One could even imagine a more elaborate implementation where these values are tuned programatically)


## Replace the array of transactions with a data-structure which groups in such a way that transactions which _might_ need deduplicating are grouped together
Currently, as the server processes the transaction responses, it builds up an array of processed entries, and linearly searches for any previously seen which are a fuzzy match. This means that the fuzzyMatch get executed for every pair of transactions. 

Imagine it was decided that if two transactions happen on different dates that *cannot* be duplicates, no matter how similar they are. If we replace the array with a simple object which groups transactions by date, say:
```
{ 
	"2025-01-01": [{...}, ...],  
	"2025-02-01": [{...}, ...], 
	... 
}
```
We would then only need to linearly search for fuzzy matches within the same group, dramatically reducing the amount of calls to the relatively expensive fuzzy match logic.

If it was decided that there are multiple properties which are 1) are always present and 2) are always shared between transactions that need deduplicating, then we could replace the key with a SHA256 of all the field values concatenated. 

## Improve performance with store data in a persistent database 

As discussed in the interview, the purpose of the database in this assignment is not to facilitate logic -- as the bank is the source of truth -- but to act as persistent cache to improve performance and data reliability. I would store the incoming transactions into a database, and then when I'm fetching new data I would instead of continuing to fetch new pages until there are no more, I would stop as soon as I reach a transaction date which is before the latest value in the database. 

The optimisation described above in _"Replace the array of transactions with a data-structure which groups in such a way that transactions which _might_ need deduplicating are grouped together"_ would still hold for processing the new incoming pieces of data, but it is analogous to having indexes in the database. 

## Restructure the code for improved navigation and maintainability 
Like many an interview assignment, the codes organisation leaves something to be desired. Were I to spend time refactoring it for organisation, I would create something like:
```
candidate_solution```
├── src
│    ├── data_sources
│    │    └── open_banking
│    │         ├── open_banking_types.ts // Containts the type definitions of the data shape that comes back from the external data source, as well as the mapping logic to convert it to the types defined in `../../logic/app_types.ts`
│    │         └── open_banking.ts // Handles the actual logic of fetching the data, and calling the mappers in `./open_banking_types.ts`
│    ├── logic
│    │    ├── app_types.ts // Contains type definitions for the internal types used throughout the server
│    │    ├── fuzzy_match.ts // All the data related to fuzzy matching, imports the `./app_types.ts` and no other internal dependencies
│    │    └── transactions.ts // Calls `../data_sources/open_banking/...` to fetch data, performs the buisness logic on it
│    └── api
│         ├── express.ts // Calls `../logic/...` and maps it using `./api_types.ts` 
│         └── api_types.ts // Contains the type defs for the API, and logic to convert to them from the app_types
└── index.ts // Calls api_express.ts, along with any other misc setup 
```
Note that:
*  `index.ts` only imports from `api/**`, 
* `api/**`only imports from `logic/**`
* `logic/**` only imports from `data_sources/*/**` 
* `data_sources/*/**` only imports **types**, but not methods, from `logic/**` 

This creates a clear separation between logic which handles in-bound communication, out-bound communication, and core business logic. 