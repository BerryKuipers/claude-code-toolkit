# Delivery and evidence

Investigate the actual failure, implement the authorized fix and verify the affected behavior. State important findings without requiring a new confirmation for every root-cause hypothesis. Ask when a missing decision materially changes the task or an action lacks authorization.

Keep user data, credentials, native permissions and other sessions' work intact. Expose errors and incomplete behavior; never report simulated output as a working integration, bypass required checks, or suppress a failing path to make tests green. Intentional compatibility/migration paths are allowed when explicit and tested.

Verify delegated changes before claiming completion. Reconcile existing task records with the latest request and repository state; stale tasks do not override current instructions. Report the result, meaningful checks and concrete remaining limits, with bounded output rather than repeated full logs.
