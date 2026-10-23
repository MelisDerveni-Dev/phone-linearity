# Authors and joint decisions

**Melis Derveni and Harsimranjeet Kaur** both worked on the project. The contribution statement below follows the authors' supplied account; no percentages or unreported tasks are assigned.

| Author | Contributions |
| --- | --- |
| Melis Derveni | Measurements and experiments; the other deliverables, including the report, README and live demonstration. |
| Harsimranjeet Kaur | Model training, testing and evaluation. |
| Both authors | Discussed alternatives, advantages and limitations, and jointly agreed how to conduct the experiments, which model to use, and why to choose the approach. |

These lead responsibilities do not imply either author worked in isolation. Both contributed to the project and its decisions. Signatures and date remain for the authors to complete in the report.

## Choices, advantages and limitations

The following records the approach jointly agreed by the authors and the tradeoffs it entails. It does not claim that every alternative was experimentally compared.

| Chosen approach | Advantage | Limitation / alternative | Why it was chosen |
| --- | --- | --- | --- |
| One full affine model, m = S a + b | Represents constant bias, gains and cross-axis coupling in one model. | More parameters than diagonal gains; placement errors can enter the fit. Diagonal gains were not independently benchmarked. | Matches the intended three-axis calibration and gives one interpretable correction for all recordings. Only S and b are fitted; no separate noise term is predicted. |
| Six nominal signed gravity references | Supplies a rank-four design with opposite directions to estimate offsets and sensitivity. | Camera bumps, buttons and support alignment make the true vectors uncertain; a precision fixture would improve reference accuracy. | Uses gravity and feasible supported positions with the available phone and equipment, with uncertainty acknowledged. |
| Equal-weight pose means | Gives every orientation equal weight despite different run lengths; reduces influence of sample noise on the mean. | A mean hides short disturbances and within-run variation. | Fits the notebook's regression approach while retaining all raw samples, stability diagnostics and masks for inspection. |
| Whole first/second repeat split | Keeps adjacent samples from the same run together and preserves a preassigned split. | Repeats from one session are correlated; independent sessions would provide stronger validation. | Respects how the recordings were collected and avoids an arbitrary random row split. The report names the independence limitation. |
| Training-only stability policy | Gives reproducible handling exclusions without selecting samples by agreement with the reference. | Low variation does not prove stationarity or correct alignment, and boundary trims remove some usable data. | Checks for brief disturbances and freezes preprocessing before held-out evaluation. |
| Wall/table geometry as a held-out angle reference | Tests different orientations without treating the phone's own inclination as truth. | Contact/ruler uncertainty and two distinct angles limit interpretation; the measured angle result worsens after correction. | Provides an external reference using available equipment. Both favourable and unfavourable results remain in the report. |
| Local Node viewer with measured JSON | Works without cloud services, frontend dependencies or API keys, and displays paired raw/corrected samples. | Requires the phone and laptop to share a network and a physical rehearsal. | Supports a practical live demonstration while preserving honest source, reference and calibration labels. |
| Shaking as a gravity-interpretation demonstration | Clearly illustrates changing specific force during motion. | No independent dynamic force reference: it cannot establish affine sensor failure or clipping. | Retains the collected experiment while limiting the conclusion to what it supports. |

Measured results, experimental limitations and reproducible commands are in the report, README and `results/analysis-2026-10-23/`. Joint agreement does not remove the need to report the poorer angle validation or supply physical signatures.
