# Is your phone linear?

**Report draft · 20 October 2026 · Measurements pending**  
Authors: [team member 1] and [team member 2]

## 1. Question and hypothesis

We ask whether a single affine calibration describes the three-axis accelerometer of our phone, how much it improves independent measurements, and where its predictions fail. Our working hypothesis is

\[m = Sa+b+\varepsilon,\qquad S\in\mathbb{R}^{3\times3},\quad b\in\mathbb{R}^3.\]

Here \(m\) is the measured vector in m/s², \(a\) is the reference specific-force vector in the phone frame, \(b\) is a constant bias in m/s², \(S\) is a dimensionless matrix of gains and cross-axis sensitivities, and \(\varepsilon\) represents unexplained measurement error. At rest, the reference has magnitude approximately \(g=9.81\,\mathrm{m/s^2}\). We use phyphox **Acceleration with g**, because gravity is our reference signal.

This is an affine map; it is a linear map only when \(b=0\). In homogeneous coordinates,

\[\begin{bmatrix}m\\1\end{bmatrix}=\begin{bmatrix}S&b\\0&1\end{bmatrix}\begin{bmatrix}a\\1\end{bmatrix}.\]

The hypothesis is restricted to the tested acceleration range, temperature, and recording conditions. It does not claim that a static calibration removes random noise or recovers clipped information. **No empirical claim about this phone is made before measurements.**

## 2. Data and experimental design

Data collection is planned for **21 October 2026**, following the user's schedule. We will use one phone and keep its case configuration fixed. Record its model, operating system, phyphox version, axis convention, and experiment settings. For each of the six signed axis orientations, record approximately 20 s at rest, supported by a flat surface or a book. Repeat all poses in a separate session. Assign session A to fitting and session B to testing **before examining errors**; keep the test session out of tuning and model selection.

We will record at least four independent ramp angles spanning 0°–45°. Measure the raised height \(h\) and the length \(L\) **along the inclined board between its support points**, so that \(\theta_{ref}=\arcsin(h/L)\). Record ruler uncertainty, phone position, tilt direction, and how the phone axes align with the ramp. A horizontal run would require arctangent instead. Avoid measuring \(L\) as the phone length unless it is also the support spacing.

Keep every original phyphox export unchanged under `data/raw/`, with decimal points and documented headers and units. Enter one row per file in `data/recordings.csv`. Derived rest masks and pose means belong in `data/processed/`. For each pose, exclude handling at the start and end and retain stable intervals using a documented rolling variability criterion and minimum duration. Select thresholds on the fit session only, report exclusions, and check the masks visually.

**To complete after collection:** device and settings; actual dates, file counts and durations; headers; accepted pose intervals; ramp dimensions and uncertainties; limit-experiment conditions.

## 3. Model and estimation

For each accepted training pose \(i\), let \(\bar m_i\) be its mean measured vector and \(a_i\) its independently assigned reference vector, ideally one of \(\pm ge_x,\pm ge_y,\pm ge_z\). Determine axis signs from the phone convention and observations; do not assume that a named face automatically has a particular sign. Placement error is a source of reference uncertainty, not automatically a sensor defect.

With one row per pose, define

\[X_i=[a_{ix},a_{iy},a_{iz},1],\quad M_i=\bar m_i^T,\quad B=\begin{bmatrix}S^T\\b^T\end{bmatrix}.\]

Estimate \(\hat B=\arg\min_B\|XB-M\|_F^2\) using a stable least-squares solver such as QR or SVD, without explicitly forming normal-equation inverses. Then \(\hat S=\hat B_{1:3,:}^{T}\) and \(\hat b=\hat B_{4,:}^{T}\). The problem is linear in the unknown entries of \(B\), even though the sensor may deviate from the proposed model. A successful fit does not itself establish physical linearity.

The twelve parameters are uniquely determined when \(\mathrm{rank}(X)=4\). Four affinely independent known vectors suffice mathematically; six opposite-axis poses provide redundancy. The planned six vectors give rank four. A set confined to \(a_z=0\), such as \(\pm ge_x,\pm ge_y\), gives rank at most three and cannot identify sensitivity to \(a_z\). Repeating only one face gives rank one. Gravity magnitude alone cannot identify a completely general \(S\): reference directions are required, because arbitrary rotations preserve the magnitude.

Report the measured design rank, singular values and condition number. Since the first three columns have units of acceleration and the last is an intercept, report both \(\kappa_2(X)\) and the condition number of the dimensionless design with \(a/g\) columns. Also report \(\kappa_2(\hat S)\); reject singular or unusably ill-conditioned calibration matrices. Apply calibration by solving

\[\hat S\,\hat a=m-\hat b,\]

and save \(\hat S,\hat b\), units, axis convention, and training provenance as JSON. The live viewer uses an explicitly labelled identity transform until fitted parameters are available. It must not present this as a measured improvement.

## 4. Evidence: five required answers

**1 — In what sense linear?** The proposed sensor relation is affine, and linear in twelve unknown parameters. The homogeneous-coordinate representation above answers the mathematical distinction. **Pending:** measured coefficients and uncertainty or repeatability.

**2 — Which linearity test?** Use an independently measured ramp rotation with reference \(a(\theta)\) determined by the documented axis convention. A chosen varying component obeys \(a_k=g\sin\theta\); test whether calibrated output follows this input on held-out angles, including both signs where feasible. For the full response, compare \(m(\theta)-\hat b\) against \(\hat S a(\theta)\). Its other reference components also change with angle, so account for them rather than treating the whole vector as a scaled input. A gravity-only ramp cannot test full-vector homogeneity over different magnitudes; it tests components and predictions over a sphere of fixed magnitude. Plot residuals versus reference input and angle and compare systematic structure against repeatability and reference uncertainty. **Pending:** slopes, intercepts, units, residuals and conclusion.

**3 — Which poses and why?** Compare the rank-four full training design to an intentionally restricted subset with deficient rank. **Pending:** measured rank, condition numbers and the consequences for fitted coefficients. The theoretical ranks above are predictions, not computed outcomes.

**4 — How much improvement?** On session B only, report before/after vector RMSE \(\sqrt{N^{-1}\sum_i\|v_i-a_i\|^2}\) in m/s² and gravity-magnitude RMSE \(\sqrt{N^{-1}\sum_i(\|v_i\|-g)^2}\). State whether \(N\) counts pose means or time samples; pose means avoid overweighting long recordings. Compute ramp tilt from the documented geometry, for example \(\theta=\operatorname{atan2}(v_k,\sqrt{v_j^2+v_l^2})\) for a signed component \(k\). Compare against the ruler reference and report tilt RMSE in degrees. Use identical test windows for raw and corrected values. **Pending:** all measured metrics; an improvement is not guaranteed.

**5 — Where does the model fail?** Preselect a limit experiment and record an independent indicator of its input or condition. A stationary drift experiment is a practical first choice: compare successive stable windows at the same supported pose over time and, if feasible, different documented temperatures. A repeatable bias change beyond baseline uncertainty would contradict a constant-parameter model. For optional controlled motion, residual tilt during shaking can demonstrate failure of gravity-only tilt inference, but is not sufficient proof that the accelerometer itself is non-affine: motion adds real specific force. Saturation would be a stronger sensor-limit example only if repeatable clipping and independent evidence of increasing input are available. **Pending:** an observed failure trace, quantified discrepancy, supported cause and user guidance. If a candidate shows no failure, report that and perform another justified candidate rather than invent a result.

Use at most **four figures**: (1) time traces and rest masks, (2) fitted residuals and design/pose evidence, (3) held-out raw/corrected vector and tilt errors, (4) limit experiment. Reserve figure space only after real data exists.

## 5. Limits and next steps

Six supported faces provide limited placement accuracy and input magnitudes. Ruler uncertainty, table alignment, within-session correlation, temperature changes and phone preprocessing may limit interpretation. Calibration does not separate gravity and motion. With another week, use a more accurate fixture, repeat on more days and temperatures, and test known dynamic inputs. A live demo will apply the fitted transform to a new recording and compare raw and corrected traces at the same timestamps and scale.

## 6. Contribution statement

[Name 1: actual experimental, coding and writing contributions.]  
[Name 2: actual experimental, coding and writing contributions.]  
Signatures and date: [both authors to complete].

## Sources

Course brief: *Sprint project: Is your phone linear?*, dated 18 October 2026, supplied by the user. phyphox remote API: https://phyphox.org/docs/remote-interface/. Sensor definitions: https://phyphox.org/docs/file-format/input/. This draft supplies a proposed method; all results remain pending.
