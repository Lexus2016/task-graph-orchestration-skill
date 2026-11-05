# Benchmark results (per task)

Quality = blind judge score as % of ideal (score × 10). Outcome = share of task criteria passed (SSoT-format criteria excluded). Means over runs.
Tokens are split by billing class: uncached input, cache write, cache read, output.

| Model | Task | Arm | n | Quality | Outcome | Time s | Turns | Tool calls | Uncached in | Cache write | Cache read | Output | Cost $ | Skill used |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Haiku 5.5 | batch-with-broken-item | without | 5 | 90% | 100% | 20.2 | 4.0 | 3.0 | 8 | 6139 | 75171 | 1670 | 0.0028 | 0% |
| Haiku 5.5 | batch-with-broken-item | forced | 5 | 90% | 100% | 13.9 | 7.6 | 5.6 | 11 | 7374 | 101356 | 1964 | 0.0035 | 100% |
| Haiku 5.5 | batch-with-broken-item | auto | 5 | 90% | 100% | 12.5 | 5.2 | 4.2 | 8 | 1963 | 80401 | 1664 | 0.0020 | 0% |
| Haiku 5.5 | direct-task-no-ritual | without | 5 | 88% | 100% | 19.5 | 7.6 | 6.6 | 10 | 6180 | 90824 | 1481 | 0.0029 | 0% |
| Haiku 5.5 | direct-task-no-ritual | forced | 5 | 86% | 100% | 14.0 | 9.2 | 7.2 | 13 | 7521 | 127005 | 1943 | 0.0037 | 100% |
| Haiku 5.5 | direct-task-no-ritual | auto | 5 | 90% | 100% | 11.6 | 7.2 | 6.2 | 9 | 1876 | 92077 | 1454 | 0.0020 | 0% |
| Haiku 5.5 | final-check-catches-unverified-claim | without | 5 | 76% | 100% | 9.5 | 1.6 | 0.6 | 3 | 4552 | 26845 | 932 | 0.0016 | 0% |
| Haiku 5.5 | final-check-catches-unverified-claim | forced | 5 | 78% | 100% | 45.0 | 7.0 | 5.0 | 13 | 9669 | 137151 | 2875 | 0.0047 | 100% |
| Haiku 5.5 | final-check-catches-unverified-claim | auto | 5 | 74% | 100% | 35.0 | 3.0 | 2.0 | 4 | 2565 | 43697 | 1507 | 0.0017 | 0% |
| Haiku 5.5 | loop-trigger-changes-strategy | without | 5 | 58% | 100% | 36.4 | 4.4 | 3.4 | 6 | 7271 | 58524 | 2234 | 0.0032 | 0% |
| Haiku 5.5 | loop-trigger-changes-strategy | forced | 5 | 58% | 100% | 157.8 | 8.4 | 6.4 | 15 | 11622 | 163699 | 3430 | 0.0057 | 100% |
| Haiku 5.5 | loop-trigger-changes-strategy | auto | 5 | 58% | 100% | 136.6 | 6.4 | 5.4 | 10 | 6830 | 110016 | 3297 | 0.0041 | 0% |
| Haiku 5.5 | partly-done-migration | without | 5 | 90% | 100% | 12.5 | 4.0 | 3.0 | 8 | 6652 | 75718 | 1328 | 0.0028 | 0% |
| Haiku 5.5 | partly-done-migration | forced | 5 | 90% | 100% | 15.2 | 6.0 | 4.0 | 11 | 7917 | 101851 | 1650 | 0.0034 | 100% |
| Haiku 5.5 | partly-done-migration | auto | 5 | 90% | 100% | 15.0 | 5.0 | 4.0 | 9 | 2955 | 94851 | 1702 | 0.0024 | 0% |
| Haiku 5.5 | programming-multifile-fix | without | 5 | 90% | 100% | 18.4 | 7.4 | 6.4 | 9 | 8595 | 90289 | 3149 | 0.0042 | 0% |
| Haiku 5.5 | programming-multifile-fix | forced | 5 | 86% | 100% | 21.4 | 11.4 | 9.4 | 13 | 10272 | 131755 | 3792 | 0.0053 | 100% |
| Haiku 5.5 | programming-multifile-fix | auto | 5 | 90% | 100% | 18.5 | 7.6 | 6.6 | 9 | 4316 | 95704 | 3179 | 0.0034 | 0% |
| Haiku 5.5 | research-conflicting-sources | without | 5 | 90% | 100% | 15.0 | 5.4 | 4.4 | 7 | 7714 | 67378 | 2534 | 0.0035 | 0% |
| Haiku 5.5 | research-conflicting-sources | forced | 5 | 90% | 100% | 17.1 | 8.4 | 6.4 | 10 | 9007 | 91877 | 2916 | 0.0042 | 100% |
| Haiku 5.5 | research-conflicting-sources | auto | 5 | 90% | 100% | 15.6 | 4.4 | 3.4 | 7 | 3359 | 72561 | 2480 | 0.0026 | 0% |
| Haiku 5.5 | vendor-contracts-review | without | 5 | 90% | 100% | 41.0 | 14.6 | 13.6 | 14 | 85284 | 304618 | 6863 | 0.0727 | 0% |
| Haiku 5.5 | vendor-contracts-review | forced | 5 | 88% | 100% | 50.8 | 13.8 | 20.0 | 16 | 58851 | 299716 | 7469 | 0.0474 | 100% |
| Haiku 5.5 | vendor-contracts-review | auto | 5 | 90% | 100% | 43.1 | 16.0 | 15.0 | 16 | 85797 | 383448 | 7467 | 0.0785 | 0% |
| Sonnet 5.5 | batch-with-broken-item | without | 2 | 90% | 100% | 14.9 | 3.0 | 2.0 | 6 | 19322 | 37447 | 626 | 0.0873 | 0% |
| Sonnet 5.5 | batch-with-broken-item | forced | 2 | 85% | 100% | 16.6 | 5.0 | 3.0 | 10 | 6282 | 86192 | 934 | 0.0431 | 100% |
| Sonnet 5.5 | batch-with-broken-item | auto | 2 | 90% | 100% | 13.6 | 3.0 | 2.0 | 6 | 1023 | 57047 | 668 | 0.0165 | 0% |
| Sonnet 5.5 | direct-task-no-ritual | without | 2 | 85% | 100% | 12.6 | 3.0 | 2.0 | 6 | 4728 | 51144 | 248 | 0.0265 | 0% |
| Sonnet 5.5 | direct-task-no-ritual | forced | 2 | 90% | 100% | 14.0 | 7.5 | 5.5 | 11 | 6217 | 98850 | 786 | 0.0426 | 100% |
| Sonnet 5.5 | direct-task-no-ritual | auto | 2 | 90% | 100% | 9.6 | 3.0 | 2.0 | 6 | 281 | 56589 | 269 | 0.0095 | 0% |
| Sonnet 5.5 | final-check-catches-unverified-claim | without | 2 | 80% | 100% | 6.0 | 1.0 | 0.0 | 2 | 4501 | 14102 | 508 | 0.0245 | 0% |
| Sonnet 5.5 | final-check-catches-unverified-claim | forced | 2 | 85% | 100% | 12.8 | 4.0 | 2.0 | 8 | 5374 | 61954 | 885 | 0.0366 | 100% |
| Sonnet 5.5 | final-check-catches-unverified-claim | auto | 2 | 70% | 100% | 5.0 | 1.0 | 0.0 | 2 | 0 | 18881 | 513 | 0.0070 | 0% |
| Sonnet 5.5 | loop-trigger-changes-strategy | without | 2 | 60% | 100% | 16.6 | 3.0 | 2.0 | 4 | 5017 | 32606 | 1502 | 0.0384 | 0% |
| Sonnet 5.5 | loop-trigger-changes-strategy | forced | 2 | 60% | 100% | 17.4 | 4.5 | 2.5 | 8 | 5866 | 61756 | 1474 | 0.0444 | 100% |
| Sonnet 5.5 | loop-trigger-changes-strategy | auto | 2 | 60% | 50% | 19.4 | 5.0 | 3.0 | 8 | 6020 | 61839 | 1514 | 0.0454 | 100% |
| Sonnet 5.5 | partly-done-migration | without | 2 | 90% | 100% | 16.2 | 3.0 | 2.0 | 6 | 5633 | 51946 | 588 | 0.0336 | 0% |
| Sonnet 5.5 | partly-done-migration | forced | 2 | 90% | 100% | 13.1 | 6.0 | 4.0 | 10 | 6936 | 87955 | 716 | 0.0437 | 100% |
| Sonnet 5.5 | partly-done-migration | auto | 2 | 90% | 100% | 16.4 | 4.0 | 3.0 | 8 | 1954 | 77942 | 882 | 0.0244 | 0% |
| Sonnet 5.5 | programming-multifile-fix | without | 2 | 85% | 100% | 23.1 | 3.5 | 2.5 | 7 | 6008 | 61961 | 1185 | 0.0421 | 0% |
| Sonnet 5.5 | programming-multifile-fix | forced | 2 | 90% | 100% | 23.1 | 9.0 | 7.0 | 12 | 7448 | 113090 | 1776 | 0.0589 | 100% |
| Sonnet 5.5 | programming-multifile-fix | auto | 2 | 80% | 100% | 27.5 | 4.0 | 3.0 | 8 | 1437 | 77475 | 1276 | 0.0263 | 0% |
| Sonnet 5.5 | research-conflicting-sources | without | 2 | 90% | 100% | 30.0 | 3.5 | 2.5 | 7 | 6956 | 62006 | 1674 | 0.0508 | 0% |
| Sonnet 5.5 | research-conflicting-sources | forced | 2 | 90% | 100% | 22.9 | 10.0 | 8.0 | 10 | 8026 | 87700 | 2431 | 0.0652 | 100% |
| Sonnet 5.5 | research-conflicting-sources | auto | 2 | 90% | 100% | 20.4 | 3.5 | 2.5 | 7 | 2339 | 67476 | 1476 | 0.0309 | 0% |
| Sonnet 5.5 | vendor-contracts-review | without | 2 | 90% | 100% | 46.5 | 9.5 | 8.5 | 18 | 15474 | 199480 | 2362 | 0.1055 | 0% |
| Sonnet 5.5 | vendor-contracts-review | forced | 2 | 90% | 100% | 48.5 | 10.0 | 8.0 | 18 | 20305 | 208540 | 3588 | 0.1380 | 100% |
| Sonnet 5.5 | vendor-contracts-review | auto | 2 | 85% | 100% | 43.7 | 9.0 | 8.0 | 17 | 19019 | 199035 | 3386 | 0.1299 | 0% |
| Opus 5.5 | batch-with-broken-item | without | 2 | 90% | 100% | 14.2 | 3.5 | 2.5 | 7 | 20004 | 47706 | 1032 | 0.1902 | 0% |
| Opus 5.5 | batch-with-broken-item | forced | 2 | 90% | 100% | 19.9 | 6.0 | 4.0 | 12 | 6794 | 111852 | 1448 | 0.1057 | 100% |
| Opus 5.5 | batch-with-broken-item | auto | 2 | 90% | 100% | 16.2 | 4.0 | 3.0 | 8 | 1222 | 77161 | 1007 | 0.0454 | 0% |
| Opus 5.5 | direct-task-no-ritual | without | 2 | 90% | 100% | 8.4 | 3.0 | 2.0 | 6 | 4665 | 51679 | 422 | 0.0561 | 0% |
| Opus 5.5 | direct-task-no-ritual | forced | 2 | 90% | 100% | 11.3 | 5.0 | 3.0 | 10 | 5814 | 86110 | 488 | 0.0735 | 100% |
| Opus 5.5 | direct-task-no-ritual | auto | 2 | 90% | 100% | 10.6 | 3.0 | 2.0 | 6 | 384 | 56824 | 410 | 0.0227 | 0% |
| Opus 5.5 | final-check-catches-unverified-claim | without | 2 | 75% | 100% | 5.8 | 1.0 | 0.0 | 2 | 4154 | 14515 | 514 | 0.0464 | 0% |
| Opus 5.5 | final-check-catches-unverified-claim | forced | 2 | 85% | 100% | 15.1 | 4.0 | 2.0 | 8 | 5458 | 62102 | 1024 | 0.0766 | 100% |
| Opus 5.5 | final-check-catches-unverified-claim | auto | 2 | 75% | 100% | 10.4 | 2.0 | 0.5 | 4 | 2702 | 28424 | 900 | 0.0453 | 50% |
| Opus 5.5 | loop-trigger-changes-strategy | without | 2 | 60% | 100% | 18.1 | 2.0 | 1.0 | 4 | 4503 | 33054 | 1272 | 0.0681 | 0% |
| Opus 5.5 | loop-trigger-changes-strategy | forced | 2 | 80% | 100% | 21.7 | 4.0 | 2.0 | 8 | 5546 | 61960 | 1594 | 0.0887 | 100% |
| Opus 5.5 | loop-trigger-changes-strategy | auto | 2 | 60% | 100% | 23.6 | 4.0 | 2.0 | 8 | 5977 | 62092 | 1633 | 0.0929 | 100% |
| Opus 5.5 | partly-done-migration | without | 2 | 90% | 100% | 12.3 | 3.0 | 2.0 | 6 | 6265 | 52635 | 782 | 0.0763 | 0% |
| Opus 5.5 | partly-done-migration | forced | 2 | 85% | 100% | 17.3 | 5.0 | 3.0 | 10 | 7002 | 87292 | 1031 | 0.0941 | 100% |
| Opus 5.5 | partly-done-migration | auto | 2 | 90% | 100% | 13.9 | 3.0 | 2.0 | 6 | 1886 | 57975 | 850 | 0.0437 | 0% |
| Opus 5.5 | programming-multifile-fix | without | 2 | 80% | 100% | 23.9 | 3.5 | 2.5 | 6 | 6646 | 52464 | 1658 | 0.0968 | 0% |
| Opus 5.5 | programming-multifile-fix | forced | 2 | 90% | 100% | 34.6 | 5.5 | 3.5 | 10 | 7542 | 87120 | 2135 | 0.1205 | 100% |
| Opus 5.5 | programming-multifile-fix | auto | 2 | 80% | 100% | 29.7 | 4.0 | 3.0 | 6 | 2144 | 57694 | 1640 | 0.0615 | 0% |
| Opus 5.5 | research-conflicting-sources | without | 2 | 90% | 100% | 22.0 | 3.0 | 2.0 | 6 | 6594 | 52285 | 1650 | 0.0962 | 0% |
| Opus 5.5 | research-conflicting-sources | forced | 2 | 90% | 100% | 25.7 | 5.0 | 3.0 | 10 | 7640 | 86949 | 2004 | 0.1186 | 100% |
| Opus 5.5 | research-conflicting-sources | auto | 2 | 90% | 100% | 21.0 | 3.0 | 2.0 | 6 | 1192 | 58526 | 1676 | 0.0548 | 0% |
| Opus 5.5 | vendor-contracts-review | without | 2 | 90% | 100% | 42.2 | 8.0 | 7.0 | 15 | 31758 | 215986 | 3487 | 0.3671 | 0% |
| Opus 5.5 | vendor-contracts-review | forced | 2 | 85% | 100% | 57.8 | 12.0 | 10.0 | 24 | 27550 | 319142 | 5032 | 0.3850 | 100% |
| Opus 5.5 | vendor-contracts-review | auto | 2 | 90% | 100% | 38.6 | 7.5 | 6.5 | 15 | 20926 | 186548 | 3266 | 0.2701 | 0% |
| DeepSeek V4.1 Flash | batch-with-broken-item | without | 3 | 90% | 100% | 14.3 | 4.7 | 8.0 | 6266 | 0 | 21057 | 803 | 0.0015 | 0% |
| DeepSeek V4.1 Flash | batch-with-broken-item | forced | 3 | 87% | 100% | 17.7 | 6.7 | 7.3 | 10296 | 0 | 57387 | 1974 | 0.0029 | 100% |
| DeepSeek V4.1 Flash | batch-with-broken-item | auto | 3 | 90% | 100% | 8.7 | 4.0 | 3.3 | 10732 | 0 | 13384 | 731 | 0.0021 | 0% |
| DeepSeek V4.1 Flash | direct-task-no-ritual | without | 3 | 90% | 100% | 8.0 | 3.0 | 5.3 | 4453 | 0 | 12544 | 572 | 0.0010 | 0% |
| DeepSeek V4.1 Flash | direct-task-no-ritual | forced | 3 | 90% | 100% | 9.0 | 3.7 | 6.3 | 13268 | 0 | 18895 | 716 | 0.0025 | 100% |
| DeepSeek V4.1 Flash | direct-task-no-ritual | auto | 3 | 90% | 100% | 6.7 | 3.3 | 5.3 | 5738 | 0 | 13729 | 474 | 0.0012 | 0% |
| DeepSeek V4.1 Flash | final-check-catches-unverified-claim | without | 3 | 73% | 100% | 13.3 | 2.7 | 4.3 | 5160 | 0 | 11605 | 1534 | 0.0017 | 0% |
| DeepSeek V4.1 Flash | final-check-catches-unverified-claim | forced | 3 | 80% | 100% | 27.7 | 4.7 | 5.3 | 12877 | 0 | 32972 | 2950 | 0.0038 | 100% |
| DeepSeek V4.1 Flash | final-check-catches-unverified-claim | auto | 3 | 77% | 100% | 15.0 | 3.0 | 4.7 | 9748 | 0 | 17274 | 1368 | 0.0023 | 100% |
| DeepSeek V4.1 Flash | loop-trigger-changes-strategy | without | 3 | 63% | 100% | 19.7 | 2.0 | 2.0 | 4376 | 0 | 7339 | 1962 | 0.0019 | 0% |
| DeepSeek V4.1 Flash | loop-trigger-changes-strategy | forced | 3 | 77% | 100% | 24.7 | 2.0 | 2.3 | 9530 | 0 | 5757 | 1333 | 0.0022 | 100% |
| DeepSeek V4.1 Flash | loop-trigger-changes-strategy | auto | 3 | 70% | 100% | 20.3 | 1.7 | 1.3 | 7236 | 0 | 4869 | 1798 | 0.0022 | 100% |
| DeepSeek V4.1 Flash | partly-done-migration | without | 3 | 87% | 100% | 17.0 | 7.0 | 9.0 | 7001 | 0 | 46976 | 1772 | 0.0023 | 0% |
| DeepSeek V4.1 Flash | partly-done-migration | forced | 3 | 87% | 100% | 21.7 | 6.0 | 10.0 | 16588 | 0 | 44787 | 1679 | 0.0036 | 100% |
| DeepSeek V4.1 Flash | partly-done-migration | auto | 3 | 90% | 100% | 16.0 | 7.3 | 8.0 | 11827 | 0 | 36867 | 997 | 0.0025 | 0% |
| DeepSeek V4.1 Flash | programming-multifile-fix | without | 3 | 87% | 100% | 23.0 | 7.3 | 14.3 | 9565 | 0 | 42605 | 2486 | 0.0031 | 0% |
| DeepSeek V4.1 Flash | programming-multifile-fix | forced | 3 | 87% | 100% | 33.7 | 7.0 | 10.7 | 12624 | 0 | 60974 | 2558 | 0.0036 | 100% |
| DeepSeek V4.1 Flash | programming-multifile-fix | auto | 3 | 90% | 100% | 20.0 | 6.3 | 13.3 | 6207 | 0 | 41833 | 2676 | 0.0027 | 0% |
| DeepSeek V4.1 Flash | research-conflicting-sources | without | 3 | 90% | 100% | 9.3 | 3.0 | 5.7 | 7859 | 0 | 9614 | 1121 | 0.0019 | 0% |
| DeepSeek V4.1 Flash | research-conflicting-sources | forced | 3 | 90% | 100% | 20.3 | 6.0 | 9.3 | 12325 | 0 | 48171 | 1931 | 0.0032 | 100% |
| DeepSeek V4.1 Flash | research-conflicting-sources | auto | 3 | 90% | 100% | 9.7 | 3.0 | 7.3 | 6587 | 0 | 11843 | 1284 | 0.0018 | 0% |
| DeepSeek V4.1 Flash | vendor-contracts-review | without | 3 | 90% | 100% | 23.7 | 8.3 | 14.3 | 84208 | 0 | 208640 | 3579 | 0.0154 | 0% |
| DeepSeek V4.1 Flash | vendor-contracts-review | forced | 3 | 90% | 100% | 25.0 | 8.3 | 13.7 | 54493 | 0 | 203866 | 4083 | 0.0112 | 100% |
| DeepSeek V4.1 Flash | vendor-contracts-review | auto | 3 | 90% | 100% | 35.3 | 11.0 | 17.7 | 46260 | 0 | 235008 | 4639 | 0.0104 | 0% |
