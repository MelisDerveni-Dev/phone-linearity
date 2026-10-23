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
| One full affine model, m = S a + b (12 numbers), fitted by least squares | Represents constant offsets, gains and cross-axis coupling in one model; halves the held-out static error (0.22 → 0.11 m/s²). | Placement tilt (for example the camera bump) can enter the cross-axis terms. Simpler bias-only and diagonal versions were compared afterwards and are listed in `results/evidence-2026-10-23/`; they were not adopted. | Matches the hypothesis in the brief and the rank-4 argument for six poses. Only S and b are fitted; no separate noise term is predicted. |
| Six nominal signed gravity references | Supplies a rank-four design with opposite directions to estimate offsets and sensitivity. | Camera bumps, buttons and support alignment make the true vectors uncertain; a precision fixture would improve reference accuracy. | Uses gravity and feasible supported positions with the available phone and equipment, with uncertainty acknowledged. |
| Equal-weight pose means | Gives every orientation equal weight despite different run lengths; reduces influence of sample noise on the mean. | A mean hides short disturbances and within-run variation. | Fits the notebook's regression approach while retaining all raw samples, stability diagnostics and masks for inspection. |
| Whole first/second repeat split | Keeps adjacent samples from the same run together and preserves a preassigned split. | Repeats from one session are correlated; independent sessions would provide stronger validation. | Respects how the recordings were collected and avoids an arbitrary random row split. The report names the independence limitation. |
| Training-only stability policy | Gives reproducible handling exclusions without selecting samples by agreement with the reference. | Low variation does not prove stationarity or correct alignment, and boundary trims remove some usable data. | Checks for brief disturbances and freezes preprocessing before held-out evaluation. |
| Wall/table geometry as a held-out angle reference | Tests different orientations without treating the phone's own inclination as truth. | Six distinct angles over two sessions, but every ramp reads 2.6–6.0° below the contact-line angle with any calibration, so the ramps cannot resolve sub-degree calibration effects. The magnitude test needs no angle reference. | Provides an external reference using available equipment. Both favourable and unfavourable results remain in the report. |
| Local Node viewer with measured JSON | Works without cloud services, frontend dependencies or API keys, and displays paired raw/corrected samples. | Requires the phone and laptop to share a network and a physical rehearsal. | Supports a practical live demonstration while preserving honest source, reference and calibration labels. |
| Shaking as the limit experiment, plus quantization and full-scale evidence | Shows where the tool's gravity-only model fails (only 0.6 % of samples within 0.35 m/s² of g) and where the sensor's output is a staircase (0.0048 m/s² steps). | No independent dynamic force reference: it cannot establish affine sensor failure; the 94.3 m/s² peak is 60 % of full scale, so no clipping. | Retains the collected experiment while limiting each conclusion to what the data support. |

Measured results, experimental limitations and reproducible commands are in the report, the README, `results/analysis-2026-10-23/`, `results/angle-validation-2026-10-23/` and `results/evidence-2026-10-23/`. Joint agreement does not remove the need to report the ramp tilt result that calibration does not improve, or to supply physical signatures.
