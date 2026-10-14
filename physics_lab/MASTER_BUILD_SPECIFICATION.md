# AURORA PHYSICS LAB — MASTER ENGINEERING BUILD SPECIFICATION

**Document Version:** 1.0.0  
**Status:** APPROVED / IN PROGRESS (PHASE 0 AUDIT COMPLETE)  
**Parent System:** Project AURORA (*Autonomous Unified Reconnaissance, Operations & Reliability Architecture*)  
**Location:** `d:\AURORA\physics_lab\`  
**Target Architecture:** Full-Stack Aerospace & Relativistic Simulation Workbench  

---

## 1. Role and Objective

Act as a senior scientific software architect, computational physicist, numerical analyst, and aerospace simulation engineer.

Extend the existing, production-verified AURORA application with a new research-grade module called **AURORA Physics Lab**.

The objective is to create a research-oriented, software-only spacecraft simulator focused on hypothetical spacecraft trajectories near a compact object or black hole. The simulator implements, simulates, and rigorously compares the distinct gravitational formulations described in the supplied 210-page research compendium (*"Lost Pages of the Lost Notebook of Ramanujan"*, authored by Kaustav Nath).

This is a substantial, phased engineering project. In accordance with Section 14 of this specification, implementation proceeds incrementally across discrete verification phases. Every completed phase remains runnable, persistent, and verifiable through automated tests.

---

## 2. Non-Negotiable Engineering Rules

1. **Repository Inspection Before Mutation:** Always inspect the repository and identify existing architecture before modifying files.
2. **Preserve Existing Capabilities:** Preserve existing AURORA screens, APIs, database schema, mission control console, telemetry ingestion, incident management, event auditing, replay scrubber, and verification features.
3. **No Standalone Demos:** Do not replace the existing application with a separate demo. AURORA Physics Lab is an integrated module within the AURORA mission-operations suite.
4. **Reuse Conventions:** Reuse established project conventions, styling (dark aerospace theme), typed contracts, and dependencies (`FastAPI`, `SQLAlchemy`, `scipy`, `numpy`, `pytest`, `React 18`, `Vite`, `Tailwind CSS`, `Vitest`).
5. **Safe Rollback Point:** Create a feature branch (`feature/aurora-physics-lab`) or git tag before substantial modifications.
6. **Test Baseline Integrity:** Record the initial test baseline and existing known failures before making changes.
7. **No Unexecuted Pass Claims:** Never claim that tests, simulations, or benchmarks passed unless they were actually executed and logged.
8. **No Fabricated Evidence:** Do not fabricate scientific results, reference data, measurements, or validation evidence.
9. **Unique Model Identifiers:** Every selectable physics model must have a distinct implementation, a unique model identifier (`model_id`), and an explicit semantic version (`model_version`).
10. **Provenance Separation:** Strictly separate equations transcribed directly from the source PDF, implementation assumptions, independently derived corrections, and unvalidated physical hypotheses.
11. **Ambiguity Handling:** If a source equation is ambiguous or inconsistent, record the issue in the Equation Registry and mark that model as `BLOCKED` or `UNRESOLVED` until clarified. Never silently substitute an equation.
12. **Disclaimer Integrity:** Never claim official space-agency affiliation (NASA, ESA, ISRO), flight qualification, or operational spacecraft safety. This is an educational and research portfolio workbench.
13. **Phased Execution:** Complete the project in discrete phases (Phase 0 through Phase 7). Keep each completed phase runnable and tested.

---

## 3. Scientific Source of Truth & Model Taxonomies

The source document is the 210-page research collection by Kaustav Nath (*CareGuardian / Indus Valley World School*). The formulations represent distinct model families and must be maintained separately:

### Model A — Classical Newtonian Baseline
- **Identifier:** `MODEL-A-NEWTONIAN` (v1.0.0)
- **Formulation:** Point-mass Newtonian gravitational acceleration in 3D Cartesian coordinates:
  $$\vec{a}_{\text{Newton}} = -\frac{GM}{r^3} \vec{r}$$
- **Energy & Angular Momentum:**
  $$E = \frac{1}{2}v^2 - \frac{GM}{r}, \quad \vec{h} = \vec{r} \times \vec{v}$$
- **Standard Solutions:** Circular velocity $v_{\text{circ}} = \sqrt{GM/r}$, escape velocity $v_{\text{esc}} = \sqrt{2GM/r}$, orbital period $T = 2\pi \sqrt{a^3/GM}$.
- **Status:** `NUMERICALLY_VERIFIED`

### Model B — Normalized Ramanujan-Inspired $p$-Series Deformation (Opening Theory)
- **Identifier:** `MODEL-B-RAMANUJAN-PSERIES-OPENING` (v1.0.0)
- **Source Reference:** Pages 1–15, 16–22
- **Kernel Definition:**
  $$K_{p,r}(s) = \sum_{k=1}^\infty \frac{e^{-\pi k^2 / p}}{(k + r)^s}, \quad p > 0, \ r \notin \{-1, -2, \dots\}, \ \text{Re}(s) > 1$$
- **Primary Gravitational Mapping:** $s = 2$, $r = 0$, $p(R) = R / R_0$.
- **Normalized Kernel:**
  $$\tilde{K}(R) = \frac{K_{p(R), 0}(2)}{K_{p(R_{\text{ref}}), 0}(2)}, \quad \tilde{K}(R_{\text{ref}}) = 1.0$$
- **Modified Potential & Vector Acceleration:**
  $$\Phi(R) = -\frac{GM}{R} \tilde{K}(R)$$
  $$\vec{a}(R) = -\nabla \Phi(R) = -GM \left( \frac{\tilde{K}(R)}{R^2} - \frac{\tilde{K}'(R)}{R} \right) \hat{r}$$
- **Analytical Derivative of Unnormalized Kernel:**
  $$\frac{dK}{dR} = \frac{1}{R_0} \sum_{k=1}^\infty \frac{\pi k^2}{p(R)^2} \frac{e^{-\pi k^2 / p(R)}}{(k + r)^2}$$
- **Circular Velocity:**
  $$v_{\text{circ}}(R) = \sqrt{GM \left( \frac{\tilde{K}(R)}{R} - \tilde{K}'(R) \right)}$$
  *Crucial Rule:* Do not use absolute values to conceal a negative quantity under the square root. If $\frac{\tilde{K}(R)}{R} - \tilde{K}'(R) \le 0$, circular orbit is not physically supported at that radius; return an invalid status.
- **Horizon-Approach Indicator:**
  $$H(R) = 1 - \frac{K_{p(R), r}(2)}{K_{p(R_{\text{far}}), r}(2)}$$
  *Constraint:* Mathematical diagnostic only; not a general relativistic event horizon.

### Model C — Generalized Kernel Perturbations in Orbital Dynamics
- **Identifier:** `MODEL-C-KERNEL-PERTURBATION` (v1.0.0)
- **Source Reference:** Pages 106–114
- **Formulation:** Superposition of distance-weighted, phase-coupled, and solar-aligned accelerations:
  $$\vec{a}_k = \vec{a}_d + \vec{a}_p + \vec{a}_s$$
  $$\vec{a}_d = K_d \left(\frac{r}{R_E}\right)^2 \hat{r}$$
  $$\vec{a}_p = K_p \sin(\phi) \hat{r}, \quad \cos\phi = \frac{\vec{r} \cdot \vec{v}}{r v}$$
  $$\vec{a}_s = K_s (\hat{r} \cdot \hat{s})\hat{s}$$
- **Applicability & Ambiguity:** Originally formulated for Earth orbit where $R_E$ is Earth's radius and $\hat{s}$ is the Sun direction. In a compact-object simulation, $R_E$ must be generalized to the central body scale $R_0$ or configured explicitly.

### Model D1 — Hurwitz-Zeta Kernel with Universal Mass Scaling
- **Identifier:** `MODEL-D1-HURWITZ-MASS-SCALED` (v1.0.0)
- **Source Reference:** Pages 115–122, 133–158
- **Kernel Definition:**
  $$K_p(R) = \frac{\zeta(p, 1 + R/R_0)}{\zeta(p)}, \quad p \approx 2.14$$
- **Nath Mass-Scaling Law:**
  $$R_0(M) = \alpha \sqrt{GM} \quad (\text{or } R_0(M) = \alpha \gamma \sqrt{GM})$$
  $$\alpha \approx 3.8 \times 10^4, \quad \gamma \approx 5.8557 \approx e + \pi$$
- **Acceleration:**
  $$\vec{a}(R) = -\frac{GM}{R^2} \frac{1}{K_p(R, R_0(M))} \hat{r}$$

### Model D2 — Regularized Compact-Object Formulation (UV Cutoff)
- **Identifier:** `MODEL-D2-REGULARIZED-UV-CUTOFF` (v1.0.0)
- **Source Reference:** Pages 141–145, 171–178, 186–189
- **UV Cutoff Function:** Replace $R$ with $\sqrt{R^2 + r_0^2}$:
  $$\Phi_{\text{reg}}(R) = -\frac{GM}{\sqrt{R^2 + r_0^2}} K_p\left(\frac{\sqrt{R^2 + r_0^2}}{R_0}\right)$$
- **Dynamical Planck-Scale UV Cutoff:**
  $$r_0(M) = (\ell_P^2 R_s)^{1/3} = \left(\frac{2 G \ell_P^2}{c^2}\right)^{1/3} M^{1/3}$$
- **QNM / LIGO Bound:** $r_0 \le 0.367 R_s$.
- **Regular Metric Line Element:**
  $$f(R) = 1 - \frac{2GM}{c^2 \sqrt{R^2 + r_0^2}} K_p\left(\frac{\sqrt{R^2 + r_0^2}}{R_0}\right)$$

### Model D3 — Environmentally Screened Non-Local Kernel
- **Identifier:** `MODEL-D3-SCREENED-NONLOCAL` (v1.0.0)
- **Source Reference:** Pages 181–185, 195–201
- **Screening Function:**
  $$S(g_{\text{bar}}) = \frac{1}{1 + (g_{\text{bar}} / g^\dagger)^2}, \quad g^\dagger \approx 1.2 \times 10^{-10} \text{ m/s}^2$$
- **Screened Acceleration:**
  $$g_{\text{obs}}(R) = g_{\text{bar}}(R) + S(g_{\text{bar}}) \left[ \frac{g_{\text{bar}}(R)}{K_p(R/R_0)} - g_{\text{bar}}(R) \right]$$

### Model E — Relativistic Reference (Schwarzschild Geodesic)
- **Identifier:** `MODEL-E-RELATIVISTIC-SCHWARZSCHILD` (v1.0.0)
- **Formulation:** Timelike geodesics in Schwarzschild spacetime ($M$, uncharged, non-rotating):
  $$\frac{d^2 r}{d\tau^2} = -\frac{GM}{r^2} + r\left(1 - \frac{2GM}{c^2 r}\right)\left(\frac{d\phi}{d\tau}\right)^2 - \frac{GM}{c^2 r^2 (1 - 2GM/(c^2 r))}\left(\frac{dr}{d\tau}\right)^2$$
- **Effective Potential:**
  $$V_{\text{eff}}(r) = \left(1 - \frac{2GM}{c^2 r}\right)\left(1 + \frac{L^2}{c^2 r^2}\right)$$
- **Physical Boundaries:**
  - Schwarzschild radius: $R_s = \frac{2GM}{c^2}$
  - Innermost Stable Circular Orbit (ISCO): $r_{\text{ISCO}} = \frac{6GM}{c^2} = 3 R_s$
  - Photon Sphere: $r_{\text{ps}} = \frac{3GM}{c^2} = 1.5 R_s$

---

## 4. Scientific Equation Registry & Provenance Schema

All models, equations, derivations, and statuses are cataloged in `d:\AURORA\physics_lab\EQUATION_REGISTRY.json` adhering to:
- `model_id` (Unique string key)
- `model_version` (Semantic version string)
- `display_name` (Human-readable title)
- `formulation_family` (`NEWTONIAN`, `RAMANUJAN_PSERIES`, `KERNEL_PERTURBATION`, `REGULARIZED_COMPACT_OBJECT`, `RELATIVISTIC_REFERENCE`)
- `source_document` ("Lost Pages of the Lost Notebook of Ramanujan" / Research Collection)
- `source_page_range` (Specific page numbers from the 210-page compendium)
- `source_equation_raw` (Verbatim transcription)
- `implementation_equation_latex` (Formal LaTeX equation)
- `parameter_definitions` (Array of parameters with symbol, description, SI units, and default value)
- `domain_of_validity` (Coordinate range, mass boundaries, energy limits)
- `implementation_status` (`TRANSCRIBED`, `UNDER_REVIEW`, `IMPLEMENTED_UNVERIFIED`, `NUMERICALLY_VERIFIED`, `EMPIRICALLY_TESTED`, `UNRESOLVED`, `DEFERRED`)
- `scientific_validation_status` (Theoretical status distinct from software passing tests)
- `known_limitations` (Documented physical and numerical constraints)
- `test_references` (List of automated test files validating the implementation)

---

## 5. Numerical Simulation Engine Architecture

The physics simulation engine (`d:\AURORA\backend\app\physics_lab\engine\`) operates independently of the real-time mission clock:
1. **State Vector Representation:**
   $$\vec{S}(t) = \left[ x, y, z, v_x, v_y, v_z, m(t) \right]^T$$
2. **Integrators:**
   - **RK4 (Runge-Kutta 4th Order):** Fixed-step integrator for deterministic benchmarking.
   - **Dormand-Prince (RK45 / DOPRI5):** Adaptive step-size integrator with local error control ($\text{rtol}, \text{atol}$).
   - **Symplectic Verlet / Velocity-Verlet:** Symplectic integrator for long-term conservative orbits preserving energy and angular momentum.
3. **Event Detection & Termination Handling:**
   - Coordinate singularity avoidance ($r \to 0$ or $r \le R_{\text{horizon}}$).
   - Event horizon crossing ($r \le R_s$).
   - Sphere of Influence / Escaped domain boundary ($r \ge R_{\text{max}}$).
   - Fuel exhaustion ($m_{\text{prop}} \le 0$).
   - Max simulation steps / timeout exceeded.
4. **Trajectory Persistence:**
   - Trajectory time series with downsampled decimation for high-resolution rendering without browser memory overflow.

---

## 6. Spacecraft Propulsion & Manoeuvre Framework

1. **Mass Depletion:**
   $$\frac{dm}{dt} = -\frac{\|\vec{T}_{\text{thrust}}\|}{I_{\text{sp}} g_0}$$
2. **Rocket Equation Compliance:**
   $$\Delta v = I_{\text{sp}} g_0 \ln\left(\frac{m_0}{m_f}\right)$$
3. **Manoeuvre Profiles:**
   - Continuous low-thrust burns (specified by direction vector $\hat{u}(t)$ and magnitude $T$).
   - Impulsive $\Delta \vec{v}$ burns at discrete simulation epochs.
   - Fuel exhaustion event detection halting active thrust.

---

## 7. Model Comparison & Verification Diagnostics

The engine enables multi-model parallel runs from identical initial conditions $(\vec{r}_0, \vec{v}_0, m_0)$:
- **Trajectory Delta:** $\|\vec{r}_{\text{model}}(t) - \vec{r}_{\text{ref}}(t)\|$ and $\|\vec{v}_{\text{model}}(t) - \vec{v}_{\text{ref}}(t)\|$.
- **Energy Conservation Tracking:** $\Delta E / E_0$ over time for conservative models.
- **Angular Momentum Tracking:** $\Delta \|\vec{h}\| / \|\vec{h}_0\|$.
- **Periapsis / Apoapsis Shift:** Quantifying perihelion precession rate.

---

## 8. Frontend Experience Architecture

The AURORA frontend adds a top-level **Physics Lab** navigation view switcher with 11 dedicated consoles:
1. **Compact-Object Setup:** Black hole / compact object mass ($M$), Schwarzschild radius ($R_s$), initial state $(\vec{r}_0, \vec{v}_0)$.
2. **Physics Model Registry:** Interactive explorer of all cataloged models, LaTeX equations, provenance pages, and validation statuses.
3. **Experiment Configuration:** Integrator selection, step sizes, tolerances, simulation time limits.
4. **Simulation Console:** Run / Pause / Step / Reset execution controls with live status readouts.
5. **3D Trajectory Viewer:** Interactive 3D trajectory visualization (orthographic / perspective projection with orbit paths and compact-object horizon).
6. **Telemetry & Diagnostics:** Real-time plots of energy error, angular momentum, radial distance, and acceleration breakdown.
7. **Model Comparison:** Multi-trajectory overlay comparing Newtonian, Ramanujan $p$-series, and Relativistic orbits.
8. **Propulsion & Manoeuvres:** Spacecraft dry mass, fuel mass, $I_{\text{sp}}$, thrust vectors, and burn schedules.
9. **Parameter Sweep & Sensitivity:** Automated sweeps over $R_0$, $p$, and $r_0$ with orbital deviation heatmaps.
10. **Validation Reports:** Formal acceptance report viewer with verifiable test logs.
11. **Saved Experiments & Archive:** Export/Import experiment runs as JSON and CSV datasets.

---

## 9. Phased Execution Roadmap

- [x] **Phase 0 — Repository Audit & Baseline Verification:**
  - Safety commit and feature branch `feature/aurora-physics-lab`.
  - Baseline tests verified (Backend: 15/15 passed, Frontend: 4/4 passed).
  - Master Engineering Specification created.
  - Scientific Equation Registry compiled from PDF.
- [ ] **Phase 1 — Mathematical Foundation:**
  - Pure Python mathematical library for Kernel $K_{p,r}(s)$, $\tilde{K}(R)$, analytical derivative $\frac{d\tilde{K}}{dR}$, and numerical finite differences.
  - Parameter validation and unit tests for Model A and Model B.
- [ ] **Phase 2 — Numerical Propagation Engine:**
  - 3D Cartesian numerical state propagation (RK4, Dormand-Prince, Symplectic).
  - Event termination detection, adaptive stepping, and trajectory recording.
- [ ] **Phase 3 — Compact-Object & Relativistic Reference:**
  - Schwarzschild geodesic solver (Model E) and horizon diagnostics.
  - Energy & angular momentum integrals, ISCO / photon sphere bounds.
- [ ] **Phase 4 — Experimental Kernel Models:**
  - Implement Model C (perturbations), Model D1 (mass-scaled Hurwitz kernel), Model D2 (regularized UV cutoff), and Model D3 (screened non-local).
- [ ] **Phase 5 — Spacecraft Propulsion & Manoeuvres:**
  - Tsiolkovsky mass depletion, continuous thrust, impulsive $\Delta v$, fuel limits.
- [ ] **Phase 6 — Research Tools (Comparison, Sweeps, Sensitivity):**
  - Multi-model differential comparison, parameter sweep jobs, objective fitting.
- [ ] **Phase 7 — Integrated Release & UI Console:**
  - Full frontend integration within AURORA navigation, persistence in SQLite, end-to-end acceptance tests.
