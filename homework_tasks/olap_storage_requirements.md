# Storage Layer Requirements — General + OLAP (Column-Store, “Own Format”)

Source: project spec in `2_storage.pdf`. fileciteturn0file0

---

## 1) Goal (applies to both tracks)

Implement a minimal but *real* storage engine that: stores tables on disk in a defined physical format, supports CRUD (insert/read/update/delete), persists across restarts, keeps schema metadata consistent, and implements at least one storage organization strategy. fileciteturn1file4L1-L9

You must pick one track, but both must expose the same logical API. fileciteturn1file4L10-L13

---

## 2) Common API contract (required)

Your storage module must provide (names illustrative): fileciteturn1file4L18-L28

- `create_table(table_name, schema)`
- `drop_table(table_name)` *(optional but recommended)*
- `open_table(table_name) -> TableHandle`
- `insert(table, record) -> RID`
- `get(table, rid) -> record | null`
- `update(table, rid, new_record) -> bool`
- `delete(table, rid) -> bool`
- `scan(table) -> iterator/stream of (RID, record)` *(needed for sequential scans)*

---

## 3) Data model requirements (required)

You must support: fileciteturn1file4L29-L33

- Fixed-length types (e.g., `INT`, `FLOAT`)
- Variable-length types (e.g., `VARCHAR`, `TEXT`)
- Optional: any other types you choose

---

## 4) General storage requirements (required)

### 4.1 Fixed-size blocks/pages + layout doc
- Implement a fixed page size “block/page structure”. fileciteturn1file4L35-L37
- Define and document page header + payload layout. fileciteturn1file4L36-L37

### 4.2 Correct CRUD + varlen safety
- Insert/read/update/delete must work correctly. fileciteturn1file4L38-L41
- Must handle fixed + variable-length records. fileciteturn1file4L39-L41
- Varlen must be handled safely (e.g., length prefixes, offsets, or indirection). fileciteturn1file1L1-L4

### 4.3 Schema/metadata persistence + restart correctness
- Persist schema so that on restart, tables can be reopened with correct types/columns. fileciteturn1file1L4-L6

### 4.4 Pick at least one storage organization strategy (required)
Choose *one* strategy (or justify another): fileciteturn1file1L6-L13

- Heap files (free-space management + page directory)
- Hash-based storage
- B+Tree-backed table or index
- LSM-like append + compaction
- Self-implemented index over Parquets
- Or another justified approach

### 4.5 Advanced features (optional, but recommended)
Pick at least one (recommended): fileciteturn1file1L13-L25

- Compression (OLAP-friendly): dictionary / delta / RLE / bit-packing on at least one column type fileciteturn1file1L15-L17
- Zone maps / min-max stats per segment/page for scan skipping (strongly encouraged for OLAP) fileciteturn1file1L18-L19
- PAX page layout (hybrid) fileciteturn1file1L20-L21
- Crash-safety-lite: atomic file replace for metadata/manifest, checksums, or WAL skeleton fileciteturn1file1L22-L23
- Micro-benchmarks demonstrating a tradeoff fileciteturn1file1L24-L25

---

## 5) OLAP track requirements (Track B: Column-store / “own format”) — required

Track B is append-optimized, columnar layout for scan-heavy analytics; Parquet is allowed, but you may also implement your own format. fileciteturn1file4L15-L17

### 5.1 Physical layout (DSM core)
For a custom (“own”) columnar format, your physical design must include: fileciteturn1file0L13-L19

- Table decomposed into **per-column storage** (separate files or separate regions/segments).
- Each stored value is associated with a **Record ID (RID) / position** so rows can be reconstructed (“late materialization / tuple reconstruction” conceptually).
- Explicitly document your RID scheme (e.g., dense `0..N-1`, or stable RID with free-list).

### 5.2 Update/delete semantics for immutable/append segments
Because OLAP-friendly columnar segments are often immutable, implement update/delete via a **delta layer** and merge-on-read: fileciteturn1file0L31-L37

- Base segments are **immutable** (e.g., row groups / segment files)
- **Updates**: append a new version keyed by RID or primary key
- **Deletes**: maintain a delete bitmap or “position delete” list per segment
- **Reads** (`get` and `scan`) must merge base + delta logically

*(This mirrors real OLAP systems where write-optimized deltas are reconciled later via compaction/merge.)* fileciteturn1file0L36-L37

### 5.3 OLAP optimizations (recommended, but very aligned)
- Projection-aware reads: if a query needs only some columns, avoid reading others. fileciteturn1file0L38-L40
- Stats per row group / segment (min/max) for skipping. fileciteturn1file0L40-L41
- Encoding/compression (dictionary/RLE/delta/bit-pack) even simplified. fileciteturn1file0L42-L42

### 5.4 Compression requirement (if you do compression)
If you implement compression, use at least one technique (RLE, Dictionary, Delta, Bit-packing), and document: encoding choice, decode cost, and integration with scans. fileciteturn1file0L20-L24

---

## 6) “Own format” checklist (what you must define/document)

This is not extra scope—it's the concrete checklist you should write down as your “format spec” so you can implement + test the required behaviors above.

### 6.1 Table directory layout
Define a table root directory/file containing:
- **Catalog entry** (schema + table name)
- **Manifest / metadata** file that lists segments (and their column chunks), encodings, and stats  
  *(Crash-safety-lite can be implemented here via atomic replace/checksums.)* fileciteturn1file1L22-L23
- **Segment files** (append-only base) + **delta files**
- Optional: per-column files vs multi-column “container” file (your choice), but must be “per-column storage” logically. fileciteturn1file0L13-L16

### 6.2 RID scheme + row reconstruction
Document:
- RID format (dense position, or stable ID + free-list) fileciteturn1file0L18-L19
- How you map RID → (segment, row_index) and reconstruct a full record from columns (during `get` and during `scan`).

### 6.3 Delta layer for updates/deletes
Define:
- Update records: (RID or PK, changed columns, new values, version/timestamp)
- Delete records: per-segment bitmap or position delete list fileciteturn1file0L33-L35
- Read path merge rules for `get` and `scan` fileciteturn1file0L35-L36
- Compaction/merge strategy (even simple): when and how deltas get folded into new immutable segments fileciteturn1file0L36-L37

### 6.4 Scan behavior + projection
Define:
- Column reader that can read only requested columns (projection) fileciteturn1file0L38-L40
- Iterator/stream interface for `scan(table) -> (RID, record)` fileciteturn1file4L27-L28

### 6.5 Stats / zone maps (recommended for OLAP)
For each segment (or “row group”), store min/max per column to skip reading segments that can’t match. fileciteturn1file0L40-L41

### 6.6 Page/block requirement (still applies)
Even if you store column chunks, you still need a fixed-size “page/block structure” + documented header/payload layout somewhere in your system (e.g., for your segment blocks). fileciteturn1file4L35-L37

---

## 7) Deliverables + tests (required)

You must ship: fileciteturn1file0L43-L54

1. Code: storage module + CLI or test harness
2. README/design doc including:
   - chosen track + rationale (workload assumptions)
   - on-disk layout description (diagrams encouraged)
3. RID semantics
4. How restart/recovery is handled (even if minimal)
5. Complexity notes (insert/update/delete/scan)
6. Tests:
   - correctness tests for CRUD + restart
   - edge cases (varlen boundaries, page-full behavior, delete tombstones, etc.)
7. Demo script proving persistence + API correctness
