# PRAHARI Alert and Review V1 Limitations

- Schedule and cost predictions are withheld; their registered alert types are inactive.
- Implementation Watch is deterministic observable pressure, not a causal diagnosis.
- Officer priority is an administrative queue field, not a probability or risk score.
- Authentication and role authorization remain deployment responsibilities; V1 preserves actor identity but does not provide an identity provider.
- Concurrent deduplication is protected by a unique database key; this is not a distributed event bus.
- Metrics describe workflow operations only and must not be presented as model-performance metrics.
- Synthetic sandbox episodes are isolated demonstrations and are not official evidence.
- Automatic resolution requires current evaluable clear evidence; unavailable months and missing updates cannot silently clear an episode.
- The first persistence threshold is policy-based and needs operational review after real officer usage.
- API pagination currently evaluates the filtered review collection in application memory; it is adequate for the prototype and should move to database-native JSON filtering at production scale.

