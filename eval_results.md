# Evaluation results

| Sample | Mode | Time (s) | Actions | Decisions | FAIL | WARN |
|---|---|---|---|---|---|---|
| short_meeting.txt | default | 8.1 | 2 | 1 | 0 | 1 |
| messy_meeting.vtt | default | 1.9 | 1 | 1 | 0 | 0 |
| no_actions_meeting.txt | default | 1.4 | 0 | 0 | 0 | 0 |
| unlabelled_meeting.txt | default | 1.8 | 2 | 1 | 0 | 0 |
| product_review.txt | default | 3.9 | 3 | 3 | 0 | 1 |
| long_planning.txt | single call | 3.8 | 7 | 3 | 0 | 1 |
| long_planning.txt | map-reduce (1200 chars) | 11.2 | 8 | 6 | 0 | 0 |

## Details

**short_meeting.txt [default]**
- [WARN] action item also in decisions: 'Change the staging server to the smaller plan' ~ 'Move the staging server to the smaller plan'

**messy_meeting.vtt [default]**
- all checks passed

**no_actions_meeting.txt [default]**
- all checks passed

**unlabelled_meeting.txt [default]**
- all checks passed

**product_review.txt [default]**
- [WARN] action item also in decisions: 'Draft help article for the export feature' ~ 'Defer writing the export feature help article until November.'

**long_planning.txt [single call]**
- [WARN] action item also in decisions: 'Collect quotes from two alternative vendors for the CloudNine contract' ~ 'The team will compare at least two alternative vendors before deciding on the CloudNine contract renewal.'

**long_planning.txt [map-reduce (1200 chars)]**
- all checks passed
