"""Materialize AI-assisted synthetic cases with explicit, reviewable reference labels."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = []


def add(family, split, category, passages, claims, answer=None):
    gold = []
    for i, (text, verdict, evidence_indices) in enumerate(claims):
        gold.append(
            {
                "id": f"c{i}",
                "claim_text": text,
                "verdict": verdict,
                "evidence_groups": [[{"index": k, "quote": passages[k]} for k in evidence_indices]]
                if evidence_indices
                else [],
            }
        )
    CASES.append(
        {
            "id": f"{family}-{category}",
            "family": family,
            "split": split,
            "category": category,
            "source": "Original synthetic specification; CC0-1.0",
            "context_passages": passages,
            "generated_answer": answer or " ".join(c[0] for c in claims),
            "gold_claims": gold,
        }
    )


# Each pair stays in the same split. These are invented specifications, not claims
# about real products. Exact passages intentionally make citation auditing possible.
simple = [
    (
        "maple-cache",
        "dev",
        [
            "Maple cache entries expire 12 minutes after creation.",
            "Reading a Maple cache entry does not extend its expiration time.",
        ],
        [
            "Maple cache entries expire 13 minutes after creation.",
            "Reading a Maple cache entry extends its expiration time.",
        ],
    ),
    (
        "birch-queue",
        "dev",
        [
            "A Birch queue's configured capacity is exactly 64 pending jobs.",
            "A full Birch queue rejects new jobs rather than deleting existing jobs.",
        ],
        [
            "A Birch queue's configured capacity is exactly 63 pending jobs.",
            "A full Birch queue accepts new jobs by deleting existing jobs.",
        ],
    ),
    (
        "sable-upload",
        "dev",
        [
            "The configured maximum size of a Sable upload is exactly 8 MiB.",
            "Sable uploads require a checksum before the server acknowledges success.",
        ],
        [
            "The configured maximum size of a Sable upload is exactly 9 MiB.",
            "Sable uploads acknowledge success without requiring a checksum.",
        ],
    ),
    (
        "cedar-audit",
        "dev",
        [
            "Cedar audit logging is available only on Enterprise plans.",
            "Cedar audit logs are retained for 7 days.",
        ],
        [
            "Cedar audit logging is available on every plan.",
            "Cedar audit logs are retained for 30 days.",
        ],
    ),
    (
        "elm-retry",
        "dev",
        [
            "Elm retries requests only when the response status is 503.",
            "Elm's configured limit is exactly 3 total attempts, including the initial request.",
        ],
        [
            "Elm retries requests when the response status is 504.",
            "Elm's configured limit is exactly 4 total attempts, including the initial request.",
        ],
    ),
    (
        "willow-session",
        "dev",
        [
            "Willow sessions expire after 20 minutes of inactivity.",
            "Willow revokes all existing sessions when the account password changes.",
        ],
        [
            "Willow sessions expire after 21 minutes of inactivity.",
            "Willow preserves all existing sessions when the account password changes.",
        ],
    ),
    (
        "granite-checkpoint",
        "test",
        [
            "Granite checkpoints its journal after 128 new pages by default.",
            "Granite checkpointing requires the primary node to be writable.",
        ],
        [
            "Granite checkpoints its journal after 127 new pages by default.",
            "Granite checkpointing requires the primary node to be read-only.",
        ],
    ),
    (
        "quartz-tls",
        "test",
        [
            "The Quartz gateway listens on port 7443.",
            "The Quartz gateway requires clients to present a certificate.",
        ],
        [
            "The Quartz gateway listens on port 7444.",
            "The Quartz gateway permits clients without a certificate.",
        ],
    ),
    (
        "opal-backup",
        "test",
        [
            "Opal backups start at 02:00 UTC each day.",
            "Opal deletes backups once they are more than 8 days old.",
        ],
        [
            "Opal backups start at 03:00 UTC each day.",
            "Opal deletes backups once they are more than 9 days old.",
        ],
    ),
    (
        "jasper-role",
        "test",
        [
            "Only Jasper workspace owners can export billing records.",
            "Jasper billing exports contain the previous 6 months of records.",
        ],
        [
            "All Jasper workspace members can export billing records.",
            "Jasper billing exports contain the previous 12 months of records.",
        ],
    ),
]

for family, split, passages, wrong in simple:
    supported = [(s, "SUPPORTED", [i]) for i, s in enumerate(passages)]
    distorted = [(s, "CONTRADICTED", [i]) for i, s in enumerate(wrong)]
    if family == "birch-queue":
        supported = [
            supported[0],
            ("A full Birch queue rejects new jobs.", "SUPPORTED", [1]),
            (
                "A full Birch queue does not delete existing jobs to accept new jobs.",
                "SUPPORTED",
                [1],
            ),
        ]
        distorted = [
            distorted[0],
            ("A full Birch queue accepts new jobs.", "CONTRADICTED", [1]),
            ("A full Birch queue deletes existing jobs to accept new jobs.", "CONTRADICTED", [1]),
        ]
    # Some answers place two independent facts in one sentence.
    supported_answer = passages[0][:-1] + "; " + passages[1][0].lower() + passages[1][1:]
    distorted_answer = wrong[0][:-1] + "; " + wrong[1][0].lower() + wrong[1][1:]
    add(family, split, "supported", passages, supported, supported_answer)
    add(family, split, "distortion", passages, distorted, distorted_answer)

multi = [
    (
        "nova-profile",
        "dev",
        [
            "Nova requests use the interactive timeout profile.",
            "The interactive timeout profile cancels requests after 300 milliseconds.",
            "The batch timeout profile cancels requests after 30 seconds.",
        ],
        "Nova requests are cancelled after 300 milliseconds.",
        ["Nova traffic is encrypted with AES-256.", "Nova servers run on Linux."],
    ),
    (
        "moss-region",
        "dev",
        [
            "Moss stores all customer snapshots in region West.",
            "Snapshots stored in region West are copied to region North nightly.",
            "Snapshots stored in region South are copied weekly.",
        ],
        "Moss customer snapshots are copied to region North nightly.",
        [
            "Moss customer snapshots are compressed with Zstandard.",
            "Moss customers can download snapshots using SFTP.",
        ],
    ),
    (
        "fern-keys",
        "dev",
        [
            "Fern tenants use key policy K2.",
            "Key policy K2 requires encryption keys to rotate every 45 days.",
            "Key policy K1 requires rotation every 90 days.",
        ],
        "Fern tenants must rotate their encryption keys every 45 days.",
        [
            "Fern uses hardware security modules for key storage.",
            "Fern has passed an independent security audit.",
        ],
    ),
    (
        "reed-failover",
        "dev",
        [
            "Reed runs in the silver availability tier.",
            "Silver tier instances require operator approval before failover.",
            "Gold tier instances perform automatic failover.",
        ],
        "Reed requires operator approval before failover.",
        [
            "Reed is deployed in three availability zones.",
            "Reed guarantees zero data loss during failover.",
        ],
    ),
    (
        "clover-version",
        "dev",
        [
            "Clover uses protocol version 4.",
            "Protocol version 4 supports resuming interrupted uploads.",
            "Protocol version 3 supports only restarting uploads from the beginning.",
        ],
        "Clover supports resuming interrupted uploads.",
        [
            "Clover supports uploading files from mobile devices.",
            "Clover deduplicates identical uploaded files.",
        ],
    ),
    (
        "aster-transactions",
        "dev",
        [
            "Aster workers connect through the strict transaction pool.",
            "Connections in the strict transaction pool use serializable isolation.",
            "Connections in the relaxed transaction pool use read-committed isolation.",
        ],
        "Aster workers use serializable transaction isolation.",
        [
            "Aster workers use PostgreSQL as their database.",
            "Aster workers persist transaction logs on SSDs.",
        ],
    ),
    (
        "lyra-compression",
        "test",
        [
            "Lyra archives use the compact storage class.",
            "The compact storage class compresses archives using algorithm LZ4.",
            "The dense storage class uses algorithm Zstandard.",
        ],
        "Lyra archives are compressed using LZ4.",
        [
            "Lyra archives are encrypted before compression.",
            "Lyra archives can be searched by document title.",
        ],
    ),
    (
        "vega-quota",
        "test",
        [
            "Vega service accounts belong to quota class C.",
            "Quota class C permits 80 requests per minute per account.",
            "Quota class D permits 120 requests per minute per account.",
        ],
        "Vega service accounts may make 80 requests per minute per account.",
        [
            "Vega service accounts authenticate with OAuth tokens.",
            "Vega service account credentials expire every month.",
        ],
    ),
    (
        "altair-vault",
        "test",
        [
            "Altair recovery copies are written to vault Indigo.",
            "Vault Indigo makes recovery copies immutable for 14 days.",
            "Vault Amber makes recovery copies immutable for 28 days.",
        ],
        "Altair recovery copies remain immutable for 14 days.",
        [
            "Altair recovery copies are kept on magnetic tape.",
            "Altair verifies recovery copies using SHA-256.",
        ],
    ),
    (
        "deneb-index",
        "test",
        [
            "Deneb search indexes are assigned to shard group R.",
            "Shard group R maintains 3 replicas of every assigned search index.",
            "Shard group S maintains 2 replicas of every assigned search index.",
        ],
        "Deneb search indexes each have 3 replicas.",
        [
            "Deneb search indexes use a B-tree data structure.",
            "Deneb search indexes support fuzzy matching.",
        ],
    ),
]

for family, split, passages, synthesis, extrinsic in multi:
    add(family, split, "multi_passage", passages, [(synthesis, "SUPPORTED", [0, 1])])
    add(family, split, "extrinsic", passages, [(s, "UNSUPPORTED", []) for s in extrinsic])

if __name__ == "__main__":
    path = ROOT / "data" / "cases.jsonl"
    path.parent.mkdir(exist_ok=True)
    payload = "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in CASES)
    path.write_text(payload)
    manifest = {
        "version": 3,
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "cases": len(CASES),
        "splits": dict(Counter(c["split"] for c in CASES)),
        "categories": dict(Counter(c["category"] for c in CASES)),
        "claim_labels": dict(Counter(g["verdict"] for c in CASES for g in c["gold_claims"])),
        "source": "Original synthetic specifications",
        "license": "CC0-1.0",
    }
    (ROOT / "data" / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
