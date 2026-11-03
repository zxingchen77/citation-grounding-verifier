# Gold review workbook: real-docs-v3

Status: **AI-drafted; human author review pending** for every case.
Check each atomic claim, label and complete evidence before signing off.
Source-only semantics: a true fact absent from the supplied context is UNSUPPORTED.
Do not revise labels to fit model outputs. Corrections after test require a new version.

## sqlite-isolation (test; multi_passage)

Human review: [ ] accepted  [ ] correction needed

A WAL reader refreshes its snapshot as soon as another connection commits. If that reader then tries the documented read-to-write upgrade against the newer database, it encounters SQLITE_BUSY_SNAPSHOT; ending the stale transaction and starting another lets it retry. SQLite automatically retries this error after 100 milliseconds.

### Passage 0: [source](https://www.sqlite.org/isolation.html)

WAL mode permits simultaneous readers and writers. It can do this because changes do not overwrite the original database file, but rather go into the separate write-ahead log file. That means that readers can continue to read the old, original, unaltered content from the original database file at the same time that the writer is appending to the write-ahead log. In WAL mode, SQLite exhibits "snapshot isolation". When a read transaction starts, that reader continues to see an unchanging "snapshot" of the database file as it existed at the moment in time when the read transaction started. Any write transactions that commit while the read transaction is active are still invisible to the read transaction, because the reader is seeing a snapshot of database file from a prior moment in time.

### Passage 1: [source](https://www.sqlite.org/isolation.html)

Another example: X starts a read transaction using BEGIN and SELECT, then Y makes a changes to the database using UPDATE. Then X tries to make a change to the database using UPDATE. The attempt by X to escalate its transaction from a read transaction to a write transaction fails with an SQLITE_BUSY_SNAPSHOT error because the snapshot of the database being viewed by X is no longer the latest version of the database. If X were allowed to write, it would fork the history of the database file, which is something SQLite does not support. In order for X to write to the database, it must first release its snapshot (using ROLLBACK for example) then start a new transaction with a subsequent BEGIN.

### Passage 2: [source](https://www.sqlite.org/isolation.html)

Since version 3.7.0 (2010-07-21), SQLite also supports "WAL mode". In WAL mode, changes are not written to the original database file. Instead, changes go into a separate "write-ahead log" or "WAL" file. Later, after the transaction commits, those changes will be moved from the WAL file back into the original database in an operation called "checkpoint". WAL mode is enabled by running "PRAGMA journal_mode=WAL".

- **0 CONTRADICTED**: A WAL reader refreshes its snapshot as soon as another connection commits.
  Reason: A live WAL read transaction keeps its old snapshot despite concurrent commits.
  Evidence [0]: Any write transactions that commit while the read transaction is active are still invisible to the read transaction, because the reader is seeing a snapshot of database file from a prior moment in time.
- **1 SUPPORTED**: In WAL mode, the documented read-to-write upgrade against a newer database encounters SQLITE_BUSY_SNAPSHOT.
  Reason: The WAL snapshot description supplies the mode and the separate upgrade example supplies the error.
  Evidence [0]: In WAL mode, SQLite exhibits "snapshot isolation".
  Evidence [1]: The attempt by X to escalate its transaction from a read transaction to a write transaction fails with an SQLITE_BUSY_SNAPSHOT error because the snapshot of the database being viewed by X is no longer the latest version of the database.
- **2 SUPPORTED**: The stale reader can retry writing by ending its transaction and starting another.
  Reason: The upgrade example explicitly requires releasing the snapshot and beginning again.
  Evidence [1]: In order for X to write to the database, it must first release its snapshot (using ROLLBACK for example) then start a new transaction with a subsequent BEGIN.
- **3 UNSUPPORTED**: SQLite automatically retries SQLITE_BUSY_SNAPSHOT after 100 milliseconds.
  Reason: No retry interval or automatic retry is specified.

Reviewer notes: ____________________

## sqlite-wal (dev; distortion)

Human review: [ ] accepted  [ ] correction needed

With the default WAL policy, the automatic checkpoint starts at 1,001 pages, although an application may choose another threshold. A checkpoint can coexist with readers and continue past every active reader's end mark, then resume from its recorded progress on the next invocation.

### Passage 0: [source](https://www.sqlite.org/wal.html)

By default, SQLite does a checkpoint automatically when the WAL file reaches a threshold size of 1000 pages. (The SQLITE_DEFAULT_WAL_AUTOCHECKPOINT compile-time option can be used to specify a different default.) Applications using WAL do not have to do anything in order for these checkpoints to occur. But if they want to, applications can adjust the automatic checkpoint threshold. Or they can turn off the automatic checkpoints and run checkpoints during idle moments or in a separate thread or process.

### Passage 1: [source](https://www.sqlite.org/wal.html)

A checkpoint operation takes content from the WAL file and transfers it back into the original database file. A checkpoint can run concurrently with readers, however the checkpoint must stop when it reaches a page in the WAL that is past the end mark of any current reader. The checkpoint has to stop at that point because otherwise it might overwrite part of the database file that the reader is actively using. The checkpoint remembers (in the wal-index) how far it got and will resume transferring content from the WAL to the database from where it left off on the next invocation.

### Passage 2: [source](https://www.sqlite.org/wal.html)

Unlike the other journaling modes, PRAGMA journal_mode=WAL is persistent. If a process sets WAL mode, then closes and reopens the database, the database will come back in WAL mode. In contrast, if a process sets (for example) PRAGMA journal_mode=TRUNCATE and then closes and reopens the database will come back up in the default rollback mode of DELETE rather than the previous TRUNCATE setting.

- **0 CONTRADICTED**: The default WAL automatic checkpoint threshold is 1,001 pages.
  Reason: The stated default is 1000 pages, not 1001.
  Evidence [0]: By default, SQLite does a checkpoint automatically when the WAL file reaches a threshold size of 1000 pages.
- **1 SUPPORTED**: An application may choose a different automatic checkpoint threshold.
  Reason: The application can adjust the threshold.
  Evidence [0]: But if they want to, applications can adjust the automatic checkpoint threshold.
- **2 SUPPORTED**: A checkpoint can coexist with readers.
  Reason: Concurrent checkpointing and reading are explicitly allowed.
  Evidence [1]: A checkpoint can run concurrently with readers
- **3 CONTRADICTED**: A checkpoint can continue past every active reader's end mark.
  Reason: It must stop at a page beyond the end mark of any current reader.
  Evidence [1]: A checkpoint can run concurrently with readers, however the checkpoint must stop when it reaches a page in the WAL that is past the end mark of any current reader.
- **4 SUPPORTED**: A checkpoint resumes from its recorded progress on the next invocation.
  Reason: Its progress is retained in the wal-index.
  Evidence [1]: The checkpoint remembers (in the wal-index) how far it got and will resume transferring content from the WAL to the database from where it left off on the next invocation.

Reviewer notes: ____________________

## sqlite-foreignkeys (dev; multi_passage)

Human review: [ ] accepted  [ ] correction needed

For a normally compiled connection whose foreign keys are still at the documented default, issuing the enable pragma in the middle of a multi-statement transaction leaves enforcement disabled. That attempt raises an error, and enabling enforcement on one connection later switches it on for every other connection too.

### Passage 0: [source](https://www.sqlite.org/foreignkeys.html)

Foreign key constraints are disabled by default (for backwards compatibility), so must be enabled separately for each database connection. (Note, however, that future releases of SQLite might change so that foreign key constraints enabled by default. Careful developers will not make any assumptions about whether or not foreign keys are enabled by default but will instead enable or disable them as necessary.) The application can also use a PRAGMA foreign_keys statement to determine if foreign keys are currently enabled. The following command-line session demonstrates this:

### Passage 1: [source](https://www.sqlite.org/foreignkeys.html)

It is not possible to enable or disable foreign key constraints in the middle of a multi-statement transaction (when SQLite is not in autocommit mode). Attempting to do so does not return an error; it simply has no effect.

Usually, the parent key of a foreign key constraint is the primary key of the parent table. If they are not the primary key, then the parent key columns must be collectively subject to a UNIQUE constraint or have a UNIQUE index. If the parent key columns have a UNIQUE index, then that index must use the collation sequences that are specified in the CREATE TABLE statement for the parent table. For example,

### Passage 2: [source](https://www.sqlite.org/foreignkeys.html)

In order to use foreign key constraints in SQLite, the library must be compiled with neither SQLITE_OMIT_FOREIGN_KEY nor SQLITE_OMIT_TRIGGER defined. If SQLITE_OMIT_TRIGGER is defined but SQLITE_OMIT_FOREIGN_KEY is not, then SQLite behaves as it did prior to version 3.6.19 (2009-10-14) - foreign key definitions are parsed and may be queried using PRAGMA foreign_key_list, but foreign key constraints are not enforced. The PRAGMA foreign_keys command is a no-op in this configuration. If OMIT_FOREIGN_KEY is defined, then foreign key definitions cannot even be parsed (attempting to specify a foreign key definition is a syntax error).

- **0 SUPPORTED**: For a normally compiled connection at the documented default, enabling foreign keys mid-transaction leaves enforcement disabled.
  Reason: Combine the disabled default with the separate rule that changing it mid-transaction has no effect.
  Evidence [0]: Foreign key constraints are disabled by default (for backwards compatibility), so must be enabled separately for each database connection.
  Evidence [1]: It is not possible to enable or disable foreign key constraints in the middle of a multi-statement transaction (when SQLite is not in autocommit mode).
  Evidence [1]: Attempting to do so does not return an error; it simply has no effect.
- **1 CONTRADICTED**: Attempting to enable foreign keys mid-transaction raises an error.
  Reason: The attempted change does not return an error.
  Evidence [1]: Attempting to do so does not return an error; it simply has no effect.
- **2 CONTRADICTED**: Enabling foreign-key enforcement on one connection enables it on every other connection.
  Reason: Enforcement must be enabled separately for each connection.
  Evidence [0]: Foreign key constraints are disabled by default (for backwards compatibility), so must be enabled separately for each database connection.

Reviewer notes: ____________________

## sqlite-lang_conflict (test; supported)

Human review: [ ] accepted  [ ] correction needed

When an applicable UPDATE violation occurs on its hundredth attempted row under FAIL, the earlier 99 changes survive and processing does not reach later rows. ABORT instead undoes changes from that statement while retaining work from earlier statements in the same still-active transaction.

### Passage 0: [source](https://www.sqlite.org/lang_conflict.html)

When an applicable constraint violation occurs, the ABORT resolution algorithm aborts the current SQL statement with an SQLITE_CONSTRAINT error and backs out any changes made by the current SQL statement; but changes caused by prior SQL statements within the same transaction are preserved and the transaction remains active. This is the default behavior and the behavior specified by the SQL standard.

### Passage 1: [source](https://www.sqlite.org/lang_conflict.html)

When an applicable constraint violation occurs, the FAIL resolution algorithm aborts the current SQL statement with an SQLITE_CONSTRAINT error. But the FAIL resolution does not back out prior changes of the SQL statement that failed nor does it end the transaction. For example, if an UPDATE statement encountered a constraint violation on the 100th row that it attempts to update, then the first 99 row changes are preserved but changes to rows 100 and beyond never occur.

### Passage 2: [source](https://www.sqlite.org/lang_conflict.html)

When an applicable constraint violation occurs, the IGNORE resolution algorithm skips the one row that contains the constraint violation and continues processing subsequent rows of the SQL statement as if nothing went wrong. Other rows before and after the row that contained the constraint violation are inserted or updated normally. No error is returned for uniqueness, NOT NULL, and UNIQUE constraint errors when the IGNORE conflict resolution algorithm is used. However, the IGNORE conflict resolution algorithm works like ABORT for foreign key constraint errors.

- **0 SUPPORTED**: Under FAIL, an applicable UPDATE violation on the hundredth attempted row preserves the earlier 99 changes.
  Reason: The documented example retains changes on rows 1 through 99.
  Evidence [1]: For example, if an UPDATE statement encountered a constraint violation on the 100th row that it attempts to update, then the first 99 row changes are preserved but changes to rows 100 and beyond never occur.
- **1 SUPPORTED**: Under FAIL, processing does not reach rows after the hundredth-row violation.
  Reason: The same example says changes to rows 100 and beyond never occur.
  Evidence [1]: For example, if an UPDATE statement encountered a constraint violation on the 100th row that it attempts to update, then the first 99 row changes are preserved but changes to rows 100 and beyond never occur.
- **2 SUPPORTED**: ABORT undoes changes made by the statement that encounters the violation.
  Reason: ABORT backs out current-statement changes.
  Evidence [0]: When an applicable constraint violation occurs, the ABORT resolution algorithm aborts the current SQL statement with an SQLITE_CONSTRAINT error and backs out any changes made by the current SQL statement; but changes caused by prior SQL statements within the same transaction are preserved and the transaction remains active.
- **3 SUPPORTED**: ABORT retains changes from earlier statements in the transaction.
  Reason: Prior-statement changes are preserved.
  Evidence [0]: When an applicable constraint violation occurs, the ABORT resolution algorithm aborts the current SQL statement with an SQLITE_CONSTRAINT error and backs out any changes made by the current SQL statement; but changes caused by prior SQL statements within the same transaction are preserved and the transaction remains active.
- **4 SUPPORTED**: ABORT leaves the transaction active.
  Reason: The transaction remains active after the current statement is backed out.
  Evidence [0]: When an applicable constraint violation occurs, the ABORT resolution algorithm aborts the current SQL statement with an SQLITE_CONSTRAINT error and backs out any changes made by the current SQL statement; but changes caused by prior SQL statements within the same transaction are preserved and the transaction remains active.

Reviewer notes: ____________________

## sqlite-autoinc (test; distortion)

Human review: [ ] accepted  [ ] correction needed

An AUTOINCREMENT key never reuses a value from a rolled-back transaction and always advances by exactly one. In an empty table the first automatic key is 1; once the greatest possible ROWID has already been inserted, further inserts fail with SQLITE_FULL.

### Passage 0: [source](https://www.sqlite.org/autoinc.html)

If a column has the type INTEGER PRIMARY KEY AUTOINCREMENT then a slightly different ROWID selection algorithm is used. The ROWID chosen for the new row is at least one larger than the largest ROWID that has ever before existed in that same table. If the table has never before contained any data, then a ROWID of 1 is used. If the largest possible ROWID has previously been inserted, then new INSERTs are not allowed and any attempt to insert a new row will fail with an SQLITE_FULL error. Only ROWID values from previous transactions that were committed are considered. ROWID values that were rolled back are ignored and can be reused.

### Passage 1: [source](https://www.sqlite.org/autoinc.html)

Note that "monotonically increasing" does not imply that the ROWID always increases by exactly one. One is the usual increment. However, if an insert fails due to (for example) a uniqueness constraint, the ROWID of the failed insertion attempt might not be reused on subsequent inserts, resulting in gaps in the ROWID sequence. AUTOINCREMENT guarantees that automatically chosen ROWIDs will be increasing but not that they will be sequential.

### Passage 2: [source](https://www.sqlite.org/autoinc.html)

SQLite keeps track of the largest ROWID using an internal table named "sqlite_sequence". The sqlite_sequence table is created automatically, if it does not already exist, whenever a normal table that contains an AUTOINCREMENT column is created. A row in the sqlite_sequence table corresponding to the table with the AUTOINCREMENT column is created the first time the AUTOINCREMENT table is written and updated on any subsequent writes that increase the maximum rowid. The content of the sqlite_sequence table can be modified using ordinary UPDATE, INSERT, and DELETE statements. But making modifications to this table will likely perturb the AUTOINCREMENT key generation algorithm. Make sure you know what you are doing before you undertake such changes. The sqlite_sequence table does not track ROWID changes associated with UPDATE statement, only INSERT statements.

- **0 CONTRADICTED**: An AUTOINCREMENT key never reuses a value from a rolled-back transaction.
  Reason: Rolled-back ROWIDs are ignored and can be reused.
  Evidence [0]: ROWID values that were rolled back are ignored and can be reused.
- **1 CONTRADICTED**: AUTOINCREMENT always advances the automatically chosen ROWID by exactly one.
  Reason: Monotonicity does not imply a gapless sequence.
  Evidence [1]: Note that "monotonically increasing" does not imply that the ROWID always increases by exactly one.
- **2 SUPPORTED**: An empty AUTOINCREMENT table receives 1 as its first automatic ROWID.
  Reason: The empty-table starting value is explicit.
  Evidence [0]: If the table has never before contained any data, then a ROWID of 1 is used.
- **3 SUPPORTED**: After the greatest possible ROWID has been inserted, further AUTOINCREMENT inserts fail with SQLITE_FULL.
  Reason: This failure condition is explicitly stated.
  Evidence [0]: If the largest possible ROWID has previously been inserted, then new INSERTs are not allowed and any attempt to insert a new row will fail with an SQLITE_FULL error.

Reviewer notes: ____________________

## sqlite-datatype3 (dev; supported)

Human review: [ ] accepted  [ ] correction needed

A NUMERIC-affinity column stores the text 3.0e+5 as an integer representing three hundred thousand. An explicit cast of 4.0 to INT yields integer 4, whereas casting that value to NUMERIC leaves it floating-point; for ordinary column storage, INTEGER and NUMERIC affinities otherwise behave alike.

### Passage 0: [source](https://www.sqlite.org/datatype3.html)

A string might look like a floating-point literal with a decimal point and/or exponent notation but as long as the value can be expressed as an integer, the NUMERIC affinity will convert it into an integer. Hence, the string '3.0e+5' is stored in a column with NUMERIC affinity as the integer 300000, not as the floating point value 300000.0.

### Passage 1: [source](https://www.sqlite.org/datatype3.html)

A column that uses INTEGER affinity behaves the same as a column with NUMERIC affinity. The difference between INTEGER and NUMERIC affinity is only evident in a CAST expression: The expression "CAST(4.0 AS INT)" returns an integer 4, whereas "CAST(4.0 AS NUMERIC)" leaves the value as a floating-point 4.0.

### Passage 2: [source](https://www.sqlite.org/datatype3.html)

A column with REAL affinity behaves like a column with NUMERIC affinity except that it forces integer values into floating point representation. (As an internal optimization, small floating point values with no fractional component and stored in columns with REAL affinity are written to disk as integers in order to take up less space and are automatically converted back into floating point as the value is read out. This optimization is completely invisible at the SQL level and can only be detected by examining the raw bits of the database file.)

- **0 SUPPORTED**: A NUMERIC-affinity column stores the text '3.0e+5' as integer 300000.
  Reason: The decimal/exponent notation does not prevent exact integer storage.
  Evidence [0]: Hence, the string '3.0e+5' is stored in a column with NUMERIC affinity as the integer 300000, not as the floating point value 300000.0.
- **1 SUPPORTED**: CAST(4.0 AS INT) returns integer 4.
  Reason: The source contrasts the two explicit casts.
  Evidence [1]: The difference between INTEGER and NUMERIC affinity is only evident in a CAST expression: The expression "CAST(4.0 AS INT)" returns an integer 4, whereas "CAST(4.0 AS NUMERIC)" leaves the value as a floating-point 4.0.
- **2 SUPPORTED**: CAST(4.0 AS NUMERIC) leaves a floating-point 4.0.
  Reason: The explicit NUMERIC cast retains the floating representation.
  Evidence [1]: The difference between INTEGER and NUMERIC affinity is only evident in a CAST expression: The expression "CAST(4.0 AS INT)" returns an integer 4, whereas "CAST(4.0 AS NUMERIC)" leaves the value as a floating-point 4.0.
- **3 SUPPORTED**: INTEGER and NUMERIC column affinities otherwise behave alike.
  Reason: The documented distinction is only evident in CAST.
  Evidence [1]: A column that uses INTEGER affinity behaves the same as a column with NUMERIC affinity.
  Evidence [1]: The difference between INTEGER and NUMERIC affinity is only evident in a CAST expression: The expression "CAST(4.0 AS INT)" returns an integer 4, whereas "CAST(4.0 AS NUMERIC)" leaves the value as a floating-point 4.0.

Reviewer notes: ____________________

## sqlite-partialindex (dev; extrinsic)

Human review: [ ] accepted  [ ] correction needed

To use a partial index, the query predicate must imply the index predicate. In practice the documented matching rule does not treat b=3+3 as a substitute for b=6, despite their mathematical equivalence. SQLite itself is dedicated to the public domain.

### Passage 0: [source](https://www.sqlite.org/partialindex.html)

Let X be the expression in the WHERE clause of a partial index, and let W be the WHERE clause of a query that uses the table that is indexed. Then, the query is permitted to use the partial index if W⇒X, where the ⇒ operator (usually pronounced "implies") is the logic operator equivalent to "X or not W". Hence, determining whether or not a partial index is usable in a particular query reduces to proving a theorem in first-order logic.

### Passage 1: [source](https://www.sqlite.org/partialindex.html)

The terms in W and X must match exactly. SQLite does not do algebra to try to get them to look the same. The term "b=6" does not match "b=3+3" or "b-6=0" or "b BETWEEN 6 AND 6". "b=6" will match to "6=b" as long as "b=6" is on the index and "6=b" is in the query. If a term of the form "6=b" appears in the index, it will never match anything.

### Passage 2: [source](https://www.sqlite.org/partialindex.html)

Database files that contain partial indices are not readable or writable by versions of SQLite prior to 3.8.0. However, a database file created by SQLite 3.8.0 is still readable and writable by prior versions as long as its schema contains no partial indexes. A database that is unreadable by legacy versions of SQLite can be made readable simply by running DROP INDEX on the partial indexes.

- **0 SUPPORTED**: A query predicate must imply the partial-index predicate for that index to be usable.
  Reason: W is the query predicate and X is the index predicate; the required direction is W implies X.
  Evidence [0]: Let X be the expression in the WHERE clause of a partial index, and let W be the WHERE clause of a query that uses the table that is indexed.
  Evidence [0]: Then, the query is permitted to use the partial index if W⇒X, where the ⇒ operator (usually pronounced "implies") is the logic operator equivalent to "X or not W".
- **1 SUPPORTED**: The documented partial-index matching rule does not treat b=3+3 as a substitute for b=6.
  Reason: The planner explicitly does not algebraically equate these terms.
  Evidence [1]: The term "b=6" does not match "b=3+3" or "b-6=0" or "b BETWEEN 6 AND 6".
- **2 SUPPORTED**: b=3+3 and b=6 are mathematically equivalent.
  Reason: The two cited expressions differ syntactically but 3+3 equals 6. The declared semantics permit arithmetic; the answer explicitly asserts this equivalence.
  Evidence [1]: The term "b=6" does not match "b=3+3" or "b-6=0" or "b BETWEEN 6 AND 6".
- **3 UNSUPPORTED**: SQLite is dedicated to the public domain.
  Reason: True in the separately recorded SQLite copyright source, but none of these retrieval passages states its license.

Reviewer notes: ____________________

## sqlite-expridx (dev; distortion)

Human review: [ ] accepted  [ ] correction needed

An expression index on x+y also matches a predicate written as y+x, because the planner rewrites algebraically equivalent expressions. Even changing only whitespace would stop a match. The documented matching rule applies in ORDER BY as well as WHERE.

### Passage 0: [source](https://www.sqlite.org/expridx.html)

The SQLite query planner will consider using an index on an expression when the expression that is indexed appears in the WHERE clause or in the ORDER BY clause of a query, exactly as it is written in the CREATE INDEX statement. The query planner does not do algebra. In order to match WHERE clause constraints and ORDER BY terms to indexes, SQLite requires that the expressions be the same, except for minor syntactic differences such as white-space changes. So if you have:

### Passage 1: [source](https://www.sqlite.org/expridx.html)

Then the index will not be used because the expression on the CREATE INDEX statement (x+y) is not the same as the expression as it appears in the query (y+x). The two expressions might be mathematically equivalent, but the SQLite query planner insists that they be the same, not merely equivalent. Consider rewriting the query thusly:

### Passage 2: [source](https://www.sqlite.org/expridx.html)

Expressions in CREATE INDEX statements may contain function calls, but only to functions whose output is always determined completely by its input parameters (a.k.a.: deterministic functions). Obviously, functions like random() will not work well in an index. But also functions like sqlite_version(), though they are constant across any one database connection, are not constant across the life of the underlying database file, and hence may not be used in a CREATE INDEX statement. Note that application-defined SQL functions are by default considered non-deterministic and may not be used in a CREATE INDEX statement unless the SQLITE_DETERMINISTIC flag is used when the function is registered.

- **0 CONTRADICTED**: An expression index on x+y matches a predicate written as y+x.
  Reason: The reordered expression is specifically excluded from matching.
  Evidence [1]: Then the index will not be used because the expression on the CREATE INDEX statement (x+y) is not the same as the expression as it appears in the query (y+x).
- **1 CONTRADICTED**: The planner rewrites algebraically equivalent expressions to match an expression index.
  Reason: It requires the same expression rather than mathematical equivalence.
  Evidence [0]: The query planner does not do algebra.
  Evidence [1]: The two expressions might be mathematically equivalent, but the SQLite query planner insists that they be the same, not merely equivalent.
- **2 CONTRADICTED**: Changing only whitespace stops an expression-index match.
  Reason: Whitespace is an allowed minor syntactic difference.
  Evidence [0]: In order to match WHERE clause constraints and ORDER BY terms to indexes, SQLite requires that the expressions be the same, except for minor syntactic differences such as white-space changes.
- **3 SUPPORTED**: Expression-index matching applies to ORDER BY as well as WHERE.
  Reason: Both clauses are named in the applicability rule.
  Evidence [0]: The SQLite query planner will consider using an index on an expression when the expression that is indexed appears in the WHERE clause or in the ORDER BY clause of a query, exactly as it is written in the CREATE INDEX statement.

Reviewer notes: ____________________

## sqlite-deterministic (dev; extrinsic)

Human review: [ ] accepted  [ ] correction needed

The no-argument datetime() call behaves like a current-time request; the oversight allowing it in deterministic-only schema expressions was fixed on March 17, 2021 in version 3.35.2. Calls using the utc modifier are non-deterministic. SQLite also offers rigid type enforcement through STRICT tables introduced in 3.37.0.

### Passage 0: [source](https://www.sqlite.org/deterministic.html)

The built-in date and time functions of SQLite are a special case. These functions are usually considered deterministic. However, if these functions use the string "now" as the date, or if they use the localtime modifier or the utc modifier, then they are considered non-deterministic. Because the function inputs are not necessarily known until run-time, the date/time functions will throw an exception if they encounter any of the non-deterministic features in a context where only deterministic functions are allowed.

### Passage 1: [source](https://www.sqlite.org/deterministic.html)

When the enhancement was made to SQLite 3.20.0 such that date/time functions would be considered deterministic as they do not depend on the current time, one case was overlooked: Many of the date/time functions can be called with no arguments at all. These no-argument date/time functions behave as if they had a single "'now'" argument. Thus "datetime()" and "datetime('now')" both yield the current date and time. However, only the second form was recognized as non-deterministic. This meant that developers could sneak the non-deterministic "datetime()" form into CHECK constraints, index expressions, generated column expressions, and similar places where non-deterministic functions make no sense. This oversight was fixed in version 3.35.2 (2021-03-17). However, there may be legacy databases in circulation that were created by SQLite version 3.20.0 through 3.35.1 that have non-deterministic date/time functions in their schemas.

### Passage 2: [source](https://www.sqlite.org/deterministic.html)

In the cases above, the values returned by the function affects the information stored in the database file. The values of functions in CHECK constraints determines which entries are valid for a table, and functions in the WHERE clause of a partial index or in an index on an expression compute values stored in the index b-tree. If any of these functions later returns a different value, then the database might no longer be well-formed. Hence, to avoid database corruption, only deterministic functions can be used in the contexts above.

- **0 SUPPORTED**: A no-argument datetime() call behaves like a current-time request.
  Reason: The no-argument form acts as if supplied now.
  Evidence [1]: These no-argument date/time functions behave as if they had a single "'now'" argument.
- **1 SUPPORTED**: The datetime() deterministic-schema oversight was fixed on March 17, 2021 in SQLite 3.35.2.
  Reason: The version and date are explicitly given together.
  Evidence [1]: This oversight was fixed in version 3.35.2 (2021-03-17).
- **2 SUPPORTED**: A SQLite date/time call using the utc modifier is non-deterministic.
  Reason: The modifier is explicitly included among the non-deterministic features.
  Evidence [0]: However, if these functions use the string "now" as the date, or if they use the localtime modifier or the utc modifier, then they are considered non-deterministic.
- **3 UNSUPPORTED**: SQLite offers rigid type enforcement through STRICT tables introduced in 3.37.0.
  Reason: This is documented on the separate datatype page, not in these retrieved passages.

Reviewer notes: ____________________

## sqlite-lang_with (dev; multi_passage)

Human review: [ ] accepted  [ ] correction needed

With OFFSET 5 and LIMIT 10 in the recursive construction, the five skipped rows consume half of the ten-row quota. They are nevertheless processed by the recursive SELECT. A negative limit allows an unbounded row count, and NOT MATERIALIZED still leaves materialization available to the planner.

### Passage 0: [source](https://www.sqlite.org/lang_with.html)

The LIMIT clause, if present, determines the maximum number of rows that will ever be added to the recursive table in step 2b. Once the limit is reached, the recursion stops. A limit of zero means that no rows are ever added to the recursive table, and a negative limit means an unlimited number of rows may be added to the recursive table.

### Passage 1: [source](https://www.sqlite.org/lang_with.html)

The OFFSET clause, if it is present and has a positive value N, prevents the first N rows from being added to the recursive table. The first N rows are still processed by the recursive-select — they just are not added to the recursive table. Rows are not counted toward fulfilling the LIMIT until all OFFSET rows have been skipped.

### Passage 2: [source](https://www.sqlite.org/lang_with.html)

If the NOT MATERIALIZED phrase is used, then select-stmt is substituted as a subquery in place of every occurrence of the CTE table name. Optimizations such as flattening and push-down are then applied to the subquery as if the subquery had been used indirectly. In spite of its name, the NOT MATERIALIZED phrase does not prohibit the use of materialization. The query planner is still free to implement the subquery using materialization if it feels that is the best solution. The true meaning of NOT MATERIALIZED is closer to "TREAT LIKE ANY ORDINARY VIEW OR SUBQUERY".

### Passage 3: [source](https://www.sqlite.org/lang_with.html)

Common Table Expressions or CTEs act like temporary views that exist only for the duration of a single SQL statement. There are two kinds of common table expressions: "ordinary" and "recursive". Ordinary common table expressions are helpful for making queries easier to understand by factoring subqueries out of the main SQL statement. Recursive common table expressions provide the ability to do hierarchical or recursive queries of trees and graphs, a capability that is not otherwise available in the SQL language.

- **0 CONTRADICTED**: With OFFSET 5 and LIMIT 10, the five skipped recursive rows consume half of the ten-row quota.
  Reason: LIMIT bounds rows added; OFFSET rows are processed but do not count toward that limit.
  Evidence [0]: The LIMIT clause, if present, determines the maximum number of rows that will ever be added to the recursive table in step 2b.
  Evidence [1]: Rows are not counted toward fulfilling the LIMIT until all OFFSET rows have been skipped.
- **1 SUPPORTED**: Rows skipped by OFFSET are still processed by the recursive SELECT.
  Reason: Processing and insertion into the recursive table are explicitly distinguished.
  Evidence [1]: The first N rows are still processed by the recursive-select — they just are not added to the recursive table.
- **2 SUPPORTED**: A negative recursive LIMIT allows an unbounded row count.
  Reason: The negative-limit case explicitly permits an unlimited number of rows.
  Evidence [0]: A limit of zero means that no rows are ever added to the recursive table, and a negative limit means an unlimited number of rows may be added to the recursive table.
- **3 SUPPORTED**: NOT MATERIALIZED leaves materialization available to the planner.
  Reason: The spelling is not a prohibition.
  Evidence [2]: In spite of its name, the NOT MATERIALIZED phrase does not prohibit the use of materialization.
  Evidence [2]: The query planner is still free to implement the subquery using materialization if it feels that is the best solution.

Reviewer notes: ____________________

## sqlite-limits (dev; supported)

Human review: [ ] accepted  [ ] correction needed

For versions after 3.32.0, the default host-parameter-number ceiling is 32,766; numbering sparsely does not avoid allocating the intervening slots. SQLite page sizes range from 512 through 65,536 bytes in powers of two. At the largest page size, the documented database-size ceiling is roughly 256 tebibytes rather than 256 decimal terabytes.

### Passage 0: [source](https://www.sqlite.org/limits.html)

SQLite allocates space to hold all host parameters between 1 and the largest host parameter number used. Hence, an SQL statement that contains a host parameter like ?1000000000 would require gigabytes of storage. This could easily overwhelm the resources of the host machine. To prevent excessive memory allocations, the maximum value of a host parameter number is SQLITE_MAX_VARIABLE_NUMBER, which defaults to 999 for SQLite versions prior to 3.32.0 (2020-05-22) or 32766 for SQLite versions after 3.32.0.

### Passage 1: [source](https://www.sqlite.org/limits.html)

Every database consists of one or more "pages". Within a single database, every page is the same size, but different databases can have page sizes that are powers of two between 512 and 65536, inclusive. The maximum size of a database file is 4294967294 pages. At the maximum page size of 65536 bytes, this translates into a maximum database size of approximately 2.8e+14 bytes (281 terabytes, or 256 tebibytes, or 281474 gigabytes, or 262143 gibibytes).

### Passage 2: [source](https://www.sqlite.org/limits.html)

The maximum depth of an expression tree can be lowered at run-time using the sqlite3_limit(db,SQLITE_LIMIT_EXPR_DEPTH,size) interface if the SQLITE_MAX_EXPR_DEPTH is initially positive. In other words, the maximum expression depth can be lowered at run-time if there is already a compile-time limit on the expression depth. If SQLITE_MAX_EXPR_DEPTH is set to 0 at compile time (if the depth of expressions is unlimited) then the sqlite3_limit(db,SQLITE_LIMIT_EXPR_DEPTH,size) is a no-op.

- **0 SUPPORTED**: After SQLite 3.32.0, the default host-parameter-number ceiling is 32766.
  Reason: The version-qualified default is given explicitly.
  Evidence [0]: To prevent excessive memory allocations, the maximum value of a host parameter number is SQLITE_MAX_VARIABLE_NUMBER, which defaults to 999 for SQLite versions prior to 3.32.0 (2020-05-22) or 32766 for SQLite versions after 3.32.0.
- **1 SUPPORTED**: Sparse host-parameter numbering still allocates the intervening slots.
  Reason: Allocation includes every parameter between 1 and the highest number.
  Evidence [0]: SQLite allocates space to hold all host parameters between 1 and the largest host parameter number used.
- **2 SUPPORTED**: SQLite page sizes range from 512 through 65536 bytes in powers of two.
  Reason: Both endpoints are inclusive.
  Evidence [1]: Within a single database, every page is the same size, but different databases can have page sizes that are powers of two between 512 and 65536, inclusive.
- **3 SUPPORTED**: At the largest page size, the database-size ceiling is roughly 256 tebibytes, not 256 decimal terabytes.
  Reason: The source equates the maximum to 256 TiB and approximately 281 TB, not 256 TB.
  Evidence [1]: At the maximum page size of 65536 bytes, this translates into a maximum database size of approximately 2.8e+14 bytes (281 terabytes, or 256 tebibytes, or 281474 gigabytes, or 262143 gibibytes).

Reviewer notes: ____________________

## sqlite-withoutrowid (test; extrinsic)

Human review: [ ] accepted  [ ] correction needed

In a WITHOUT ROWID table, INTEGER PRIMARY KEY gives the key integer affinity rather than a rowid alias, and inserting into that table leaves sqlite3_last_insert_rowid() unchanged. SQLite first gained WAL mode in version 3.7.0 on July 21, 2010.

### Passage 0: [source](https://www.sqlite.org/withoutrowid.html)

The special behaviors associated with "INTEGER PRIMARY KEY" do not apply on WITHOUT ROWID tables. In an ordinary table, "INTEGER PRIMARY KEY" means that the column is an alias for the rowid. But since there is no rowid in a WITHOUT ROWID table, that special meaning no longer applies. An "INTEGER PRIMARY KEY" column in a WITHOUT ROWID table works like an "INT PRIMARY KEY" column in an ordinary table: It is a PRIMARY KEY that has integer affinity.

### Passage 1: [source](https://www.sqlite.org/withoutrowid.html)

The sqlite3_last_insert_rowid() function does not work for WITHOUT ROWID tables. Inserts into a WITHOUT ROWID do not change the value returned by the sqlite3_last_insert_rowid() function. The last_insert_rowid() SQL function is also unaffected since it is just a wrapper around sqlite3_last_insert_rowid().

### Passage 2: [source](https://www.sqlite.org/withoutrowid.html)

WITHOUT ROWID tables work best when individual rows are not too large. A good rule-of-thumb is that the average size of a single row in a WITHOUT ROWID table should be less than about 1/20th the size of a database page. That means that rows should not contain more than about 50 bytes each for a 1KiB page size or about 200 bytes each for 4KiB page size. WITHOUT ROWID tables will work (in the sense that they get the correct answer) for arbitrarily large rows - up to 2GB in size - but traditional rowid tables tend to work faster for large row sizes. This is because rowid tables are implemented as B*-Trees where all content is stored in the leaves of the tree, whereas WITHOUT ROWID tables are implemented using ordinary B-Trees with content stored on both leaves and intermediate nodes. Storing content in intermediate nodes causes each intermediate node entry to take up more space on the page and thus reduces the fan-out, increasing the search cost.

- **0 SUPPORTED**: In a WITHOUT ROWID table, INTEGER PRIMARY KEY gives the key integer affinity.
  Reason: The special alias behavior is absent while integer affinity remains.
  Evidence [0]: But since there is no rowid in a WITHOUT ROWID table, that special meaning no longer applies.
  Evidence [0]: An "INTEGER PRIMARY KEY" column in a WITHOUT ROWID table works like an "INT PRIMARY KEY" column in an ordinary table: It is a PRIMARY KEY that has integer affinity.
- **1 SUPPORTED**: In a WITHOUT ROWID table, INTEGER PRIMARY KEY is not a rowid alias.
  Reason: The special alias behavior is absent while integer affinity remains.
  Evidence [0]: But since there is no rowid in a WITHOUT ROWID table, that special meaning no longer applies.
  Evidence [0]: An "INTEGER PRIMARY KEY" column in a WITHOUT ROWID table works like an "INT PRIMARY KEY" column in an ordinary table: It is a PRIMARY KEY that has integer affinity.
- **2 SUPPORTED**: Inserting into a WITHOUT ROWID table leaves sqlite3_last_insert_rowid() unchanged.
  Reason: The rowid-returning API is unaffected by such inserts.
  Evidence [1]: Inserts into a WITHOUT ROWID do not change the value returned by the sqlite3_last_insert_rowid() function.
- **3 UNSUPPORTED**: SQLite first gained WAL mode in version 3.7.0 on July 21, 2010.
  Reason: The historical release fact is present on the isolation page, not in this retrieval context.

Reviewer notes: ____________________

## postgres-transaction-iso (dev; supported)

Human review: [ ] accepted  [ ] correction needed

Two ordinary SELECTs in a Read Committed transaction can disagree after a concurrent commit. Repeatable Read instead fixes its snapshot at the first non-control statement, although it still sees earlier writes from its own transaction. That stronger snapshot rule does not eliminate serialization anomalies.

### Passage 0: [source](https://www.postgresql.org/docs/18/transaction-iso.html)

Read Committed is the default isolation level in PostgreSQL. When a transaction uses this isolation level, a SELECT query (without a FOR UPDATE/SHARE clause) sees only data committed before the query began; it never sees either uncommitted data or changes committed by concurrent transactions during the query's execution. In effect, a SELECT query sees a snapshot of the database as of the instant the query begins to run. However, SELECT does see the effects of previous updates executed within its own transaction, even though they are not yet committed. Also note that two successive SELECT commands can see different data, even though they are within a single transaction, if other transactions commit changes after the first SELECT starts and before the second SELECT starts.

### Passage 1: [source](https://www.postgresql.org/docs/18/transaction-iso.html)

The Repeatable Read isolation level only sees data committed before the transaction began; it never sees either uncommitted data or changes committed by concurrent transactions during the transaction's execution. (However, each query does see the effects of previous updates executed within its own transaction, even though they are not yet committed.) This is a stronger guarantee than is required by the SQL standard for this isolation level, and prevents all of the phenomena described in Table 13.1 except for serialization anomalies. As mentioned above, this is specifically allowed by the standard, which only describes the minimum protections each isolation level must provide.

This level is different from Read Committed in that a query in a repeatable read transaction sees a snapshot as of the start of the first non-transaction-control statement in the transaction, not as of the start of the current statement within the transaction. Thus, successive SELECT commands within a single transaction see the same data, i.e., they do not see changes made by other transactions that committed after their own transaction started.

### Passage 2: [source](https://www.postgresql.org/docs/18/transaction-iso.html)

In PostgreSQL, you can request any of the four standard transaction isolation levels, but internally only three distinct isolation levels are implemented, i.e., PostgreSQL's Read Uncommitted mode behaves like Read Committed. This is because it is the only sensible way to map the standard isolation levels to PostgreSQL's multiversion concurrency control architecture.

- **0 SUPPORTED**: Two ordinary SELECTs in a Read Committed transaction can disagree after a concurrent commit.
  Reason: Each statement gets a new snapshot; the explicit two-SELECT example permits different data.
  Evidence [0]: Also note that two successive SELECT commands can see different data, even though they are within a single transaction, if other transactions commit changes after the first SELECT starts and before the second SELECT starts.
- **1 SUPPORTED**: Repeatable Read fixes its snapshot at the first non-transaction-control statement.
  Reason: The first statement rather than the current statement anchors the snapshot.
  Evidence [1]: This level is different from Read Committed in that a query in a repeatable read transaction sees a snapshot as of the start of the first non-transaction-control statement in the transaction, not as of the start of the current statement within the transaction.
- **2 SUPPORTED**: Repeatable Read sees earlier writes from its own transaction.
  Reason: Own writes remain visible despite the fixed snapshot.
  Evidence [1]: (However, each query does see the effects of previous updates executed within its own transaction, even though they are not yet committed.) This is a stronger guarantee than is required by the SQL standard for this isolation level, and prevents all of the phenomena described in Table 13.1 except for serialization anomalies.
- **3 SUPPORTED**: Repeatable Read has a stronger snapshot rule than Read Committed.
  Reason: The answer calls it a stronger rule; the supplied descriptions contrast per-command snapshots with a stable transaction snapshot.
  Evidence [0]: Also note that two successive SELECT commands can see different data, even though they are within a single transaction, if other transactions commit changes after the first SELECT starts and before the second SELECT starts.
  Evidence [1]: This level is different from Read Committed in that a query in a repeatable read transaction sees a snapshot as of the start of the first non-transaction-control statement in the transaction, not as of the start of the current statement within the transaction.
- **4 SUPPORTED**: Repeatable Read does not eliminate serialization anomalies.
  Reason: The stronger level prevents the listed phenomena except serialization anomalies.
  Evidence [1]: (However, each query does see the effects of previous updates executed within its own transaction, even though they are not yet committed.) This is a stronger guarantee than is required by the SQL standard for this isolation level, and prevents all of the phenomena described in Table 13.1 except for serialization anomalies.

Reviewer notes: ____________________

## postgres-explicit-locking (test; multi_passage)

Human review: [ ] accepted  [ ] correction needed

If FOR UPDATE is acquired after a savepoint, rolling back to that point releases the acquired lock without waiting for the outer transaction to finish. Nevertheless, even under Repeatable Read, a waiting FOR UPDATE always returns the updated row rather than raising an error when that row changed since the transaction began.

### Passage 0: [source](https://www.postgresql.org/docs/18/explicit-locking.html)

Once acquired, a lock is normally held until the end of the transaction. But if a lock is acquired after establishing a savepoint, the lock is released immediately if the savepoint is rolled back to. This is consistent with the principle that ROLLBACK cancels all effects of the commands since the savepoint. The same holds for locks acquired within a PL/pgSQL exception block: an error escape from the block releases locks acquired within it.

### Passage 1: [source](https://www.postgresql.org/docs/18/explicit-locking.html)

FOR UPDATE causes the rows retrieved by the SELECT statement to be locked as though for update. This prevents them from being locked, modified or deleted by other transactions until the current transaction ends. That is, other transactions that attempt UPDATE, DELETE, SELECT FOR UPDATE, SELECT FOR NO KEY UPDATE, SELECT FOR SHARE or SELECT FOR KEY SHARE of these rows will be blocked until the current transaction ends; conversely, SELECT FOR UPDATE will wait for a concurrent transaction that has run any of those commands on the same row, and will then lock and return the updated row (or no row, if the row was deleted). Within a REPEATABLE READ or SERIALIZABLE transaction, however, an error will be thrown if a row to be locked has changed since the transaction started. For further discussion see Section 13.4.

### Passage 2: [source](https://www.postgresql.org/docs/18/explicit-locking.html)

The use of explicit locking can increase the likelihood of deadlocks, wherein two (or more) transactions each hold locks that the other wants. For example, if transaction 1 acquires an exclusive lock on table A and then tries to acquire an exclusive lock on table B, while transaction 2 has already exclusive-locked table B and now wants an exclusive lock on table A, then neither one can proceed. PostgreSQL automatically detects deadlock situations and resolves them by aborting one of the transactions involved, allowing the other(s) to complete. (Exactly which transaction will be aborted is difficult to predict and should not be relied upon.)

- **0 SUPPORTED**: Rolling back a savepoint releases a FOR UPDATE lock acquired after it without waiting for the outer transaction to finish.
  Reason: Combine FOR UPDATE acquiring row locks with the savepoint release exception.
  Evidence [1]: FOR UPDATE causes the rows retrieved by the SELECT statement to be locked as though for update.
  Evidence [0]: But if a lock is acquired after establishing a savepoint, the lock is released immediately if the savepoint is rolled back to.
- **1 CONTRADICTED**: Under Repeatable Read, a waiting FOR UPDATE always returns the updated row rather than raising an error when the row changed since the transaction began.
  Reason: The general updated-row rule has an explicit Repeatable Read/Serializable exception.
  Evidence [1]: Within a REPEATABLE READ or SERIALIZABLE transaction, however, an error will be thrown if a row to be locked has changed since the transaction started.

Reviewer notes: ____________________

## postgres-ddl-constraints (test; distortion)

Human review: [ ] accepted  [ ] correction needed

A CHECK accepts a row only when its expression is true, so a positivity CHECK also guarantees non-null input. Ordinary UNIQUE treats two nulls as equal by default; NULLS NOT DISTINCT changes that default behavior.

### Passage 0: [source](https://www.postgresql.org/docs/18/ddl-constraints.html)

It should be noted that a check constraint is satisfied if the check expression evaluates to true or the null value. Since most expressions will evaluate to the null value if any operand is null, they will not prevent null values in the constrained columns. To ensure that a column does not contain null values, the not-null constraint described in the next section can be used.

### Passage 1: [source](https://www.postgresql.org/docs/18/ddl-constraints.html)

In general, a unique constraint is violated if there is more than one row in the table where the values of all of the columns included in the constraint are equal. By default, two null values are not considered equal in this comparison. That means even in the presence of a unique constraint it is possible to store duplicate rows that contain a null value in at least one of the constrained columns. This behavior can be changed by adding the clause NULLS NOT DISTINCT, like

The default behavior can be specified explicitly using NULLS DISTINCT. The default null treatment in unique constraints is implementation-defined according to the SQL standard, and other implementations have a different behavior. So be careful when developing applications that are intended to be portable.

### Passage 2: [source](https://www.postgresql.org/docs/18/ddl-constraints.html)

The default ON DELETE action is ON DELETE NO ACTION; this does not need to be specified. This means that the deletion in the referenced table is allowed to proceed. But the foreign-key constraint is still required to be satisfied, so this operation will usually result in an error. But checking of foreign-key constraints can also be deferred to later in the transaction (not covered in this chapter). In that case, the NO ACTION setting would allow other commands to “fix” the situation before the constraint is checked, for example by inserting another suitable row into the referenced table or by deleting the now-dangling rows from the referencing table.

- **0 CONTRADICTED**: A CHECK accepts a row only when its expression is true.
  Reason: Truth is sufficient but not necessary: NULL also satisfies the CHECK, refuting the reversed condition.
  Evidence [0]: It should be noted that a check constraint is satisfied if the check expression evaluates to true or the null value.
- **1 CONTRADICTED**: A positivity CHECK guarantees non-null input.
  Reason: CHECK expressions do not prevent null values; a separate NOT NULL is needed.
  Evidence [0]: Since most expressions will evaluate to the null value if any operand is null, they will not prevent null values in the constrained columns.
- **2 CONTRADICTED**: Ordinary UNIQUE treats two nulls as equal by default.
  Reason: The default explicitly does not consider them equal.
  Evidence [1]: By default, two null values are not considered equal in this comparison.
- **3 SUPPORTED**: NULLS NOT DISTINCT changes the default treatment of nulls in a unique constraint.
  Reason: The clause changes the null-distinctness default.
  Evidence [1]: By default, two null values are not considered equal in this comparison.
  Evidence [1]: This behavior can be changed by adding the clause NULLS NOT DISTINCT, like

The default behavior can be specified explicitly using NULLS DISTINCT.

Reviewer notes: ____________________

## postgres-indexes-partial (dev; extrinsic)

Human review: [ ] accepted  [ ] correction needed

A partial index contains only rows satisfying its predicate. Planning can recognize that x < 1 implies x < 2, but a parameterized x < ? is insufficient to establish that bound for every possible parameter. PostgreSQL also makes Read Uncommitted behave like Read Committed.

### Passage 0: [source](https://www.postgresql.org/docs/18/indexes-partial.html)

A partial index is an index built over a subset of a table; the subset is defined by a conditional expression (called the predicate of the partial index). The index contains entries only for those table rows that satisfy the predicate. Partial indexes are a specialized feature, but there are several situations in which they are useful.

### Passage 1: [source](https://www.postgresql.org/docs/18/indexes-partial.html)

The system can recognize simple inequality implications, for example “x < 1” implies “x < 2”; otherwise the predicate condition must exactly match part of the query's WHERE condition or the index will not be recognized as usable. Matching takes place at query planning time, not at run time. As a result, parameterized query clauses do not work with a partial index. For example a prepared query with a parameter might specify “x < ?” which will never imply “x < 2” for all possible values of the parameter.

### Passage 2: [source](https://www.postgresql.org/docs/18/indexes-partial.html)

(Put the category column first, for the reasons described in Section 11.3.) While a search in this larger index might have to descend through a couple more tree levels than a search in a smaller index, that's almost certainly going to be cheaper than the planner effort needed to select the appropriate one of the partial indexes. The core of the problem is that the system does not understand the relationship among the partial indexes, and will laboriously test each one to see if it's applicable to the current query.

- **0 SUPPORTED**: A partial index contains only rows satisfying its predicate.
  Reason: The subset definition is explicit.
  Evidence [0]: The index contains entries only for those table rows that satisfy the predicate.
- **1 SUPPORTED**: Planning can recognize that x < 1 implies x < 2.
  Reason: This inequality implication is the documented example.
  Evidence [1]: The system can recognize simple inequality implications, for example “x < 1” implies “x < 2”; otherwise the predicate condition must exactly match part of the query's WHERE condition or the index will not be recognized as usable.
  Evidence [1]: Matching takes place at query planning time, not at run time.
- **2 SUPPORTED**: A parameterized x < ? cannot establish x < 2 for every possible parameter.
  Reason: A prepared parameter does not prove the implication for all values.
  Evidence [1]: For example a prepared query with a parameter might specify “x < ?” which will never imply “x < 2” for all possible values of the parameter.
- **3 UNSUPPORTED**: PostgreSQL makes Read Uncommitted behave like Read Committed.
  Reason: True on the separate isolation-level page, absent from this context.

Reviewer notes: ____________________

## postgres-indexes-index-only-scans (test; supported)

Human review: [ ] accepted  [ ] correction needed

B-tree can supply index-only scans, whereas support in GiST and SP-GiST depends on the operator class and GIN lacks it. For an otherwise eligible scan, a set all-visible bit avoids a heap visit; without that bit the heap entry still has to be checked.

### Passage 0: [source](https://www.postgresql.org/docs/18/indexes-index-only-scans.html)

The index type must support index-only scans. B-tree indexes always do. GiST and SP-GiST indexes support index-only scans for some operator classes but not others. Other index types have no support. The underlying requirement is that the index must physically store, or else be able to reconstruct, the original data value for each index entry. As a counterexample, GIN indexes cannot support index-only scans because each index entry typically holds only part of the original data value.

### Passage 1: [source](https://www.postgresql.org/docs/18/indexes-index-only-scans.html)

However, for seldom-changing data there is a way around this problem. PostgreSQL tracks, for each page in a table's heap, whether all rows stored in that page are old enough to be visible to all current and future transactions. This information is stored in a bit in the table's visibility map. An index-only scan, after finding a candidate index entry, checks the visibility map bit for the corresponding heap page. If it's set, the row is known visible and so the data can be returned with no further work. If it's not set, the heap entry must be visited to find out whether it's visible, so no performance advantage is gained over a standard index scan.

### Passage 2: [source](https://www.postgresql.org/docs/18/indexes-index-only-scans.html)

Suffix truncation always removes non-key columns from upper B-Tree levels. As payload columns, they are never used to guide index scans. The truncation process also removes one or more trailing key column(s) when the remaining prefix of key column(s) happens to be sufficient to describe tuples on the lowest B-Tree level. In practice, covering indexes without an INCLUDE clause often avoid storing columns that are effectively payload in the upper levels. However, explicitly defining payload columns as non-key columns reliably keeps the tuples in upper levels small.

- **0 SUPPORTED**: B-tree supports index-only scans.
  Reason: B-tree always supports the capability.
  Evidence [0]: B-tree indexes always do.
- **1 SUPPORTED**: GiST and SP-GiST index-only-scan support depends on the operator class.
  Reason: Some operator classes support it and others do not.
  Evidence [0]: GiST and SP-GiST indexes support index-only scans for some operator classes but not others.
- **2 SUPPORTED**: GIN does not support index-only scans.
  Reason: GIN cannot reconstruct the whole original value.
  Evidence [0]: As a counterexample, GIN indexes cannot support index-only scans because each index entry typically holds only part of the original data value.
- **3 SUPPORTED**: For an otherwise eligible index-only scan, a set all-visible bit avoids a heap visit.
  Reason: The visibility-map check can prove the candidate visible without heap access.
  Evidence [1]: An index-only scan, after finding a candidate index entry, checks the visibility map bit for the corresponding heap page.
  Evidence [1]: If it's set, the row is known visible and so the data can be returned with no further work.
- **4 SUPPORTED**: Without the all-visible bit, an index-only scan must check the heap entry.
  Reason: Unset bits force a heap visibility check.
  Evidence [1]: If it's not set, the heap entry must be visited to find out whether it's visible, so no performance advantage is gained over a standard index scan.

Reviewer notes: ____________________

## postgres-wal-async-commit (dev; multi_passage)

Human review: [ ] accepted  [ ] correction needed

An asynchronous success response can precede durable WAL, so a crash after that response can still lose the acknowledged transaction. Recovery replays commits in order; therefore, if B depended on earlier A, it can retain B while losing A. This mode risks lost transactions rather than corruption.

### Passage 0: [source](https://www.postgresql.org/docs/18/wal-async-commit.html)

As described in the previous section, transaction commit is normally synchronous: the server waits for the transaction's WAL records to be flushed to permanent storage before returning a success indication to the client. The client is therefore guaranteed that a transaction reported to be committed will be preserved, even in the event of a server crash immediately after. However, for short transactions this delay is a major component of the total transaction time. Selecting asynchronous commit mode means that the server returns success as soon as the transaction is logically completed, before the WAL records it generated have actually made their way to disk. This can provide a significant boost in throughput for small transactions.

### Passage 1: [source](https://www.postgresql.org/docs/18/wal-async-commit.html)

The risk that is taken by using asynchronous commit is of data loss, not data corruption. If the database should crash, it will recover by replaying WAL up to the last record that was flushed. The database will therefore be restored to a self-consistent state, but any transactions that were not yet flushed to disk will not be reflected in that state. The net effect is therefore loss of the last few transactions. Because the transactions are replayed in commit order, no inconsistency can be introduced — for example, if transaction B made changes relying on the effects of a previous transaction A, it is not possible for A's effects to be lost while B's effects are preserved.

### Passage 2: [source](https://www.postgresql.org/docs/18/wal-async-commit.html)

Asynchronous commit provides behavior different from setting fsync = off. fsync is a server-wide setting that will alter the behavior of all transactions. It disables all logic within PostgreSQL that attempts to synchronize writes to different portions of the database, and therefore a system crash (that is, a hardware or operating system crash, not a failure of PostgreSQL itself) could result in arbitrarily bad corruption of the database state. In many scenarios, asynchronous commit provides most of the performance improvement that could be obtained by turning off fsync, but without the risk of data corruption.

- **0 SUPPORTED**: An asynchronous success response can precede durable WAL.
  Reason: This is an explicit premise in the answer, separate from the subsequent crash-loss conclusion.
  Evidence [0]: Selecting asynchronous commit mode means that the server returns success as soon as the transaction is logically completed, before the WAL records it generated have actually made their way to disk.
- **1 SUPPORTED**: A crash after an asynchronous success response can still lose the acknowledged transaction.
  Reason: Combine early success before disk flush with loss of transactions not yet flushed.
  Evidence [0]: Selecting asynchronous commit mode means that the server returns success as soon as the transaction is logically completed, before the WAL records it generated have actually made their way to disk.
  Evidence [1]: The database will therefore be restored to a self-consistent state, but any transactions that were not yet flushed to disk will not be reflected in that state.
- **2 SUPPORTED**: Recovery replays transactions in commit order.
  Reason: Replay order is explicitly stated.
  Evidence [1]: Because the transactions are replayed in commit order, no inconsistency can be introduced — for example, if transaction B made changes relying on the effects of a previous transaction A, it is not possible for A's effects to be lost while B's effects are preserved.
- **3 CONTRADICTED**: If transaction B depended on earlier A, recovery can retain B while losing A.
  Reason: The explicit dependency example rules out that combination.
  Evidence [1]: Because the transactions are replayed in commit order, no inconsistency can be introduced — for example, if transaction B made changes relying on the effects of a previous transaction A, it is not possible for A's effects to be lost while B's effects are preserved.
- **4 SUPPORTED**: Asynchronous commit risks lost transactions.
  Reason: The risk distinction is explicit.
  Evidence [1]: The risk that is taken by using asynchronous commit is of data loss, not data corruption.
- **5 SUPPORTED**: Asynchronous commit does not risk data corruption.
  Reason: The risk distinction is explicit.
  Evidence [1]: The risk that is taken by using asynchronous commit is of data loss, not data corruption.

Reviewer notes: ____________________

## postgres-runtime-config-resource (dev; distortion)

Human review: [ ] accepted  [ ] correction needed

A work_mem value written as 4MB means exactly 4,000,000 bytes and is a single shared cap for all sorting in one query. With hash_mem_multiplier set to 2, a hash table has an 8 MiB limit at that setting. Supplying work_mem without a unit uses kilobytes.

### Passage 0: [source](https://www.postgresql.org/docs/18/runtime-config-resource.html)

Sets the base maximum amount of memory to be used by a query operation (such as a sort or hash table) before writing to temporary disk files. If this value is specified without units, it is taken as kilobytes. The default value is four megabytes (4MB). Note that a complex query might perform several sort and hash operations at the same time, with each operation generally being allowed to use as much memory as this value specifies before it starts to write data into temporary files. Also, several running sessions could be doing such operations concurrently. Therefore, the total memory used could be many times the value of work_mem; it is necessary to keep this fact in mind when choosing the value. Sort operations are used for ORDER BY, DISTINCT, and merge joins. Hash tables are used in hash joins, hash-based aggregation, memoize nodes and hash-based processing of IN subqueries.

### Passage 1: [source](https://www.postgresql.org/docs/18/runtime-config-resource.html)

Hash-based operations are generally more sensitive to memory availability than equivalent sort-based operations. The memory limit for a hash table is computed by multiplying work_mem by hash_mem_multiplier. This makes it possible for hash-based operations to use an amount of memory that exceeds the usual work_mem base amount.

### Passage 2: [source](https://www.postgresql.org/docs/18/runtime-config-resource.html)

Specifies the maximum safe depth of the server's execution stack. The ideal setting for this parameter is the actual stack size limit enforced by the kernel (as set by ulimit -s or local equivalent), less a safety margin of a megabyte or so. The safety margin is needed because the stack depth is not checked in every routine in the server, but only in key potentially-recursive routines. If this value is specified without units, it is taken as kilobytes. The default setting is two megabytes (2MB), which is conservatively small and unlikely to risk crashes. However, it might be too small to allow execution of complex functions. Only superusers and users with the appropriate SET privilege can change this setting.

### Passage 3: [source](https://www.postgresql.org/docs/18/config-setting.html)

Numeric with Unit: Some numeric parameters have an implicit unit, because they describe quantities of memory or time. The unit might be bytes, kilobytes, blocks (typically eight kilobytes), milliseconds, seconds, or minutes. An unadorned numeric value for one of these settings will use the setting's default unit, which can be learned from pg_settings.unit. For convenience, settings can be given with a unit specified explicitly, for example '120 ms' for a time value, and they will be converted to whatever the parameter's actual unit is. Note that the value must be written as a string (with quotes) to use this feature. The unit name is case-sensitive, and there can be whitespace between the numeric value and the unit.

Valid memory units are B (bytes), kB (kilobytes), MB (megabytes), GB (gigabytes), and TB (terabytes). The multiplier for memory units is 1024, not 1000.

Valid time units are us (microseconds), ms (milliseconds), s (seconds), min (minutes), h (hours), and d (days).

- **0 CONTRADICTED**: A work_mem value written as 4MB means exactly 4000000 bytes.
  Reason: PostgreSQL memory units use 1024, so 4MB is 4194304 bytes.
  Evidence [3]: Valid memory units are B (bytes), kB (kilobytes), MB (megabytes), GB (gigabytes), and TB (terabytes).
  Evidence [3]: The multiplier for memory units is 1024, not 1000.
- **1 CONTRADICTED**: work_mem is a single shared cap for all sorting in one query.
  Reason: Each operation is generally allowed its own work_mem budget.
  Evidence [0]: Note that a complex query might perform several sort and hash operations at the same time, with each operation generally being allowed to use as much memory as this value specifies before it starts to write data into temporary files.
- **2 SUPPORTED**: With work_mem 4MB and hash_mem_multiplier 2, a hash table has an 8 MiB limit.
  Reason: Combine the multiplicative hash limit with binary memory units; 4 times 2 MiB is 8 MiB.
  Evidence [1]: The memory limit for a hash table is computed by multiplying work_mem by hash_mem_multiplier.
  Evidence [3]: Valid memory units are B (bytes), kB (kilobytes), MB (megabytes), GB (gigabytes), and TB (terabytes).
  Evidence [3]: The multiplier for memory units is 1024, not 1000.
- **3 SUPPORTED**: Supplying work_mem without a unit uses kilobytes.
  Reason: The no-unit convention is explicit in the work_mem description.
  Evidence [0]: If this value is specified without units, it is taken as kilobytes.

Reviewer notes: ____________________

## postgres-runtime-config-client (dev; distortion)

Human review: [ ] accepted  [ ] correction needed

A unitless lock_timeout of 1500 permits about 1.5 seconds of waiting per acquisition attempt, and it fires exactly at the limit rather than only after it is exceeded. A zero setting causes immediate expiration. A nonzero statement_timeout of the same duration would fire first. In a simple-query message containing several statements, the statement timeout applies to each separately.

### Passage 0: [source](https://www.postgresql.org/docs/18/runtime-config-client.html)

Abort any statement that waits longer than the specified amount of time while attempting to acquire a lock on a table, index, row, or other database object. The time limit applies separately to each lock acquisition attempt. The limit applies both to explicit locking requests (such as LOCK TABLE, or SELECT FOR UPDATE without NOWAIT) and to implicitly-acquired locks. If this value is specified without units, it is taken as milliseconds. A value of zero (the default) disables the timeout.

Unlike statement_timeout, this timeout can only occur while waiting for locks. Note that if statement_timeout is nonzero, it is rather pointless to set lock_timeout to the same or larger value, since the statement timeout would always trigger first. If log_min_error_statement is set to ERROR or lower, the statement that timed out will be logged.

### Passage 1: [source](https://www.postgresql.org/docs/18/runtime-config-client.html)

Abort any statement that takes more than the specified amount of time. If log_min_error_statement is set to ERROR or lower, the statement that timed out will also be logged. If this value is specified without units, it is taken as milliseconds. A value of zero (the default) disables the timeout.

The timeout is measured from the time a command arrives at the server until it is completed by the server. If multiple SQL statements appear in a single simple-query message, the timeout is applied to each statement separately. (PostgreSQL versions before 13 usually treated the timeout as applying to the whole query string.) In extended query protocol, the timeout starts running when any query-related message (Parse, Bind, Execute, Describe) arrives, and it is canceled by completion of an Execute or Sync message.

### Passage 2: [source](https://www.postgresql.org/docs/18/runtime-config-client.html)

This option can be used to ensure that idle sessions do not hold locks for an unreasonable amount of time. Even when no significant locks are held, an open transaction prevents vacuuming away recently-dead tuples that may be visible only to this transaction; so remaining idle for a long time can contribute to table bloat. See Section 24.1 for more details.

- **0 SUPPORTED**: A unitless lock_timeout of 1500 permits about 1.5 seconds of waiting per acquisition attempt.
  Reason: Units are milliseconds and the limit applies separately to each attempt; 1500ms is 1.5s.
  Evidence [0]: The time limit applies separately to each lock acquisition attempt.
  Evidence [0]: If this value is specified without units, it is taken as milliseconds.
- **1 CONTRADICTED**: lock_timeout fires exactly at the limit rather than only after it is exceeded.
  Reason: The documented boundary is waits longer than the specified time.
  Evidence [0]: Abort any statement that waits longer than the specified amount of time while attempting to acquire a lock on a table, index, row, or other database object.
- **2 CONTRADICTED**: A zero lock_timeout causes immediate expiration.
  Reason: Zero disables the timeout.
  Evidence [0]: A value of zero (the default) disables the timeout.
- **3 SUPPORTED**: In a simple-query message containing several statements, the statement timeout applies to each separately.
  Reason: The documented modern behavior applies to each statement.
  Evidence [1]: If multiple SQL statements appear in a single simple-query message, the timeout is applied to each statement separately.
- **4 SUPPORTED**: A nonzero statement_timeout of the same duration as lock_timeout fires first.
  Reason: The priority is explicitly stated.
  Evidence [0]: Note that if statement_timeout is nonzero, it is rather pointless to set lock_timeout to the same or larger value, since the statement timeout would always trigger first.

Reviewer notes: ____________________

## postgres-sql-truncate (dev; supported)

Human review: [ ] accepted  [ ] correction needed

TRUNCATE can be rolled back with its surrounding transaction, yet an older concurrent snapshot can see the table as empty after truncation. It runs ON TRUNCATE triggers, not ON DELETE triggers; all BEFORE TRUNCATE hooks precede any truncation.

### Passage 0: [source](https://www.postgresql.org/docs/18/sql-truncate.html)

TRUNCATE is not MVCC-safe. After truncation, the table will appear empty to concurrent transactions, if they are using a snapshot taken before the truncation occurred. See Section 13.6 for more details.

TRUNCATE is transaction-safe with respect to the data in the tables: the truncation will be safely rolled back if the surrounding transaction does not commit.

### Passage 1: [source](https://www.postgresql.org/docs/18/sql-truncate.html)

TRUNCATE will not fire any ON DELETE triggers that might exist for the tables. But it will fire ON TRUNCATE triggers. If ON TRUNCATE triggers are defined for any of the tables, then all BEFORE TRUNCATE triggers are fired before any truncation happens, and all AFTER TRUNCATE triggers are fired after the last truncation is performed and any sequences are reset. The triggers will fire in the order that the tables are to be processed (first those listed in the command, and then any that were added due to cascading).

### Passage 2: [source](https://www.postgresql.org/docs/18/sql-truncate.html)

TRUNCATE cannot be used on a table that has foreign-key references from other tables, unless all such tables are also truncated in the same command. Checking validity in such cases would require table scans, and the whole point is not to do one. The CASCADE option can be used to automatically include all dependent tables — but be very careful when using this option, or else you might lose data you did not intend to! Note in particular that when the table to be truncated is a partition, siblings partitions are left untouched, but cascading occurs to all referencing tables and all their partitions with no distinction.

- **0 SUPPORTED**: TRUNCATE can be rolled back with its surrounding transaction.
  Reason: Table data changes are transaction-safe.
  Evidence [0]: TRUNCATE is transaction-safe with respect to the data in the tables: the truncation will be safely rolled back if the surrounding transaction does not commit.
- **1 SUPPORTED**: An older concurrent snapshot can see the table as empty after truncation.
  Reason: The operation is not MVCC-safe even though it is transaction-safe.
  Evidence [0]: After truncation, the table will appear empty to concurrent transactions, if they are using a snapshot taken before the truncation occurred.
- **2 SUPPORTED**: TRUNCATE runs ON TRUNCATE triggers.
  Reason: The trigger type is explicit.
  Evidence [1]: But it will fire ON TRUNCATE triggers.
- **3 SUPPORTED**: TRUNCATE does not run ON DELETE triggers.
  Reason: DELETE triggers are explicitly excluded.
  Evidence [1]: TRUNCATE will not fire any ON DELETE triggers that might exist for the tables.
- **4 SUPPORTED**: All BEFORE TRUNCATE triggers run before any truncation.
  Reason: The trigger ordering applies across the affected tables.
  Evidence [1]: If ON TRUNCATE triggers are defined for any of the tables, then all BEFORE TRUNCATE triggers are fired before any truncation happens, and all AFTER TRUNCATE triggers are fired after the last truncation is performed and any sequences are reset.

Reviewer notes: ____________________

## postgres-functions-sequence (test; extrinsic)

Human review: [ ] accepted  [ ] correction needed

After setval(seq, 42, false), the next nextval returns 42 without advancing first. Rolling back a transaction does not reclaim its allocated nextval value, so sequences need not be gapless. PostgreSQL uses an MVCC architecture.

### Passage 0: [source](https://www.postgresql.org/docs/18/functions-sequence.html)

Sets the sequence object's current value, and optionally its is_called flag. The two-parameter form sets the sequence's last_value field to the specified value and sets its is_called field to true, meaning that the next nextval will advance the sequence before returning a value. The value that will be reported by currval is also set to the specified value. In the three-parameter form, is_called can be set to either true or false. true has the same effect as the two-parameter form. If it is set to false, the next nextval will return exactly the specified value, and sequence advancement commences with the following nextval. Furthermore, the value reported by currval is not changed in this case. For example,

### Passage 1: [source](https://www.postgresql.org/docs/18/functions-sequence.html)

To avoid blocking concurrent transactions that obtain numbers from the same sequence, the value obtained by nextval is not reclaimed for re-use if the calling transaction later aborts. This means that transaction aborts or database crashes can result in gaps in the sequence of assigned values. That can happen without a transaction abort, too. For example an INSERT with an ON CONFLICT clause will compute the to-be-inserted tuple, including doing any required nextval calls, before detecting any conflict that would cause it to follow the ON CONFLICT rule instead. Thus, PostgreSQL sequence objects cannot be used to obtain “gapless” sequences.

### Passage 2: [source](https://www.postgresql.org/docs/18/functions-sequence.html)

If the database cluster crashes before committing a transaction containing a nextval or setval call, the sequence state change might not have made its way to persistent storage, so that it is uncertain whether the sequence will have its original or updated state after the cluster restarts. This is harmless for usage of the sequence within the database, since other effects of uncommitted transactions will not be visible either. However, if you wish to use a sequence value for persistent outside-the-database purposes, make sure that the nextval call has been committed before doing so.

- **0 SUPPORTED**: After setval(seq, 42, false), the next nextval returns 42 without advancing first.
  Reason: False defers advancement until the following call.
  Evidence [0]: If it is set to false, the next nextval will return exactly the specified value, and sequence advancement commences with the following nextval.
- **1 SUPPORTED**: Rolling back a transaction does not reclaim its allocated nextval value.
  Reason: Aborting the caller does not reclaim the number.
  Evidence [1]: To avoid blocking concurrent transactions that obtain numbers from the same sequence, the value obtained by nextval is not reclaimed for re-use if the calling transaction later aborts.
- **2 SUPPORTED**: PostgreSQL sequences need not be gapless.
  Reason: The sequence-object limitation is explicit.
  Evidence [1]: Thus, PostgreSQL sequence objects cannot be used to obtain “gapless” sequences.
- **3 UNSUPPORTED**: PostgreSQL uses an MVCC architecture.
  Reason: True in the isolation documentation, not stated in these sequence excerpts.

Reviewer notes: ____________________

## python-asyncio-task (dev; multi_passage)

Human review: [ ] accepted  [ ] correction needed

When one TaskGroup child fails with a non-cancellation exception, its siblings are cancelled and the group waits for them before raising the grouped failures. No new children can be added after that failure. gather provides the same sibling-cancellation guarantee when a submitted task raises.

### Passage 0: [source](https://docs.python.org/3.13/library/asyncio-task.html)

The async with statement will wait for all tasks in the group to finish. While waiting, new tasks may still be added to the group (for example, by passing tg into one of the coroutines and calling tg.create_task() in that coroutine). Once the last task has finished and the async with block is exited, no new tasks may be added to the group.

The first time any of the tasks belonging to the group fails with an exception other than asyncio.CancelledError, the remaining tasks in the group are cancelled. No further tasks can then be added to the group. At this point, if the body of the async with statement is still active (i.e., __aexit__() hasn’t been called yet), the task directly containing the async with statement is also cancelled. The resulting asyncio.CancelledError will interrupt an await, but it will not bubble out of the containing async with statement.

### Passage 1: [source](https://docs.python.org/3.13/library/asyncio-task.html)

Once all tasks have finished, if any tasks have failed with an exception other than asyncio.CancelledError, those exceptions are combined in an ExceptionGroup or BaseExceptionGroup (as appropriate; see their documentation) which is then raised.

A new alternative to create and run tasks concurrently and wait for their completion is asyncio.TaskGroup. TaskGroup provides stronger safety guarantees than gather for scheduling a nesting of subtasks: if a task (or a subtask, a task scheduled by a task) raises an exception, TaskGroup will, while gather will not, cancel the remaining scheduled tasks.

### Passage 2: [source](https://docs.python.org/3.13/library/asyncio-task.html)

Save a reference to the result of this function, to avoid a task disappearing mid-execution. The event loop only keeps weak references to tasks. A task that isn’t referenced elsewhere may get garbage collected at any time, even before it’s done. For reliable “fire-and-forget” background tasks, gather them in a collection:

- **0 SUPPORTED**: When one TaskGroup child fails with a non-cancellation exception, its siblings are cancelled.
  Reason: The first non-CancelledError failure triggers cancellation.
  Evidence [0]: The first time any of the tasks belonging to the group fails with an exception other than asyncio.CancelledError, the remaining tasks in the group are cancelled.
- **1 SUPPORTED**: After a non-cancellation child failure, TaskGroup waits for the cancelled siblings before raising grouped failures.
  Reason: Combine sibling cancellation with waiting for all tasks and only then raising grouped exceptions.
  Evidence [0]: The first time any of the tasks belonging to the group fails with an exception other than asyncio.CancelledError, the remaining tasks in the group are cancelled.
  Evidence [0]: The async with statement will wait for all tasks in the group to finish.
  Evidence [1]: Once all tasks have finished, if any tasks have failed with an exception other than asyncio.CancelledError, those exceptions are combined in an ExceptionGroup or BaseExceptionGroup (as appropriate; see their documentation) which is then raised.
- **2 SUPPORTED**: No new children can be added to TaskGroup after a non-cancellation child failure.
  Reason: The following sentence prohibits further additions.
  Evidence [0]: The first time any of the tasks belonging to the group fails with an exception other than asyncio.CancelledError, the remaining tasks in the group are cancelled.
  Evidence [0]: No further tasks can then be added to the group.
- **3 CONTRADICTED**: gather guarantees sibling cancellation when a submitted task raises.
  Reason: The comparison explicitly says gather will not cancel the remaining tasks in this situation.
  Evidence [1]: TaskGroup provides stronger safety guarantees than gather for scheduling a nesting of subtasks: if a task (or a subtask, a task scheduled by a task) raises an exception, TaskGroup will, while gather will not, cancel the remaining scheduled tasks.

Reviewer notes: ____________________

## python-concurrent.futures (test; distortion)

Human review: [ ] accepted  [ ] correction needed

Calling executor shutdown with wait=False lets the Python process exit immediately while work is pending. With cancel_futures=True it also cancels already-running jobs. Increasing map chunksize can speed long ProcessPoolExecutor workloads, but it has no effect for ThreadPoolExecutor.

### Passage 0: [source](https://docs.python.org/3.13/library/concurrent.futures.html)

If wait is True then this method will not return until all the pending futures are done executing and the resources associated with the executor have been freed. If wait is False then this method will return immediately and the resources associated with the executor will be freed when all pending futures are done executing. Regardless of the value of wait, the entire Python program will not exit until all pending futures are done executing.

If cancel_futures is True, this method will cancel all pending futures that the executor has not started running. Any futures that are completed or running won’t be cancelled, regardless of the value of cancel_futures.

If both cancel_futures and wait are True, all futures that the executor has started running will be completed prior to this method returning. The remaining futures are cancelled.

### Passage 1: [source](https://docs.python.org/3.13/library/concurrent.futures.html)

When using ProcessPoolExecutor, this method chops iterables into a number of chunks which it submits to the pool as separate tasks. The (approximate) size of these chunks can be specified by setting chunksize to a positive integer. For very long iterables, using a large value for chunksize can significantly improve performance compared to the default size of 1. With ThreadPoolExecutor, chunksize has no effect.

### Passage 2: [source](https://docs.python.org/3.13/library/concurrent.futures.html)

max_tasks_per_child is an optional argument that specifies the maximum number of tasks a single process can execute before it will exit and be replaced with a fresh worker process. By default max_tasks_per_child is None which means worker processes will live as long as the pool. When a max is specified, the “spawn” multiprocessing start method will be used by default in absence of a mp_context parameter. This feature is incompatible with the “fork” start method.

- **0 CONTRADICTED**: Executor shutdown with wait=False lets the Python process exit immediately while work is pending.
  Reason: The method can return immediately but program exit still waits for pending futures.
  Evidence [0]: Regardless of the value of wait, the entire Python program will not exit until all pending futures are done executing.
- **1 CONTRADICTED**: Executor shutdown with cancel_futures=True cancels already-running jobs.
  Reason: Running and completed futures are explicitly excluded.
  Evidence [0]: Any futures that are completed or running won’t be cancelled, regardless of the value of cancel_futures.
- **2 SUPPORTED**: Increasing map chunksize can speed long ProcessPoolExecutor workloads.
  Reason: The context explicitly describes this potential benefit for process pools.
  Evidence [1]: When using ProcessPoolExecutor, this method chops iterables into a number of chunks which it submits to the pool as separate tasks.
  Evidence [1]: For very long iterables, using a large value for chunksize can significantly improve performance compared to the default size of 1.
- **3 SUPPORTED**: map chunksize has no effect for ThreadPoolExecutor.
  Reason: The executor-specific exception is explicit.
  Evidence [1]: With ThreadPoolExecutor, chunksize has no effect.

Reviewer notes: ____________________

## python-datetime (dev; distortion)

Human review: [ ] accepted  [ ] correction needed

ISO weeks start on Sunday, and January 1 always belongs to week 1 of its Gregorian year. On non-POSIX systems that count leap seconds, fromtimestamp still maps timestamps a second apart to different datetime objects. Its common platform-supported year range is 1970 through 2038.

### Passage 0: [source](https://docs.python.org/3.13/library/datetime.html)

The ISO year consists of 52 or 53 full weeks, and where a week starts on a Monday and ends on a Sunday. The first week of an ISO year is the first (Gregorian) calendar week of a year containing a Thursday. This is called week number 1, and the ISO year of that Thursday is the same as its Gregorian year.

### Passage 1: [source](https://docs.python.org/3.13/library/datetime.html)

fromtimestamp() may raise OverflowError, if the timestamp is out of the range of values supported by the platform C localtime() or gmtime() functions, and OSError on localtime() or gmtime() failure. It’s common for this to be restricted to years in 1970 through 2038. Note that on non-POSIX systems that include leap seconds in their notion of a timestamp, leap seconds are ignored by fromtimestamp(), and then it’s possible to have two timestamps differing by a second that yield identical datetime objects. This method is preferred over utcfromtimestamp().

### Passage 2: [source](https://docs.python.org/3.13/library/datetime.html)

If any argument is a float and there are fractional microseconds, the fractional microseconds left over from all arguments are combined and their sum is rounded to the nearest microsecond using round-half-to-even tiebreaker. If no argument is a float, the conversion and normalization processes are exact (no information is lost).

- **0 CONTRADICTED**: ISO weeks start on Sunday.
  Reason: The source says Monday through Sunday.
  Evidence [0]: The ISO year consists of 52 or 53 full weeks, and where a week starts on a Monday and ends on a Sunday.
- **1 CONTRADICTED**: January 1 always belongs to ISO week 1 of its Gregorian year.
  Reason: Week 1 is defined by containing a Thursday; January 1 need not be in that week.
  Evidence [0]: The first week of an ISO year is the first (Gregorian) calendar week of a year containing a Thursday.
  Evidence [0]: This is called week number 1, and the ISO year of that Thursday is the same as its Gregorian year.
- **2 CONTRADICTED**: On non-POSIX systems that count leap seconds, fromtimestamp maps timestamps a second apart to different datetime objects.
  Reason: Ignoring leap seconds can collapse the two inputs to an identical result.
  Evidence [1]: Note that on non-POSIX systems that include leap seconds in their notion of a timestamp, leap seconds are ignored by fromtimestamp(), and then it’s possible to have two timestamps differing by a second that yield identical datetime objects.
- **3 SUPPORTED**: The common platform-supported year range for fromtimestamp is 1970 through 2038.
  Reason: This is described as common, not universal.
  Evidence [1]: It’s common for this to be restricted to years in 1970 through 2038.

Reviewer notes: ____________________

## python-decimal (dev; supported)

Human review: [ ] accepted  [ ] correction needed

Converting a float to Decimal preserves the actual binary value rather than repairing it to the intended decimal literal. Thus Decimal.from_float(0.1) differs from Decimal("0.1"). A context precision of three does not strip the five stored zeros from Decimal("3.00000").

### Passage 0: [source](https://docs.python.org/3.13/library/decimal.html)

If value is a float, the binary floating-point value is losslessly converted to its exact decimal equivalent. This conversion can often require 53 or more digits of precision. For example, Decimal(float('1.1')) converts to Decimal('1.100000000000000088817841970012523233890533447265625').

The context precision does not affect how many digits are stored. That is determined exclusively by the number of digits in value. For example, Decimal('3.00000') records all five zeros even if the context precision is only three.

### Passage 1: [source](https://docs.python.org/3.13/library/decimal.html)

Note Decimal.from_float(0.1) is not the same as Decimal('0.1'). Since 0.1 is not exactly representable in binary floating point, the value is stored as the nearest representable value which is 0x1.999999999999ap-4. That equivalent value in decimal is 0.1000000000000000055511151231257827021181583404541015625.

### Passage 2: [source](https://docs.python.org/3.13/library/decimal.html)

If ndigits is an int, the context’s rounding mode is respected and a Decimal representing number rounded to the nearest multiple of Decimal('1E-ndigits') is returned; in this case, round(number, ndigits) is equivalent to self.quantize(Decimal('1E-ndigits')). Returns Decimal('NaN') if number is a quiet NaN. Raises InvalidOperation if number is an infinity, a signaling NaN, or if the length of the coefficient after the quantize operation would be greater than the current context’s precision. In other words, for the non-corner cases:

- **0 SUPPORTED**: Converting a float to Decimal preserves its actual binary floating-point value exactly.
  Reason: The conversion is lossless to the exact decimal equivalent.
  Evidence [0]: If value is a float, the binary floating-point value is losslessly converted to its exact decimal equivalent.
- **1 SUPPORTED**: Decimal.from_float(0.1) differs from Decimal("0.1").
  Reason: The documented comparison distinguishes the float conversion from the string literal.
  Evidence [1]: Note Decimal.from_float(0.1) is not the same as Decimal('0.1').
- **2 SUPPORTED**: Context precision three does not strip the five stored zeros from Decimal("3.00000").
  Reason: Construction retains all five zeros despite the arithmetic precision.
  Evidence [0]: For example, Decimal('3.00000') records all five zeros even if the context precision is only three.

Reviewer notes: ____________________

## python-pathlib (test; multi_passage)

Human review: [ ] accepted  [ ] correction needed

During top-down Path.walk, removing an entry from dirnames prunes that subtree. With follow_symlinks=True, that same pruning mechanism can exclude a directory reached through a symlink. Leaving such a link in the walk is always safe from loops because the walker remembers visited directories. Editing dirnames bottom-up prunes just as effectively.

### Passage 0: [source](https://docs.python.org/3.13/library/pathlib.html)

When top_down is true, the caller can modify the dirnames list in-place (for example, using del or slice assignment), and Path.walk() will only recurse into the subdirectories whose names remain in dirnames. This can be used to prune the search, or to impose a specific order of visiting, or even to inform Path.walk() about directories the caller creates or renames before it resumes Path.walk() again. Modifying dirnames when top_down is false has no effect on the behavior of Path.walk() since the directories in dirnames have already been generated by the time dirnames is yielded to the caller.

### Passage 1: [source](https://docs.python.org/3.13/library/pathlib.html)

By default, Path.walk() does not follow symbolic links, and instead adds them to the filenames list. Set follow_symlinks to true to resolve symlinks and place them in dirnames and filenames as appropriate for their targets, and consequently visit directories pointed to by symlinks (where supported).

Be aware that setting follow_symlinks to true can lead to infinite recursion if a link points to a parent directory of itself. Path.walk() does not keep track of the directories it has already visited.

### Passage 2: [source](https://docs.python.org/3.13/library/pathlib.html)

By default, errors from os.scandir() are ignored. If the optional argument on_error is specified, it should be a callable; it will be called with one argument, an OSError instance. The callable can handle the error to continue the walk or re-raise it to stop the walk. Note that the filename is available as the filename attribute of the exception object.

- **0 SUPPORTED**: During top-down Path.walk, removing an entry from dirnames prunes that subtree.
  Reason: Only names remaining in dirnames are traversed.
  Evidence [0]: When top_down is true, the caller can modify the dirnames list in-place (for example, using del or slice assignment), and Path.walk() will only recurse into the subdirectories whose names remain in dirnames.
- **1 SUPPORTED**: With top-down Path.walk and follow_symlinks=True, removing a symlinked directory from dirnames excludes its subtree.
  Reason: Combine symlink targets being put in dirnames with top-down in-place pruning.
  Evidence [1]: Set follow_symlinks to true to resolve symlinks and place them in dirnames and filenames as appropriate for their targets, and consequently visit directories pointed to by symlinks (where supported).
  Evidence [0]: When top_down is true, the caller can modify the dirnames list in-place (for example, using del or slice assignment), and Path.walk() will only recurse into the subdirectories whose names remain in dirnames.
- **2 CONTRADICTED**: With follow_symlinks=True, Path.walk always avoids loops.
  Reason: The walker does not track visited directories and may recurse infinitely.
  Evidence [1]: Be aware that setting follow_symlinks to true can lead to infinite recursion if a link points to a parent directory of itself.
  Evidence [1]: Path.walk() does not keep track of the directories it has already visited.
- **3 CONTRADICTED**: Path.walk remembers visited directories.
  Reason: The walker does not track visited directories and may recurse infinitely.
  Evidence [1]: Be aware that setting follow_symlinks to true can lead to infinite recursion if a link points to a parent directory of itself.
  Evidence [1]: Path.walk() does not keep track of the directories it has already visited.
- **4 CONTRADICTED**: Editing dirnames bottom-up prunes the walk as effectively as top-down.
  Reason: Bottom-up edits have no effect on traversal.
  Evidence [0]: Modifying dirnames when top_down is false has no effect on the behavior of Path.walk() since the directories in dirnames have already been generated by the time dirnames is yielded to the caller.

Reviewer notes: ____________________

## python-json (dev; extrinsic)

Human review: [ ] accepted  [ ] correction needed

JSON round-tripping a dictionary with integer keys can change those keys into strings. If an object repeats a name, the default decoder keeps its final value rather than raising. Python's JSON encoder also emits NaN by default, despite the JSON specification.

### Passage 0: [source](https://docs.python.org/3.13/library/json.html)

Keys in key/value pairs of JSON are always of the type str. When a dictionary is converted into JSON, all the keys of the dictionary are converted to strings. As a result of this, if a dictionary is converted into JSON and then back into a dictionary, the dictionary may not equal the original one. That is, loads(dumps(x)) != x if x has non-string keys. sort_keys sorts the keys before they are converted to strings, so numeric keys are sorted by value, not by their string representation.

### Passage 1: [source](https://docs.python.org/3.13/library/json.html)

The RFC specifies that the names within a JSON object should be unique, but does not mandate how repeated names in JSON objects should be handled. By default, this module does not raise an exception; instead, it ignores all but the last name-value pair for a given name:

The object_pairs_hook parameter can be used to alter this behavior.

### Passage 2: [source](https://docs.python.org/3.13/library/json.html)

The old version of JSON specified by the obsolete RFC 4627 required that the top-level value of a JSON text must be either a JSON object or array (Python dict or list), and could not be a JSON null, boolean, number, or string value. RFC 7159 removed that restriction, and this module does not and has never implemented that restriction in either its serializer or its deserializer.

- **0 SUPPORTED**: JSON round-tripping a dictionary with integer keys can change its keys into strings.
  Reason: All dictionary keys are converted to strings.
  Evidence [0]: When a dictionary is converted into JSON, all the keys of the dictionary are converted to strings.
- **1 SUPPORTED**: For a repeated object name, the default JSON decoder keeps the final value.
  Reason: The last pair wins and no exception is raised by default.
  Evidence [1]: By default, this module does not raise an exception; instead, it ignores all but the last name-value pair for a given name:

The object_pairs_hook parameter can be used to alter this behavior.
- **2 SUPPORTED**: The default JSON decoder does not raise an exception for repeated object names.
  Reason: The last pair wins and no exception is raised by default.
  Evidence [1]: By default, this module does not raise an exception; instead, it ignores all but the last name-value pair for a given name:

The object_pairs_hook parameter can be used to alter this behavior.
- **3 UNSUPPORTED**: Python JSON emits NaN by default.
  Reason: True in another paragraph of this page, but omitted from all selected passages.
- **4 UNSUPPORTED**: The JSON specification does not permit NaN.
  Reason: True in another paragraph of this page, but omitted from all selected passages.

Reviewer notes: ____________________

## python-tempfile (test; extrinsic)

Human review: [ ] accepted  [ ] correction needed

With delete=True but delete_on_close=False, closing the named temporary file delays cleanup until context exit or finalization; cleanup is not guaranteed. On Windows without directory delete permission, that delayed unlink can fail with PermissionError. mkstemp avoids a creation race when the platform correctly implements O_EXCL.

### Passage 0: [source](https://docs.python.org/3.13/library/tempfile.html)

If delete is true (the default) and delete_on_close is true (the default), the file is deleted as soon as it is closed. If delete is true and delete_on_close is false, the file is deleted on context manager exit only, or else when the file-like object is finalized. Deletion is not always guaranteed in this case (see object.__del__()). If delete is false, the value of delete_on_close is ignored.

### Passage 1: [source](https://docs.python.org/3.13/library/tempfile.html)

On Windows, if delete_on_close is false, and the file is created in a directory for which the user lacks delete access, then the os.unlink() call on exit of the context manager will fail with a PermissionError. This cannot happen when delete_on_close is true because delete access is requested by the open, which fails immediately if the requested access is not granted.

### Passage 2: [source](https://docs.python.org/3.13/library/tempfile.html)

The returned object is a file-like object whose _file attribute is either an io.BytesIO or io.TextIOWrapper object (depending on whether binary or text mode was specified) or a true file object, depending on whether rollover() has been called. This file-like object can be used in a with statement, just like a normal file.

- **0 SUPPORTED**: With delete=True and delete_on_close=False, named temporary-file cleanup is delayed until context exit or finalization.
  Reason: The two flag combinations are distinguished explicitly.
  Evidence [0]: If delete is true and delete_on_close is false, the file is deleted on context manager exit only, or else when the file-like object is finalized.
- **1 SUPPORTED**: Named temporary-file cleanup is not guaranteed with delete=True and delete_on_close=False.
  Reason: Finalization-based cleanup has an explicit caveat.
  Evidence [0]: Deletion is not always guaranteed in this case (see object.__del__()).
- **2 SUPPORTED**: On Windows without directory delete permission, delayed temporary-file unlink can fail with PermissionError.
  Reason: The access and timing conditions are explicitly specified.
  Evidence [1]: On Windows, if delete_on_close is false, and the file is created in a directory for which the user lacks delete access, then the os.unlink() call on exit of the context manager will fail with a PermissionError.
- **3 UNSUPPORTED**: mkstemp avoids a creation race when the platform correctly implements O_EXCL.
  Reason: This is true in a different unprovided section, but these excerpts concern cleanup and spooling.

Reviewer notes: ____________________

## python-functools (dev; multi_passage)

Human review: [ ] accepted  [ ] correction needed

A cached_property value installed by the latest concurrent getter can later be invalidated by deleting that attribute. The memoizing function cache can likewise compute the same call twice during a race; therefore it is not thread-safe.

### Passage 0: [source](https://docs.python.org/3.13/library/functools.html)

The cached_property decorator only runs on lookups and only when an attribute of the same name doesn’t exist. When it does run, the cached_property writes to the attribute with the same name. Subsequent attribute reads and writes take precedence over the cached_property method and it works like a normal attribute.

The cached value can be cleared by deleting the attribute. This allows the cached_property method to run again.

### Passage 1: [source](https://docs.python.org/3.13/library/functools.html)

The cached_property does not prevent a possible race condition in multi-threaded usage. The getter function could run more than once on the same instance, with the latest run setting the cached value. If the cached property is idempotent or otherwise not harmful to run more than once on an instance, this is fine. If synchronization is needed, implement the necessary locking inside the decorated getter function or around the cached property access.

### Passage 2: [source](https://docs.python.org/3.13/library/functools.html)

Decorator to wrap a function with a memoizing callable that saves up to the maxsize most recent calls. It can save time when an expensive or I/O bound function is periodically called with the same arguments.

The cache is threadsafe so that the wrapped function can be used in multiple threads. This means that the underlying data structure will remain coherent during concurrent updates.

It is possible for the wrapped function to be called more than once if another thread makes an additional call before the initial call has been completed and cached.

### Passage 3: [source](https://docs.python.org/3.13/library/functools.html)

Note, type specificity applies only to the function’s immediate arguments rather than their contents. The scalar arguments, Decimal(42) and Fraction(42) are treated as distinct calls with distinct results. In contrast, the tuple arguments ('answer', Decimal(42)) and ('answer', Fraction(42)) are treated as equivalent.

- **0 SUPPORTED**: A cached_property value installed by the latest concurrent getter can later be invalidated by deleting that attribute.
  Reason: The race paragraph identifies which getter installs the cached value; the attribute paragraph supplies deletion invalidation.
  Evidence [1]: The getter function could run more than once on the same instance, with the latest run setting the cached value.
  Evidence [0]: The cached value can be cleared by deleting the attribute.
- **1 SUPPORTED**: The memoizing function cache can compute the same call twice during a race.
  Reason: Concurrent calls can execute before the initial result is cached.
  Evidence [2]: It is possible for the wrapped function to be called more than once if another thread makes an additional call before the initial call has been completed and cached.
- **2 CONTRADICTED**: The memoizing function cache is not thread-safe.
  Reason: Duplicate computation does not negate the explicit data-structure thread-safety guarantee.
  Evidence [2]: The cache is threadsafe so that the wrapped function can be used in multiple threads.
  Evidence [2]: This means that the underlying data structure will remain coherent during concurrent updates.

Reviewer notes: ____________________

## python-sqlite3 (dev; extrinsic)

Human review: [ ] accepted  [ ] correction needed

Exiting a sqlite3 connection context manages the open transaction without closing the connection. With check_same_thread=False the connection may be shared across threads, although the caller may need to serialize writes. The module can optionally load SQLite extensions from shared libraries.

### Passage 0: [source](https://docs.python.org/3.13/library/sqlite3.html)

A Connection object can be used as a context manager that automatically commits or rolls back open transactions when leaving the body of the context manager. If the body of the with statement finishes without exceptions, the transaction is committed. If this commit fails, or if the body of the with statement raises an uncaught exception, the transaction is rolled back. If autocommit is False, a new transaction is implicitly opened after committing or rolling back.

If there is no open transaction upon leaving the body of the with statement, or if autocommit is True, the context manager does nothing.

The context manager neither implicitly opens a new transaction nor closes the connection. If you need a closing context manager, consider using contextlib.closing().

### Passage 1: [source](https://docs.python.org/3.13/library/sqlite3.html)

check_same_thread (bool) – If True (default), ProgrammingError will be raised if the database connection is used by a thread other than the one that created it. If False, the connection may be accessed in multiple threads; write operations may need to be serialized by the user to avoid data corruption. See threadsafety for more information.

### Passage 2: [source](https://docs.python.org/3.13/library/sqlite3.html)

detect_types (int) – Control whether and how data types not natively supported by SQLite are looked up to be converted to Python types, using the converters registered with register_converter(). Set it to any combination (using |, bitwise or) of PARSE_DECLTYPES and PARSE_COLNAMES to enable this. Column names take precedence over declared types if both flags are set. By default (0), type detection is disabled.

- **0 SUPPORTED**: Exiting a sqlite3 connection context manages the open transaction.
  Reason: The context manager commits or rolls back the open transaction on exit.
  Evidence [0]: A Connection object can be used as a context manager that automatically commits or rolls back open transactions when leaving the body of the context manager.
- **1 SUPPORTED**: Exiting a sqlite3 connection context does not close the connection.
  Reason: Closing is explicitly not provided.
  Evidence [0]: The context manager neither implicitly opens a new transaction nor closes the connection.
- **2 SUPPORTED**: With check_same_thread=False, a sqlite3 connection may be shared across threads.
  Reason: The flag removes the same-thread restriction.
  Evidence [1]: If False, the connection may be accessed in multiple threads; write operations may need to be serialized by the user to avoid data corruption.
- **3 SUPPORTED**: When a sqlite3 connection is shared across threads, the caller may need to serialize writes.
  Reason: The user is responsible for possible write serialization.
  Evidence [1]: If False, the connection may be accessed in multiple threads; write operations may need to be serialized by the user to avoid data corruption.
- **4 UNSUPPORTED**: The sqlite3 module can optionally load SQLite extensions from shared libraries.
  Reason: The feature is real, but is in a different unprovided section.

Reviewer notes: ____________________

## python-zipfile (test; supported)

Human review: [ ] accepted  [ ] correction needed

ZIP64 archive support is on by default and is used when an archive exceeds 4 GiB. For a member whose size is unknown but could exceed 2 GiB, force_zip64=True prepares a suitable header. Deflate accepts levels zero through nine, while bzip2 starts at one; the setting does nothing for stored or LZMA members.

### Passage 0: [source](https://docs.python.org/3.13/library/zipfile.html)

If allowZip64 is True (the default) zipfile will create ZIP files that use the ZIP64 extensions when the zipfile is larger than 4 GiB. If it is false zipfile will raise an exception when the ZIP file would require ZIP64 extensions.

When writing a file, if the file size is not known in advance but may exceed 2 GiB, pass force_zip64=True to ensure that the header format is capable of supporting large files. If the file size is known in advance, construct a ZipInfo object with file_size set, and use that as the name parameter.

### Passage 1: [source](https://docs.python.org/3.13/library/zipfile.html)

The compresslevel parameter controls the compression level to use when writing files to the archive. When using ZIP_STORED or ZIP_LZMA it has no effect. When using ZIP_DEFLATED integers 0 through 9 are accepted (see zlib for more information). When using ZIP_BZIP2 integers 1 through 9 are accepted (see bz2 for more information).

### Passage 2: [source](https://docs.python.org/3.13/library/zipfile.html)

The Path class does not sanitize filenames within the ZIP archive. Unlike the ZipFile.extract() and ZipFile.extractall() methods, it is the caller’s responsibility to validate or sanitize filenames to prevent path traversal vulnerabilities (for example, absolute paths or paths with “..” components). When handling untrusted archives, consider resolving filenames using os.path.abspath() and checking against the target directory with os.path.commonpath().

- **0 SUPPORTED**: ZIP64 archive support is on by default.
  Reason: allowZip64 defaults to true.
  Evidence [0]: If allowZip64 is True (the default) zipfile will create ZIP files that use the ZIP64 extensions when the zipfile is larger than 4 GiB.
- **1 SUPPORTED**: ZIP64 extensions are used when an archive exceeds 4 GiB with allowZip64 enabled.
  Reason: The threshold is greater than 4 GiB.
  Evidence [0]: If allowZip64 is True (the default) zipfile will create ZIP files that use the ZIP64 extensions when the zipfile is larger than 4 GiB.
- **2 SUPPORTED**: For a member of unknown size that could exceed 2 GiB, force_zip64=True prepares a suitable header.
  Reason: The member-header recommendation has a separate 2 GiB boundary.
  Evidence [0]: When writing a file, if the file size is not known in advance but may exceed 2 GiB, pass force_zip64=True to ensure that the header format is capable of supporting large files.
- **3 SUPPORTED**: ZIP_DEFLATED accepts compression levels zero through nine.
  Reason: Both endpoints are included.
  Evidence [1]: When using ZIP_DEFLATED integers 0 through 9 are accepted (see zlib for more information).
- **4 SUPPORTED**: ZIP_BZIP2 accepts compression levels one through nine.
  Reason: Its lower bound differs from DEFLATED.
  Evidence [1]: When using ZIP_BZIP2 integers 1 through 9 are accepted (see bz2 for more information).
- **5 SUPPORTED**: compresslevel has no effect for ZIP_STORED or ZIP_LZMA.
  Reason: Both compression modes are exceptions.
  Evidence [1]: When using ZIP_STORED or ZIP_LZMA it has no effect.

Reviewer notes: ____________________
