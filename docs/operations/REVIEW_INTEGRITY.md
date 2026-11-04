# Recoverable model governance and lineage status

The SQL-backed authorization and MLflow Registry alias are distinct systems. SQL
preparation commits a `RECONCILING` review checkpoint **before** mutating `champion`.
It revokes the old SQL APPROVED state first, so all new APPROVED-mode requests fail
closed while synchronization is incomplete.

After alias synchronization, a second SQL transaction finalizes the new APPROVED
state (or REVOKED after revocation). If Registry or SQL fails midway, the request
remains RECONCILING. **Retry the same approval_id** through the review endpoint
with `approve=true` and `confirm=REVIEW_EXPLICIT_VERSION` after checking the
current alias. Do not submit a new request until reconciliation completes. The
operation refuses unexpected external alias changes and never overwrites them.

Migration 009 introduces RECONCILING and RECORDED without deleting history.
New proposal usage references are persisted as RECORDED when identifiers and
artifact SHA are present, not VERIFIED. Live verification through
`GET /v1/audit/proposal/{proposal_id}` performs model/Registry, snapshot,
storage and manifest reconciliation. Historical immutable VERIFIED records are
not rewritten; their stored label is not authoritative.

Cache inventory is a presentation of the inference LRU and includes its loaded
versions, hashes and timestamps. It may be invalidated when cached models are
cleared for maintenance; it is not an approval authority.

## Validation
- Run unit tests and migration tests after rebuilding.
- In an isolated Compose stack, inject failures after SQL preparation and before
  MLflow alias mutation, and after alias mutation before final SQL commit.
- Confirm no APPROVED-mode inference is authorized until both stores agree.
- Retry RECONCILING request and confirm idempotent finalization.
- Confirm an unavailable/unexpected champion never results in silent approval.
- Verify new proposal rows have RECORDED; live audit can return VERIFIED.
- Confirm /internal/draft/cache matches actual LRU residency after >4 versions
  and after explicit cache_clear.
- Preserve existing MLflow runs, models and proposal rows.
