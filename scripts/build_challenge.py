"""Author challenge-v1 without touching the original dataset or historical results.

Sentence-index references below are converted to literal sufficient evidence groups.
This is AI-authored synthetic data with author self-review (AI-assisted).
"""

import json
from pathlib import Path

from grounding.dataset import inspect_dataset

ROOT = Path(__file__).resolve().parents[1]
CASES = []
S, C, U = "SUPPORTED", "CONTRADICTED", "UNSUPPORTED"


def add(name, split, capabilities, semantics, paragraphs, answer, claims):
    gold = []
    for i, (text, verdict, rationale, refs) in enumerate(claims):
        gold.append(
            {
                "id": f"c{i}",
                "claim_text": text,
                "verdict": verdict,
                "rationale": rationale,
                "evidence_groups": [
                    [
                        {
                            "index": ref[0],
                            "quote": ref[2] if len(ref) == 3 else paragraphs[ref[0]][ref[1]],
                        }
                        for ref in refs
                    ]
                ]
                if refs
                else [],
            }
        )
    CASES.append(
        {
            "id": name,
            "family": name,
            "split": split,
            "category": capabilities[0],
            "capabilities": capabilities,
            "logical_semantics": semantics,
            "source": "Original synthetic scenario; AI-authored; CC0-1.0",
            "context_passages": [" ".join(p) for p in paragraphs],
            "generated_answer": answer,
            "gold_claims": gold,
        }
    )


add(
    "archive-release",
    "dev",
    ["conditions_exceptions", "scope_negation", "multi_passage"],
    "Legal holds override age-based release. Export and deletion are separate actions.",
    [
        [
            "The Meridian archive normally releases a record for deletion once it is 30 days old.",
            "A legal hold overrides that rule: a held record cannot be released for "
            "deletion at any age.",
            "Releasing a record is a permission change, not an instruction to erase "
            "the bytes immediately.",
        ],
        [
            "Record R17 is 45 days old and is currently under a legal hold.",
            "An auditor may export a held record after a supervisor signs the export request.",
            "The export leaves both the original record and its hold intact.",
        ],
        [
            "The operations guide gives no deadline for processing a signed export request.",
            "A different archive used for public newsletters automatically publishes "
            "monthly bundles; that service does not store Meridian records.",
        ],
    ],
    "R17 cannot be released for deletion. An auditor may export it after a supervisor "
    "signs the request, "
    "and that export removes its legal hold. A signed export request for R17 finishes "
    "within two hours.",
    [
        (
            "R17 cannot be released for deletion.",
            S,
            "The hold overrides age, and R17 is held.",
            [(0, 1), (1, 0)],
        ),
        (
            "An auditor may export R17 after a supervisor signs the request.",
            S,
            "The held-record permission applies to R17.",
            [(1, 0), (1, 1)],
        ),
        (
            "Exporting R17 removes its legal hold.",
            C,
            "Exports explicitly leave the held record and its hold intact.",
            [(1, 0), (1, 1), (1, 2)],
        ),
        (
            "A signed export request for R17 finishes within two hours.",
            U,
            "No completion time is specified.",
            [],
        ),
    ],
)

add(
    "batch-bound",
    "dev",
    ["logical_bounds", "scope_negation", "distractors"],
    "At most is a pure upper bound; it neither states an exact configured capacity nor"
    " proves attainability.",
    [
        [
            "The Beacon analysis guarantees that every batch contains at most 12 records.",
            "This is a proven upper bound, not a statement of the configured capacity "
            "or of any observed batch size.",
            "The analysis makes no claim that a batch of 12 records can actually occur.",
        ],
        [
            "The report also guarantees that every accepted record has a nonempty identifier.",
            "It does not constrain the identifier's alphabet or length.",
            "Rejected records are outside the identifier guarantee.",
        ],
        [
            "A training illustration depicts a batch with four colored boxes; the "
            "boxes are not measurements from Beacon.",
            "The downstream viewer can paginate a display into 20 rows, which does not"
            " change the analysis of batch size.",
        ],
    ],
    "Every Beacon batch contains at most 15 records, and at most 10 records. "
    "Beacon permits a batch with 13 records. Every accepted Beacon record has an identifier.",
    [
        (
            "Every Beacon batch contains at most 15 records.",
            S,
            "A bound of 12 entails the weaker bound of 15.",
            [(0, 0)],
        ),
        (
            "Every Beacon batch contains at most 10 records.",
            U,
            "A tighter bound is neither proved nor refuted by the bound of 12.",
            [],
        ),
        (
            "Beacon permits a batch with 13 records.",
            C,
            "A 13-record batch violates the universal upper bound.",
            [(0, 0)],
        ),
        (
            "Every accepted Beacon record has an identifier.",
            S,
            "The Beacon analysis identifies the report whose accepted-record guarantee is quoted.",
            [(0, 0), (1, 0)],
        ),
    ],
)

add(
    "listener-inventory",
    "dev",
    ["non_exclusive_facts", "exact_configuration", "distractors"],
    "An observed port is non-exclusive; an explicitly sole port is exclusive. Each "
    "applies to a different listener.",
    [
        [
            "A probe observed the public listener of the Kestrel relay accepting "
            "connections on port 8448.",
            "The probe checked only that port; it did not enumerate the listener's "
            "full port configuration.",
            "No statement in this inventory rules out additional public ports.",
        ],
        [
            "The relay's administrative listener has exactly one configured port, 9551.",
            "It rejects administrative connections on every other port.",
            "Public and administrative listeners are separate components, so the "
            "public probe does not describe administrative access.",
        ],
        [
            "A deployment example for an older simulator uses port 8449 for public traffic.",
            "That simulator is not the Kestrel relay, and the example is not an "
            "observation of its current deployment.",
        ],
    ],
    "Kestrel's public listener accepts connections on port 8448. It also accepts them "
    "on port 8449. "
    "Its administrative listener accepts administrative connections on port 9552, and "
    "has exactly one configured port.",
    [
        (
            "Kestrel's public listener accepts connections on port 8448.",
            S,
            "The probe directly observed this public port.",
            [(0, 0)],
        ),
        (
            "Kestrel's public listener accepts connections on port 8449.",
            U,
            "Another public port is neither confirmed nor excluded.",
            [],
        ),
        (
            "Kestrel's administrative listener accepts administrative connections on port 9552.",
            C,
            "The public probe identifies Kestrel as the relay; "
            "its admin listener rejects other ports.",
            [(0, 0), (1, 0), (1, 1)],
        ),
        (
            "Kestrel's administrative listener has exactly one configured port.",
            S,
            "The relay identity and its explicitly sole administrative port establish this.",
            [(0, 0), (1, 0)],
        ),
    ],
)

add(
    "release-cohorts",
    "dev",
    ["scope_negation", "conditions_exceptions", "distractors"],
    "Universal claims over all nodes are refuted by an explicit counterexample; "
    "absence of rollout timing is not a negative.",
    [
        [
            "The Nimbus fleet has two cohorts, copper and silver, and every node "
            "belongs to exactly one of them.",
            "In release 6, signed updates are mandatory for copper nodes.",
            "Silver nodes still accept unsigned updates in release 6.",
        ],
        [
            "Node T4 belongs to silver and successfully installed an unsigned "
            "release-6 update yesterday.",
            "An operator can voluntarily sign an update for either cohort.",
            "The rollout memo does not give a date for making signatures mandatory on silver.",
        ],
        [
            "The release-7 design draft proposes replacing the two cohorts with a single policy.",
            "The draft is a proposal only; it has not changed the current release-6 "
            "acceptance rules.",
        ],
    ],
    "All Nimbus nodes require signed updates in release 6. T4 can install unsigned "
    "release-6 updates, "
    "while copper nodes require signed release-6 updates. Silver nodes will require "
    "signatures next Monday.",
    [
        (
            "All Nimbus nodes require signed updates in release 6.",
            C,
            "T4 is a silver counterexample, and silver is explicitly a Nimbus cohort.",
            [(0, 0), (1, 0)],
        ),
        (
            "T4 can install unsigned release-6 updates.",
            S,
            "A successful installation directly demonstrates this capability.",
            [(1, 0)],
        ),
        (
            "Copper nodes require signed release-6 updates.",
            S,
            "This is the current copper rule.",
            [(0, 1)],
        ),
        (
            "Silver nodes will require signatures next Monday.",
            U,
            "No rollout date is committed.",
            [],
        ),
    ],
)

add(
    "mirror-residency",
    "dev",
    ["multi_passage", "conditions_exceptions", "scope_negation"],
    "Routing requires both an account-to-policy link and a residency override; general"
    " mirroring does not override residency.",
    [
        [
            "All ordinary payloads on route delta are mirrored to the North vault every night.",
            "A residency-locked payload on that route is instead mirrored only to the "
            "East vault and never to North.",
            "The override concerns payload content; operational counters are outside this rule.",
        ],
        [
            "The Solstice account sends all its payloads on route delta.",
            "Its invoice payloads are residency-locked, while its catalog payloads are"
            " ordinary payloads.",
            "No other payload types are described in the account note.",
        ],
        [
            "Both vaults acknowledge completed writes to an operations ledger.",
            "The ledger entry contains a payload identifier and destination, but the "
            "documentation does not describe encryption of vault contents.",
        ],
    ],
    "Solstice invoices are mirrored to North every night. Its invoices are mirrored only to East, "
    "and its catalogs are mirrored to North nightly. Its invoice mirrors are encrypted at rest.",
    [
        (
            "Solstice invoices are mirrored to North every night.",
            C,
            "The routing link and locked status activate the explicit no-North override.",
            [(0, 1), (1, 0), (1, 1)],
        ),
        (
            "Solstice invoices are mirrored only to East.",
            S,
            "The residency override, routing link and type mapping jointly establish "
            "the destination.",
            [(0, 1), (1, 0), (1, 1)],
        ),
        (
            "Solstice catalogs are mirrored to North nightly.",
            S,
            "Catalogs are ordinary payloads on delta.",
            [(0, 0), (1, 0), (1, 1)],
        ),
        (
            "Solstice invoice mirrors are encrypted at rest.",
            U,
            "A write ledger says nothing about encryption.",
            [],
        ),
    ],
)

add(
    "alias-handoff",
    "dev",
    ["paraphrase_coreference", "multi_passage", "distractors"],
    "Aliases identify the same component only where explicitly mapped. Accepting a "
    "transfer does not imply destruction of its source.",
    [
        [
            "In the Heliograph operator guide, 'the courier' is the component whose "
            "service identifier is HX-2.",
            "HX-2 hands a completed bundle to the receiving spool before acknowledging"
            " the transfer.",
            "HX-2 acknowledges as soon as the spool accepts the bundle and does not "
            "wait for end-user delivery.",
        ],
        [
            "After the courier acknowledges a transfer, it retains its source bundle for one day.",
            "The receiving spool and the source bundle are distinct copies.",
            "The guide does not state how long a bundle remains in the receiving spool.",
        ],
        [
            "A component named the messenger appears in a separate training diagram.",
            "The guide never identifies the messenger as HX-2, and the diagram's "
            "immediate-deletion rule applies only to the messenger.",
        ],
    ],
    "HX-2 waits for spool acceptance before acknowledging a transfer, but it waits for"
    " end-user delivery too. "
    "The courier keeps its source bundle for one day after acknowledgment. The "
    "receiving spool retains a bundle for seven days.",
    [
        (
            "HX-2 waits for spool acceptance before acknowledging a transfer.",
            S,
            "The handoff and acceptance precede the acknowledgment.",
            [(0, 1), (0, 2)],
        ),
        (
            "HX-2 waits for end-user delivery before acknowledging a transfer.",
            C,
            "The guide explicitly excludes that wait.",
            [(0, 2)],
        ),
        (
            "The courier keeps its source bundle for one day after acknowledgment.",
            S,
            "The retention interval is explicit.",
            [(1, 0)],
        ),
        (
            "The receiving spool retains a bundle for seven days.",
            U,
            "Source retention cannot establish spool retention.",
            [],
        ),
    ],
)

add(
    "lease-race",
    "dev",
    ["conditions_exceptions", "scope_negation", "multi_passage"],
    "Cancellation has a defined linearization boundary; requesting cancellation is "
    "distinct from cancellation taking effect.",
    [
        [
            "In the Plover scheduler, a cancellation takes effect if its request "
            "reaches the scheduler before the job commits its lease.",
            "Once a lease is committed, later cancellation requests are recorded but "
            "do not stop that job.",
            "An effective cancellation prevents the job from starting; a recorded "
            "request alone carries no such guarantee.",
        ],
        [
            "Job J8 committed its lease at 10:04:00, and its cancellation request "
            "arrived at 10:04:01.",
            "Job J9 received a cancellation request before committing any lease.",
            "The event log contains no completion timestamp for either job.",
        ],
        [
            "The dashboard groups effective cancellations and late requests under a "
            "single 'cancellation activity' counter.",
            "That aggregate counter is a UI summary rather than evidence that every "
            "counted job stopped.",
        ],
    ],
    "The cancellation request stopped J8. J9 is prevented from starting, and J8's late"
    " request is recorded. J8 finished at 10:05:00.",
    [
        (
            "The cancellation request stopped J8.",
            C,
            "J8's request was after commit, so it did not stop the job.",
            [(0, 1), (1, 0)],
        ),
        (
            "J9 is prevented from starting.",
            S,
            "The before-commit request takes effect and prevents starting.",
            [(0, 0), (0, 2), (1, 1)],
        ),
        (
            "J8's late cancellation request is recorded.",
            S,
            "Post-commit requests are recorded even though ineffective.",
            [(0, 1), (1, 0)],
        ),
        ("J8 finished at 10:05:00.", U, "No completion timestamp is present.", []),
    ],
)

add(
    "latency-population",
    "dev",
    ["scope_negation", "logical_bounds", "distractors"],
    "A median is not a per-request upper bound. Observed rates apply to the stated sample only.",
    [
        [
            "The Marlin trial measured 100 requests on a private test cluster during a"
            " single ten-minute window.",
            "Their median completion time was 40 milliseconds, and one measured "
            "request took 90 milliseconds.",
            "All 100 measured requests completed successfully.",
        ],
        [
            "The trial did not sample the public production cluster or publish a "
            "service-level guarantee.",
            "Only completion time was measured; the record contains no CPU or energy measurements.",
            "The engineers retained the slow request in the sample rather than "
            "treating it as an outlier.",
        ],
        [
            "A separate tuning proposal targets a median of 25 milliseconds in a later experiment.",
            "That target is not an achieved result and does not change the "
            "measurements in this trial.",
        ],
    ],
    "The trial's median completion time was 40 milliseconds. Every measured request "
    "finished within 40 milliseconds. "
    "All measured requests succeeded. Marlin's production median is 40 milliseconds.",
    [
        (
            "The trial's median completion time was 40 milliseconds.",
            S,
            "The sample definition resolves the statistic’s antecedent; its median is reported.",
            [(0, 0), (0, 1)],
        ),
        (
            "Every measured request finished within 40 milliseconds.",
            C,
            "The measured 90-millisecond request is a counterexample.",
            [(0, 1)],
        ),
        (
            "All measured requests succeeded.",
            S,
            "Success is reported for the entire measured sample.",
            [(0, 2)],
        ),
        (
            "Marlin's production median is 40 milliseconds.",
            U,
            "The trial did not measure production.",
            [],
        ),
    ],
)

add(
    "delegation-permissions",
    "dev",
    ["conditions_exceptions", "scope_negation", "multi_passage"],
    "The authorization rule is a biconditional; meeting only one of two prerequisites "
    "is insufficient.",
    [
        [
            "A non-owner can approve a Lumen transfer if and only if that person has "
            "both an active delegation and a current training certificate.",
            "Owners can approve transfers without those two prerequisites.",
            "The rule governs approval, not the separate act of initiating a transfer.",
        ],
        [
            "Mira is a non-owner with an active delegation and a current training certificate.",
            "Leon is a non-owner with an active delegation but no current training certificate.",
            "The roster gives no ownership, delegation or training information about Suri.",
        ],
        [
            "The transfer screen displays an Approve button to every logged-in person.",
            "Visibility of the button is not an authorization grant; the server "
            "applies the stated rule when a person submits an approval.",
        ],
    ],
    "Mira may approve a Lumen transfer, and Leon may approve one. "
    "Owners may approve transfers without training certificates. Suri may approve transfers.",
    [
        (
            "Mira may approve a Lumen transfer.",
            S,
            "Both prerequisites and non-owner status are supplied.",
            [(0, 0), (1, 0)],
        ),
        (
            "Leon may approve a Lumen transfer.",
            C,
            "Leon lacks a necessary certificate under the iff rule.",
            [(0, 0), (1, 1)],
        ),
        (
            "Owners may approve Lumen transfers without training certificates.",
            S,
            "The owner exception waives the two prerequisites defined in the preceding rule.",
            [(0, 0), (0, 1)],
        ),
        (
            "Suri may approve Lumen transfers.",
            U,
            "The roster gives none of Suri's relevant attributes.",
            [],
        ),
    ],
)

add(
    "quota-dimensions",
    "dev",
    ["exact_configuration", "logical_bounds", "scope_negation"],
    "A configured maximum is exact, but a lower bound on available capacity is not "
    "exact usage. Per-project and per-user scopes differ.",
    [
        [
            "The Vireo workspace has exactly three projects, and each project has an "
            "independently configured maximum of eight active tasks.",
            "There is no shared workspace task cap beyond those project caps.",
            "A task belongs to exactly one project, so the same task is not counted "
            "under multiple caps.",
        ],
        [
            "At the observation time, project A had at least two active tasks.",
            "The observation did not record A's exact count or any user's task count.",
            "Project names label task ownership, not the human users who submitted tasks.",
        ],
        [
            "The interface can show up to ten task cards on a page.",
            "Pagination is a display setting and is unrelated to admission limits or "
            "the number of currently active tasks.",
        ],
    ],
    "Each Vireo project has a configured maximum of nine active tasks. The workspace "
    "can have at most 24 active tasks. "
    "Project A had at least one active task at the observation time. Project A had "
    "exactly two active tasks then.",
    [
        (
            "Each Vireo project has a configured maximum of nine active tasks.",
            C,
            "The exact configured maximum is eight.",
            [(0, 0)],
        ),
        (
            "The Vireo workspace can have at most 24 active tasks.",
            S,
            "Three disjoint projects each bounded by eight imply the total bound.",
            [(0, 0), (0, 2)],
        ),
        (
            "Project A had at least one active task at the observation time.",
            S,
            "At least two entails at least one.",
            [(1, 0)],
        ),
        (
            "Project A had exactly two active tasks at the observation time.",
            U,
            "A lower bound does not fix the exact count.",
            [],
        ),
    ],
)

add(
    "receipt-semantics",
    "dev",
    ["non_exclusive_facts", "paraphrase_coreference", "conditions_exceptions"],
    "Receipt acceptance and durable commit are separate states. A listed "
    "implementation detail is not an exhaustive inventory.",
    [
        [
            "An Osprey receipt certifies that the intake has accepted a submission "
            "into volatile memory.",
            "A receipt does not certify that the submission has reached durable storage.",
            "Only a later commit acknowledgment certifies that durable-storage step.",
        ],
        [
            "Submission Q6 has a receipt but has not received a commit acknowledgment.",
            "The intake's implementation note mentions use of a checksum when "
            "validating submissions.",
            "The note is not an exhaustive list of validation steps and says nothing "
            "about which checksum algorithm is used.",
        ],
        [
            "The client calls the receipt an 'acceptance ticket'; both names refer to "
            "the same object.",
            "A reconnect tutorial for a different product uses the word ticket for "
            "authentication, but Osprey's acceptance ticket is not that tutorial's "
            "object.",
        ],
    ],
    "An Osprey acceptance ticket certifies durable storage. Q6 has been accepted into "
    "volatile memory. "
    "Osprey uses a checksum in submission validation. Its checksum algorithm is SHA-256. "
    "Q6 has a receipt, but no commit acknowledgment.",
    [
        (
            "An Osprey acceptance ticket certifies durable storage.",
            C,
            "The Osprey receipt definition, client alias and explicit "
            "non-durability rule are all needed.",
            [(0, 0), (0, 1), (2, 0)],
        ),
        (
            "Q6 has been accepted into volatile memory.",
            S,
            "Q6's receipt establishes the intake acceptance state.",
            [(0, 0), (1, 0)],
        ),
        (
            "Osprey uses a checksum in submission validation.",
            S,
            "The Osprey intake is identified by its receipt definition; "
            "its note states the checksum fact.",
            [(0, 0), (1, 1)],
        ),
        ("Osprey's checksum algorithm is SHA-256.", U, "The algorithm is not specified.", []),
        ("Q6 has a receipt.", S, "The submission state explicitly records a receipt.", [(1, 0)]),
        (
            "Q6 has no commit acknowledgment.",
            S,
            "The submission has not received that acknowledgment.",
            [(1, 0)],
        ),
    ],
)

add(
    "compatibility-matrix",
    "dev",
    ["multi_passage", "scope_negation", "distractors"],
    "Version support attaches to a specific format and reader pair. A format's "
    "existence does not imply every reader supports it.",
    [
        [
            "The Seabird writer emits format R when its legacy switch is off and "
            "format L when that switch is on.",
            "The current deployment has the legacy switch off.",
            "The switch chooses one output format; the writer does not emit both "
            "formats for the same record.",
        ],
        [
            "Reader Pine accepts format R but rejects format L.",
            "Reader Ash accepts format L but rejects format R.",
            "Reader Oak is listed in the fleet inventory, but no compatibility entry "
            "is provided for it.",
        ],
        [
            "A migration utility can convert R records into L records when explicitly run.",
            "No conversion utility runs in the current deployment; reader "
            "compatibility must therefore be assessed against the writer's original "
            "output.",
        ],
    ],
    "Pine accepts the current Seabird output, and Ash accepts that output too. "
    "The current Seabird writer emits format R. Oak accepts format R.",
    [
        (
            "Pine accepts the current Seabird output.",
            S,
            "The off switch selects R, which Pine accepts.",
            [(0, 0), (0, 1), (1, 0)],
        ),
        (
            "Ash accepts the current Seabird output.",
            C,
            "Current output is R and Ash rejects R; no conversion intervenes.",
            [(0, 0), (0, 1), (1, 1), (2, 1)],
        ),
        (
            "The current Seabird writer emits format R.",
            S,
            "The current switch value selects R.",
            [(0, 0), (0, 1)],
        ),
        ("Oak accepts format R.", U, "An inventory entry is not a compatibility guarantee.", []),
    ],
)

# Held-out scenarios cover the same reasoning abilities in different domains.
# They are authored and structurally checked here; no test model calls are made.
add(
    "museum-loans",
    "test",
    ["conditions_exceptions", "scope_negation", "multi_passage"],
    "Inspection is necessary for outward loans, and fragility is an overriding "
    "prohibition; insurance is a separate property.",
    [
        [
            "The Calder museum may lend an object outward only after that object "
            "passes an inspection.",
            "Objects marked fragile cannot leave the museum on loan, even after a "
            "successful inspection.",
            "A passing inspection by itself does not guarantee that any loan "
            "application will be approved.",
        ],
        [
            "The blue vase passed inspection but remains marked fragile.",
            "The brass clock passed inspection and is not marked fragile; its loan "
            "application is still undecided.",
            "The ledger does not report insurance arrangements for either object.",
        ],
        [
            "Visitors can see fragile objects in the museum's permanent gallery.",
            "Public display inside the building is distinct from an outward loan and "
            "does not waive the fragile-object rule.",
        ],
    ],
    "The blue vase may leave the museum on loan. It passed inspection and is marked fragile. "
    "The brass clock's loan application has not been decided. The brass clock is "
    "insured for outward loans.",
    [
        (
            "The blue vase may leave the museum on loan.",
            C,
            "The fragile flag activates the prohibition despite the inspection.",
            [(0, 1), (1, 0)],
        ),
        (
            "The blue vase passed inspection.",
            S,
            "The ledger records a passing inspection.",
            [(1, 0)],
        ),
        ("The blue vase is marked fragile.", S, "The current ledger states the flag.", [(1, 0)]),
        (
            "The brass clock's loan application has not been decided.",
            S,
            "Its application is explicitly undecided.",
            [(1, 1)],
        ),
        (
            "The brass clock is insured for outward loans.",
            U,
            "Insurance information is absent.",
            [],
        ),
    ],
)

add(
    "reservoir-interval",
    "test",
    ["logical_bounds", "scope_negation", "distractors"],
    "The reported interval is inclusive uncertainty about one level, not an exact "
    "measurement or a capacity specification.",
    [
        [
            "The Alder reservoir's noon report establishes that its water level was at"
            " least 18 metres and at most 23 metres.",
            "Both endpoints are included in this uncertainty interval; the report does"
            " not identify the exact level.",
            "The numbers describe water level above the local datum, not reservoir "
            "depth or storage capacity.",
        ],
        [
            "A second instrument was offline at noon, so it supplied no additional "
            "constraint on the interval.",
            "The report gives no level measurements for the following hour.",
            "An older engineering sketch marks a 25-metre maintenance platform, which "
            "is not a water-level observation.",
        ],
        [
            "The dashboard labels the interval as a validated bound.",
            "Its midpoint display is a visualization aid and is not claimed to be the "
            "actual noon water level.",
        ],
    ],
    "Alder's noon water level was at least 17 metres, and it was exactly 20 metres. "
    "Its noon water level was 24 metres. Its noon water level was no more than 23 metres.",
    [
        (
            "Alder's noon water level was at least 17 metres.",
            S,
            "The lower bound of 18 entails the weaker lower bound of 17.",
            [(0, 0)],
        ),
        (
            "Alder's noon water level was exactly 20 metres.",
            U,
            "Twenty is possible within the interval but not established.",
            [],
        ),
        (
            "Alder's noon water level was 24 metres.",
            C,
            "Twenty-four exceeds the inclusive upper bound.",
            [(0, 0)],
        ),
        (
            "Alder's noon water level was no more than 23 metres.",
            S,
            "This restates the upper bound.",
            [(0, 0)],
        ),
    ],
)

add(
    "radio-channels",
    "test",
    ["non_exclusive_facts", "exact_configuration", "scope_negation"],
    "Reception observed on one frequency is non-exclusive; the emergency transmitter's"
    " sole configured frequency is exclusive.",
    [
        [
            "At the harbor station, a survey detected the research receiver receiving "
            "broadcasts on channel 11.",
            "The survey sampled channel 11 only and did not enumerate other channels "
            "the receiver could receive.",
            "A receiver's observed channel does not determine the emergency "
            "transmitter's configuration.",
        ],
        [
            "The emergency transmitter is configured to transmit on channel 6 only.",
            "It cannot transmit on any other channel under the current configuration.",
            "This is the complete current transmission configuration, not a sample "
            "from a monitoring session.",
        ],
        [
            "A sailing-club handbook mentions research broadcasts on channel 12 at another harbor.",
            "The handbook gives no information about reception at this station or its "
            "emergency transmitter.",
        ],
    ],
    "The station's research receiver receives channel 11 broadcasts and can receive "
    "channel 12 broadcasts. "
    "Its emergency transmitter can transmit on channel 7. The emergency transmitter's "
    "sole configured channel is 6.",
    [
        (
            "The station's research receiver receives channel 11 broadcasts.",
            S,
            "Reception was observed on this channel.",
            [(0, 0)],
        ),
        (
            "The station's research receiver can receive channel 12 broadcasts.",
            U,
            "Another harbor and an untested channel do not resolve this receiver's capability.",
            [],
        ),
        (
            "The station's emergency transmitter can transmit on channel 7.",
            C,
            "The current transmitter cannot use channels other than 6.",
            [(1, 0), (1, 1)],
        ),
        (
            "The station's emergency transmitter's sole configured channel is 6.",
            S,
            "The complete configuration explicitly establishes exclusivity.",
            [(1, 0)],
        ),
    ],
)

add(
    "scholarship-scope",
    "test",
    ["scope_negation", "conditions_exceptions", "distractors"],
    "A rule for one enrollment class does not extend to all students; an explicit "
    "part-time example refutes that extension.",
    [
        [
            "The Fenwick institute enrolls both full-time and part-time students in "
            "its certificate course.",
            "The 2026 travel grant is available to every full-time certificate student"
            " who submits a receipt.",
            "Part-time certificate students are ineligible for that grant, even if "
            "they submit receipts.",
        ],
        [
            "Nora is a part-time certificate student and submitted a travel receipt.",
            "Ivo is a full-time certificate student and submitted a travel receipt.",
            "The grant bulletin makes no commitment about next year's eligibility rules.",
        ],
        [
            "A separate library-access program includes both enrollment classes.",
            "Library access is not a travel grant and does not change the grant's "
            "eligibility condition.",
        ],
    ],
    "Every certificate student with a receipt is eligible for the 2026 travel grant. "
    "Nora is ineligible, "
    "while Ivo is eligible. Part-time students will be eligible for the 2027 travel grant.",
    [
        (
            "Every certificate student with a receipt is eligible for the 2026 travel grant.",
            C,
            "Nora is a receipt-holding counterexample under the exclusion "
            "for the identified 2026 grant.",
            [(0, 1), (0, 2), (1, 0)],
        ),
        (
            "Nora is ineligible for the 2026 travel grant.",
            S,
            "Her part-time status invokes the exclusion for the identified 2026 grant.",
            [(0, 1), (0, 2), (1, 0)],
        ),
        (
            "Ivo is eligible for the 2026 travel grant.",
            S,
            "His full-time status and receipt satisfy the rule.",
            [(0, 1), (1, 1)],
        ),
        (
            "Part-time students will be eligible for the 2027 travel grant.",
            U,
            "Future rules are unspecified.",
            [],
        ),
    ],
)

add(
    "specimen-routing",
    "test",
    ["multi_passage", "conditions_exceptions", "scope_negation"],
    "A handling exception overrides the general route based on a specimen's recorded "
    "condition; custody does not imply test results.",
    [
        [
            "The laboratory's routine route sends dry mineral specimens to Room B for "
            "optical analysis.",
            "A specimen marked moisture-sensitive is routed to sealed Room D instead, "
            "regardless of its routine route.",
            "Moisture-sensitive specimens are never opened in Room B.",
        ],
        [
            "The west excavation's mineral specimens all use the routine dry-mineral route.",
            "Specimen W3 from that excavation is marked moisture-sensitive; specimen "
            "W4 has no such mark and is classified as routine dry material.",
            "The shipping list records custody transfers only, with no composition measurements.",
        ],
        [
            "Room B also receives ordinary glass standards for instrument calibration.",
            "Those standards are not excavation specimens and their calibration "
            "certificates do not describe W3 or W4.",
        ],
    ],
    "W3 is routed to Room D. W4 is routed to Room B, and W3 is opened in Room B. W3 "
    "contains quartz.",
    [
        (
            "W3 is routed to Room D.",
            S,
            "Its moisture-sensitive mark activates the overriding route.",
            [(0, 1), (1, 1)],
        ),
        (
            "W4 is routed to Room B.",
            S,
            "Its explicit routine dry classification and the general routing rule suffice.",
            [
                (0, 0),
                (1, 1, "specimen W4 has no such mark and is classified as routine dry material."),
            ],
        ),
        (
            "W3 is opened in Room B.",
            C,
            "Its mark invokes the explicit no-opening rule.",
            [(0, 2), (1, 1)],
        ),
        (
            "W3 contains quartz.",
            U,
            "Custody records and unrelated standards do not establish composition.",
            [],
        ),
    ],
)

add(
    "registry-supersession",
    "test",
    ["paraphrase_coreference", "multi_passage", "scope_negation"],
    "Entity aliases preserve identity across a rename, but dated ownership records "
    "supersede older ownership only, not the entity identifier.",
    [
        [
            "The city registry identifies building B-19 by the former name Bell House "
            "and the current name Lantern House.",
            "Both names refer to the same physical building and registry identifier, "
            "not to two adjacent properties.",
            "The registry uses dated transfers to determine current ownership; a later"
            " completed transfer supersedes the previous owner's entry.",
        ],
        [
            "An entry dated March 1 records Orin Trust as owner of B-19.",
            "A completed transfer dated April 12 records Vale Cooperative as the new "
            "owner of B-19, and there are no later transfers.",
            "The name change to Lantern House occurred on April 20 without changing "
            "the building identifier.",
        ],
        [
            "A brochure lists a roof renovation at Bell House but gives neither its "
            "completion date nor the contractor.",
            "A nearby property called Lantern Lodge is separately registered as B-91 "
            "and is still owned by Orin Trust.",
        ],
    ],
    "Bell House and Lantern House are the same building. Orin Trust currently owns Lantern House. "
    "It retains identifier B-19, and Vale Cooperative currently owns it. Its roof "
    "renovation was completed in April.",
    [
        (
            "Bell House and Lantern House are the same building.",
            S,
            "The registry explicitly equates both names.",
            [(0, 0), (0, 1)],
        ),
        (
            "Orin Trust currently owns Lantern House.",
            C,
            "The final completed transfer supersedes Orin's older ownership; the alias"
            " identifies B-19.",
            [(0, 0), (0, 2), (1, 1)],
        ),
        (
            "Lantern House retains identifier B-19.",
            S,
            "The registry alias and unchanged identifier establish this.",
            [(0, 0), (1, 2)],
        ),
        (
            "Vale Cooperative currently owns Lantern House.",
            S,
            "Vale is the latest completed owner of the aliased building.",
            [(0, 0), (0, 2), (1, 1)],
        ),
        (
            "Lantern House's roof renovation was completed in April.",
            U,
            "The renovation brochure gives no completion date.",
            [],
        ),
    ],
)

add(
    "ballot-cutoff",
    "test",
    ["conditions_exceptions", "multi_passage", "scope_negation"],
    "Eligibility depends on receipt, not dispatch, with a specified inclusive cutoff. "
    "Being late does not prove who cast a ballot.",
    [
        [
            "A completed ballot in the Toren election is counted if and only if the "
            "election desk receives it by 18:00:00 on election day.",
            "The cutoff is inclusive: a ballot received exactly at 18:00:00 is on time.",
            "Dispatch time does not replace receipt time when applying this rule.",
        ],
        [
            "Completed ballot B4 was dispatched at 17:59:00 but reached the desk at 18:00:01.",
            "Completed ballot B5 reached the desk at exactly 18:00:00.",
            "The anonymized timing log omits the voters' names and does not link "
            "ballot identifiers to people.",
        ],
        [
            "The postal desk prints dispatch timestamps on envelopes as a tracking aid.",
            "Those timestamps explain transit delays but do not create an exception to"
            " the counting rule.",
        ],
    ],
    "B4 is counted. B5 is counted. A receipt at exactly 18:00:00 is on time. B4 was cast by Rowan.",
    [
        (
            "B4 is counted.",
            C,
            "Its receipt was one second late under the iff rule.",
            [(0, 0), (1, 0)],
        ),
        (
            "B5 is counted.",
            S,
            "Its completed ballot arrived at the inclusive cutoff.",
            [(0, 0), (0, 1), (1, 1)],
        ),
        (
            "A receipt at exactly 18:00:00 is on time.",
            S,
            "The endpoint is explicitly included.",
            [(0, 1)],
        ),
        ("B4 was cast by Rowan.", U, "The timing log provides no voter identity.", []),
    ],
)

add(
    "survey-denominators",
    "test",
    ["scope_negation", "logical_bounds", "distractors"],
    "Respondents are a strict subset of invitees. Percentages require the specified "
    "denominator, and nonresponse has no imputed opinion.",
    [
        [
            "The town invited exactly 200 households to a transport survey, and "
            "exactly 80 households responded.",
            "Of the respondents, 60 favored the new bus route and 20 opposed it; each "
            "respondent chose exactly one of those options.",
            "The survey recorded no opinion from the 120 households that did not respond.",
        ],
        [
            "The published headline says that three quarters of respondents favored the route.",
            "The analysts explicitly declined to impute the missing households' opinions.",
            "A household's failure to reply is not recorded as either support or opposition.",
        ],
        [
            "A separate bicycle petition obtained 150 signatures from individuals, "
            "some of whom share households.",
            "Its signatories and question differ from the bus survey, so its total is "
            "not a bus-route vote count.",
        ],
    ],
    "Seventy-five percent of survey respondents favored the bus route. Seventy-five "
    "percent of invited households recorded support. "
    "Exactly 120 invited households did not respond. Most nonresponding households "
    "opposed the route. At least 60 invited households favored the route.",
    [
        (
            "Seventy-five percent of survey respondents favored the bus route.",
            S,
            "Sixty of eighty respondents is three quarters.",
            [(0, 0), (0, 1)],
        ),
        (
            "Seventy-five percent of invited households recorded support for the bus route.",
            C,
            "Only sixty of two hundred invitees recorded support, which is thirty percent.",
            [(0, 0), (0, 1), (0, 2)],
        ),
        (
            "Exactly 120 invited households did not respond.",
            S,
            "The invitation and response counts differ by 120, also explicitly stated.",
            [(0, 0)],
        ),
        (
            "Most nonresponding households opposed the bus route.",
            U,
            "Their unrecorded opinions cannot be inferred from silence.",
            [],
        ),
        (
            "At least 60 invited households favored the bus route.",
            S,
            "The sixty favorable respondents are members of the invited set.",
            [(0, 0), (0, 1)],
        ),
    ],
)

add(
    "evacuation-logic",
    "test",
    ["conditions_exceptions", "scope_negation", "multi_passage"],
    "An alarm is sufficient but not necessary for evacuation. A controller's two "
    "explicit triggers are exhaustive, and one failed trigger does not negate the "
    "other.",
    [
        [
            "The Vale hall evacuation controller activates when either the smoke alarm"
            " sounds or the duty officer presses the evacuation switch.",
            "These are its only two activation triggers, and either one is sufficient "
            "without the other.",
            "The smoke alarm sounding is therefore not a prerequisite when the duty "
            "officer uses the switch.",
        ],
        [
            "During drill D7 the smoke alarm remained silent, but the duty officer "
            "pressed the evacuation switch.",
            "During drill D8 the alarm remained silent and nobody pressed the switch.",
            "The drill log records controller inputs only; it does not record the time"
            " taken for people to leave.",
        ],
        [
            "A demonstration panel in the visitor center flashes whenever its test "
            "button is pressed.",
            "That panel is not connected to the hall controller, and its button is not"
            " an additional evacuation trigger.",
        ],
    ],
    "The evacuation controller activated during D7. It activated during D8 too. "
    "D7's evacuation took less than three minutes. The smoke alarm must sound for the "
    "controller to activate.",
    [
        (
            "The evacuation controller activated during D7.",
            S,
            "The officer's switch is independently sufficient and was pressed.",
            [(0, 0), (0, 1), (1, 0)],
        ),
        (
            "The evacuation controller activated during D8.",
            C,
            "Neither of its exhaustive triggers occurred.",
            [(0, 0), (0, 1), (1, 1)],
        ),
        (
            "D7's evacuation took less than three minutes.",
            U,
            "No departure timing is reported.",
            [],
        ),
        (
            "The smoke alarm must sound for the evacuation controller to activate.",
            C,
            "The switch can activate it without an alarm.",
            [(0, 0), (0, 1)],
        ),
    ],
)

add(
    "training-overlap",
    "test",
    ["logical_bounds", "exact_configuration", "scope_negation"],
    "Course totals are exact set cardinalities, but their unreported intersection is "
    "not assumed empty. A union is bounded by the sum.",
    [
        [
            "The Rook team has exactly 20 employees. Exactly 12 completed the safety "
            "course and exactly 11 completed the equipment course.",
            "An employee can complete both courses, and the report does not identify "
            "how many did so.",
            "Only team employees are included in either course total, and each "
            "employee is counted once per completed course.",
        ],
        [
            "The course report has no attendance dates and no list linking names to "
            "completed courses.",
            "Completion of the safety course is permanent in this report; the numbers "
            "are not attendance slots or repeat enrollments.",
            "A training room has 24 seats, but seat capacity is not the number of "
            "people who completed a course.",
        ],
        [
            "The manager wants to arrange refresher training after reviewing the overlap.",
            "That proposed follow-up does not supply the missing overlap count or "
            "establish that anyone completed neither course.",
        ],
    ],
    "At least three Rook employees completed both courses. No Rook employee completed "
    "both courses. "
    "Exactly five employees completed both courses. Exactly 12 employees completed the"
    " safety course. At most 20 employees completed at least one course.",
    [
        (
            "At least three Rook employees completed both courses.",
            S,
            "The intersection is at least 12 + 11 - 20 = 3.",
            [(0, 0), (0, 2)],
        ),
        (
            "No Rook employee completed both courses.",
            C,
            "Disjoint course sets would require 23 distinct employees in a team of 20.",
            [(0, 0), (0, 2)],
        ),
        (
            "Exactly five Rook employees completed both courses.",
            U,
            "Five is possible, but the intersection is not fixed.",
            [],
        ),
        (
            "Exactly 12 Rook employees completed the safety course.",
            S,
            "This exact total is reported.",
            [(0, 0)],
        ),
        (
            "At most 20 Rook employees completed at least one course.",
            S,
            "Both course sets are subsets of the twenty-person team.",
            [(0, 0), (0, 2)],
        ),
    ],
)

add(
    "lab-badges",
    "test",
    ["non_exclusive_facts", "paraphrase_coreference", "multi_passage"],
    "A witnessed access permission is a non-exclusive fact. A nickname is an identity "
    "link, while task assignment does not grant undocumented access.",
    [
        [
            "The observatory's visitor log calls technician Ren 'the calibrator'; this"
            " is Ren's nickname, not a job shared by several technicians.",
            "A supervised access trial showed Ren's badge opening laboratory A on Tuesday.",
            "The trial tested laboratory A only and made no statement about the "
            "badge's permissions for other laboratories.",
        ],
        [
            "The current badge registry explicitly denies Ren access to the chemical store.",
            "The registry lists a spectrometer calibration assignment for Ren but does"
            " not identify which laboratory contains the instrument.",
            "Assignments do not themselves change badge permissions; those permissions"
            " are administered separately.",
        ],
        [
            "Technician Renn, whose name has a second n, has chemical-store access.",
            "Renn is a different person from Ren, so that entry cannot be used as the "
            "calibrator's permission record.",
        ],
    ],
    "The calibrator's badge opened laboratory A on Tuesday. It also grants access to laboratory B. "
    "Ren has access to the chemical store. Ren is assigned to spectrometer calibration.",
    [
        (
            "The calibrator's badge opened laboratory A on Tuesday.",
            S,
            "The nickname identifies Ren, whose badge was observed opening A.",
            [(0, 0), (0, 1)],
        ),
        (
            "The calibrator's badge grants access to laboratory B.",
            U,
            "One successful trial on A is non-exclusive and does not establish B.",
            [],
        ),
        (
            "Ren has access to the chemical store.",
            C,
            "The current registry explicitly denies Ren this access; Renn is different.",
            [(1, 0)],
        ),
        (
            "Ren is assigned to spectrometer calibration.",
            S,
            "The assignment is explicitly listed.",
            [(1, 1)],
        ),
    ],
)

add(
    "package-dependencies",
    "test",
    ["multi_passage", "conditions_exceptions", "distractors"],
    "Dependencies are conjunctive and transitive. An optional theme is not a "
    "prerequisite, and absence of a necessary dependency prevents launch.",
    [
        [
            "The Cobalt editor can launch only when both the Render library and the "
            "Text library are installed and working.",
            "Render works only when the Pixel runtime is installed; installing Render "
            "does not automatically install Pixel.",
            "A theme package is optional and is not needed for the editor to launch.",
        ],
        [
            "Machine M2 has Render and Text installed but does not have Pixel installed.",
            "Machine M3 has all three libraries or runtimes installed and no theme package.",
            "The guide gives necessary dependencies only; it does not claim that "
            "satisfying them rules out every other launch failure.",
        ],
        [
            "A troubleshooting article for the unrelated Copper editor says a theme is mandatory.",
            "Copper's requirement does not apply to Cobalt, and neither guide "
            "documents Cobalt's memory consumption.",
        ],
    ],
    "M2 can launch Cobalt. Pixel is a necessary dependency for Cobalt. "
    "A theme package is mandatory for Cobalt to launch. M3 is guaranteed to launch "
    "successfully. Cobalt consumes less than one gigabyte of memory.",
    [
        (
            "M2 can launch Cobalt.",
            C,
            "The required Render dependency cannot work without the missing Pixel runtime.",
            [(0, 0), (0, 1), (1, 0)],
        ),
        (
            "Pixel is a necessary dependency for Cobalt.",
            S,
            "The editor requires working Render, which requires Pixel.",
            [(0, 0), (0, 1)],
        ),
        (
            "A theme package is mandatory for Cobalt to launch.",
            C,
            "The guide explicitly says it is optional.",
            [(0, 2)],
        ),
        (
            "M3 is guaranteed to launch Cobalt successfully.",
            U,
            "Meeting necessary conditions alone is not a success guarantee.",
            [],
        ),
        (
            "Cobalt consumes less than one gigabyte of memory.",
            U,
            "Memory consumption is not specified.",
            [],
        ),
    ],
)


# Reference-only audit: this self-contained sentence also establishes the order.
# Retain the original two-sentence group as an alternative; model inputs are unchanged.
alias_case = next(c for c in CASES if c["id"] == "alias-handoff")
alias_case["gold_claims"][0]["evidence_groups"].append(
    [
        {
            "index": 0,
            "quote": (
                "HX-2 acknowledges as soon as the spool accepts the bundle "
                "and does not wait for end-user delivery."
            ),
        }
    ]
)


if __name__ == "__main__":
    folder = ROOT / "data/challenge-v1"
    folder.mkdir(exist_ok=True)
    path = folder / "cases.jsonl"
    path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in CASES))
    manifest = {
        "version": "challenge-v1",
        "reference_revision": 2,
        "reference_revision_note": (
            "Reference-only evidence audit after initial dev inference; "
            "original references retained. All model inputs, verdicts "
            "and held-out records unchanged."
        ),
        "source": "Original synthetic scenarios; AI-authored",
        "license": "CC0-1.0",
        "annotation_review": "author self-review (AI-assisted)",
        "test_inference_status": "Not run; requires a separate user decision",
        **inspect_dataset(path),
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
