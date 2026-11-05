-- APPLICATION_DATABASE_URL; never MLflow internal tables.
SELECT p.proposal_id,p.cycle_code,p.revision,p.status,p.payload_sha256,p.manifest_uri,
       count(o.offer_id) AS offers
FROM planning.ai_proposals_v2 p
JOIN planning.ai_proposal_offers_v2 o USING(proposal_id)
WHERE p.proposal_id=:proposal_id
GROUP BY p.proposal_id;
