# Synthetic Analytics datasets

These JSON files contain fictional security-test data only. Every file is kept under 100 lines so the fixtures stay light and readable.

`expected-results.json` is the executable manifest used by the integration tests. It records the accepted risk levels, expected finding types, minimum finding count, tampering expectation, and data categories for every sample.

The log fixtures intentionally place sensitive-shaped values in the middle or at the end of the record list so the scanner and structural sampler cannot rely on the first characters of a document. `sample-10-finding-at-end.json` keeps its only finding in the last record on purpose; if you add records to it, the finding must stay last.
