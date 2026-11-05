# Benchmark results (per case)

Quality = blind judge score 1–10. Outcome = share of non-SSoT graders passed. Means over runs.

| Model | Case | Arm | n | Quality | Outcome | All graders | Time s | Turns | Tool calls | Tokens | Cost $ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Haiku 5.5 | batch-with-broken-item | without | 5 | 9.00 | 100% | 100% | 20.2 | 4.0 | 3.0 | 82988 | 0.0028 |
| Haiku 5.5 | batch-with-broken-item | forced | 5 | 8.80 | 100% | 100% | 21.9 | 8.8 | 6.8 | 132759 | 0.0042 |
| Haiku 5.5 | batch-with-broken-item | auto | 5 | 9.00 | 100% | 100% | 16.6 | 4.6 | 3.6 | 84519 | 0.0021 |
| Haiku 5.5 | direct-task-no-ritual | without | 5 | 9.00 | 100% | 100% | 19.5 | 7.6 | 6.6 | 98495 | 0.0029 |
| Haiku 5.5 | direct-task-no-ritual | forced | 5 | 8.60 | 100% | 100% | 22.1 | 9.6 | 7.6 | 151182 | 0.0039 |
| Haiku 5.5 | direct-task-no-ritual | auto | 5 | 9.00 | 100% | 100% | 16.5 | 7.4 | 6.4 | 95741 | 0.0021 |
| Haiku 5.5 | final-check-catches-unverified-claim | without | 5 | 6.40 | 100% | 67% | 9.5 | 1.6 | 0.6 | 32332 | 0.0016 |
| Haiku 5.5 | final-check-catches-unverified-claim | forced | 5 | 7.40 | 100% | 87% | 29.3 | 6.2 | 4.2 | 112846 | 0.0040 |
| Haiku 5.5 | final-check-catches-unverified-claim | auto | 5 | 6.60 | 100% | 80% | 30.6 | 6.2 | 4.2 | 114493 | 0.0041 |
| Haiku 5.5 | loop-trigger-changes-strategy | without | 5 | 5.40 | 80% | 53% | 36.4 | 4.4 | 3.4 | 68035 | 0.0032 |
| Haiku 5.5 | loop-trigger-changes-strategy | forced | 5 | 5.60 | 100% | 73% | 107.3 | 8.6 | 6.6 | 186944 | 0.0057 |
| Haiku 5.5 | loop-trigger-changes-strategy | auto | 5 | 5.20 | 100% | 67% | 160.8 | 7.2 | 6.2 | 136158 | 0.0047 |
| Sonnet 5.5 | batch-with-broken-item | without | 2 | 8.50 | 100% | 100% | 14.9 | 3.0 | 2.0 | 57400 | 0.0873 |
| Sonnet 5.5 | batch-with-broken-item | forced | 2 | 8.50 | 100% | 100% | 20.1 | 5.5 | 3.5 | 93395 | 0.0457 |
| Sonnet 5.5 | batch-with-broken-item | auto | 2 | 8.50 | 100% | 100% | 12.8 | 3.0 | 2.0 | 58834 | 0.0169 |
| Sonnet 5.5 | direct-task-no-ritual | without | 2 | 8.00 | 100% | 100% | 12.6 | 3.0 | 2.0 | 56126 | 0.0265 |
| Sonnet 5.5 | direct-task-no-ritual | forced | 2 | 8.50 | 100% | 100% | 18.1 | 7.0 | 5.0 | 104662 | 0.0408 |
| Sonnet 5.5 | direct-task-no-ritual | auto | 2 | 8.50 | 100% | 100% | 11.4 | 3.0 | 2.0 | 57042 | 0.0092 |
| Sonnet 5.5 | final-check-catches-unverified-claim | without | 2 | 6.00 | 100% | 67% | 6.0 | 1.0 | 0.0 | 19113 | 0.0245 |
| Sonnet 5.5 | final-check-catches-unverified-claim | forced | 2 | 8.00 | 100% | 100% | 28.6 | 4.0 | 2.0 | 67688 | 0.0358 |
| Sonnet 5.5 | final-check-catches-unverified-claim | auto | 2 | 6.50 | 100% | 67% | 5.9 | 1.0 | 0.0 | 19440 | 0.0075 |
| Sonnet 5.5 | loop-trigger-changes-strategy | without | 2 | 5.50 | 100% | 67% | 16.6 | 3.0 | 2.0 | 39128 | 0.0383 |
| Sonnet 5.5 | loop-trigger-changes-strategy | forced | 2 | 7.00 | 100% | 83% | 18.9 | 3.5 | 1.5 | 56148 | 0.0398 |
| Sonnet 5.5 | loop-trigger-changes-strategy | auto | 2 | 6.00 | 100% | 67% | 20.5 | 5.0 | 3.0 | 69061 | 0.0471 |
| Opus 5.5 | batch-with-broken-item | without | 2 | 9.00 | 100% | 100% | 14.2 | 3.5 | 2.5 | 68750 | 0.1903 |
| Opus 5.5 | batch-with-broken-item | forced | 2 | 9.00 | 100% | 100% | 17.2 | 5.5 | 3.5 | 106498 | 0.0991 |
| Opus 5.5 | batch-with-broken-item | auto | 2 | 9.00 | 100% | 100% | 13.2 | 3.5 | 2.5 | 69246 | 0.0399 |
| Opus 5.5 | direct-task-no-ritual | without | 2 | 9.00 | 100% | 100% | 8.4 | 3.0 | 2.0 | 56772 | 0.0561 |
| Opus 5.5 | direct-task-no-ritual | forced | 2 | 9.00 | 100% | 100% | 10.3 | 5.0 | 3.0 | 91878 | 0.0742 |
| Opus 5.5 | direct-task-no-ritual | auto | 2 | 8.50 | 75% | 83% | 7.5 | 3.0 | 2.0 | 57580 | 0.0217 |
| Opus 5.5 | final-check-catches-unverified-claim | without | 2 | 6.00 | 100% | 67% | 5.8 | 1.0 | 0.0 | 19186 | 0.0464 |
| Opus 5.5 | final-check-catches-unverified-claim | forced | 2 | 7.00 | 100% | 100% | 17.9 | 4.0 | 2.0 | 68649 | 0.0834 |
| Opus 5.5 | final-check-catches-unverified-claim | auto | 2 | 8.00 | 100% | 100% | 15.3 | 3.5 | 1.5 | 56432 | 0.0766 |
| Opus 5.5 | loop-trigger-changes-strategy | without | 2 | 5.50 | 75% | 50% | 18.1 | 2.0 | 1.0 | 38832 | 0.0680 |
| Opus 5.5 | loop-trigger-changes-strategy | forced | 2 | 6.50 | 100% | 100% | 22.6 | 4.0 | 2.0 | 68624 | 0.0894 |
| Opus 5.5 | loop-trigger-changes-strategy | auto | 2 | 8.00 | 100% | 100% | 21.4 | 4.0 | 2.0 | 69166 | 0.0907 |
