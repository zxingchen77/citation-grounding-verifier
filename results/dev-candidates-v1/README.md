# Historical development experiment

This run used dataset version 2. It compares the staged candidate with compact
evidence-ID selection, after the initial minimal baseline in `dev-minimal-v1`.

Candidate disagreements revealed ambiguous upper-bound labels in the dataset.
An upper bound of 3 logically entails an upper bound of 4; the references had
instead treated both numbers as exact configured maxima. Dataset v3 clarifies
those development inputs. The three required methods are rerun in `dev-v3`.
Do not interpret these historical score differences as established quality gains
or losses. The original inputs, outputs and scores remain inspectable.

The staged system also combined two Birch distortion claims into one output;
one-to-one scoring leaves one reference unmatched. It used 48 model calls versus
24 for each single-call approach. Compact selection emitted 2,287 output tokens
versus the initial minimal baseline's 2,813; this is a resource-use observation,
not a quality conclusion from the ambiguous cases.
