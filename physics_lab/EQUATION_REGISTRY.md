# Scientific Equation Registry & Provenance Catalog

**Project:** AURORA Physics Lab  
**Document:** Provenance & Mathematical Definition Catalog  
**Primary Source Document:** *"Lost Pages of the Lost Notebook of Ramanujan"* (Research Compendium by Kaustav Nath, 210 pages)  
**Standard Status Taxonomy:**  
`TRANSCRIBED` $\to$ `UNDER_REVIEW` $\to$ `IMPLEMENTED_UNVERIFIED` $\to$ `NUMERICALLY_VERIFIED` $\to$ `EMPIRICALLY_TESTED`  
*(Or `UNRESOLVED`, `DEFERRED`, `BLOCKED` for ambiguous formulations)*

---

## 1. Scientific Status Taxonomy

To maintain absolute scientific and engineering integrity (Rules 7, 8, 9, 10, 11):
- **TRANSCRIBED:** The formulation has been transcribed verbatim from the source PDF, cataloging its mathematical symbols, dimensions, and declared domain.
- **UNDER_REVIEW:** Equations, sign conventions, dimensional consistency, and limiting behaviors are under active analysis before code implementation.
- **IMPLEMENTED_UNVERIFIED:** Code exists and runs, but numerical convergence, conservation laws, and analytical edge cases have not been tested.
- **NUMERICALLY_VERIFIED:** Automated unit and regression tests confirm that analytical derivatives match numerical finite differences, convergence tolerances are met, and conservation laws hold to documented precision.
- **EMPIRICALLY_TESTED:** The model has been evaluated against published benchmark datasets (e.g., SPARC 175-galaxy catalog, solar system ephemerides, or LIGO GW150914 ringdown bounds).
- **UNRESOLVED:** The source text exhibits ambiguity, missing constants, or coordinate inconsistencies requiring clarification. Code execution is blocked until resolved.
- **DEFERRED:** The formulation is documented for future expansion (e.g., Kerr rotating black hole metric or cosmological structure formation).

---

## 2. Cataloged Models

### Model A: Classical Point-Mass Newtonian Gravitation
- **Model ID:** `MODEL-A-NEWTONIAN` | **Version:** 1.0.0
- **Family:** `NEWTONIAN`
- **Source Citation:** Standard classical gravitation & PDF Section 1 (p. 2)
- **Potential:**
  $$\Phi(R) = -\frac{GM}{R}$$
- **Vector Acceleration:**
  $$\vec{a}(R) = -\nabla \Phi(R) = -\frac{GM}{R^2} \hat{r} = -\frac{GM}{R^3} \vec{r}$$
- **Conserved Integrals:**
  $$E = \frac{1}{2} v^2 - \frac{GM}{R}, \quad \vec{h} = \vec{r} \times \vec{v}$$
- **Status:** `NUMERICALLY_VERIFIED` | **Scientific Status:** `EMPIRICALLY_TESTED`

---

### Model B: Normalized Ramanujan-Inspired $p$-Series Deformation (Opening Theory)
- **Model ID:** `MODEL-B-RAMANUJAN-PSERIES-OPENING` | **Version:** 1.0.0
- **Family:** `RAMANUJAN_PSERIES`
- **Source Citation:** Pages 2–8, 16–22
- **Kernel Definition:**
  $$K_{p,r}(s) = \sum_{k=1}^\infty \frac{e^{-\pi k^2 / p}}{(k + r)^s}$$
  *Parameters:* $s = 2$, $r = 0$, $p(R) = R / R_0$.
- **Normalized Kernel:**
  $$\tilde{K}(R) = \frac{K_{p(R), 0}(2)}{K_{p(R_{\text{ref}}), 0}(2)}$$
  Ensures $\tilde{K}(R_{\text{ref}}) = 1.0$, recovering Newtonian potential at reference radius $R_{\text{ref}}$.
- **Potential & Vector Acceleration:**
  $$\Phi(R) = -GM \frac{\tilde{K}(R)}{R}$$
  $$\vec{a}(R) = -\nabla \Phi(R) = -GM \left[ \frac{\tilde{K}(R)}{R^2} - \frac{\tilde{K}'(R)}{R} \right] \hat{r}$$
- **Analytical Radial Derivative:**
  $$\frac{dK}{dR} = \frac{1}{R_0} \sum_{k=1}^\infty \frac{\pi k^2}{p(R)^2} \frac{e^{-\pi k^2 / p(R)}}{(k + r)^2}, \quad \tilde{K}'(R) = \frac{\frac{dK}{dR}(R)}{K(R_{\text{ref}})}$$
- **Circular Orbit Velocity:**
  $$v_{\text{circ}}(R) = \sqrt{GM \left[ \frac{\tilde{K}(R)}{R} - \tilde{K}'(R) \right]}$$
  *Engineering Rule:* If $\frac{\tilde{K}(R)}{R} - \tilde{K}'(R) \le 0$, circular orbit does not exist; code returns `NaN` / `UNSUPPORTED_ORBIT` with explicit diagnostic log.
- **Horizon-Approach Diagnostic:**
  $$H(R) = 1 - \frac{K_{p(R), r}(2)}{K_{p(R_{\text{far}}), r}(2)}$$
- **Status:** `NUMERICALLY_VERIFIED` | **Scientific Status:** `UNDER_REVIEW`

---

### Model C: Generalized Kernel Perturbations in Orbital Dynamics
- **Model ID:** `MODEL-C-KERNEL-PERTURBATION` | **Version:** 1.0.0
- **Family:** `KERNEL_PERTURBATION`
- **Source Citation:** Pages 106–114
- **Perturbation Acceleration:**
  $$\vec{a}_k = \vec{a}_d + \vec{a}_p + \vec{a}_s$$
  - Distance-weighted term: $\vec{a}_d = K_d \left( \frac{r}{R_{\text{ref}}} \right)^2 \hat{r}$
  - Phase-coupled term: $\vec{a}_p = K_p \sin(\phi) \hat{r}, \quad \cos\phi = \frac{\vec{r} \cdot \vec{v}}{r v}$
  - Solar-aligned term: $\vec{a}_s = K_s (\hat{r} \cdot \hat{s}) \hat{s}$
- **Notes on Compact-Object Generalization:** In a compact-object simulation without a Sun, $\hat{s}$ represents an external reference direction (e.g., galactic center unit vector or companion star).
- **Status:** `TRANSCRIBED` | **Scientific Status:** `UNDER_REVIEW`

---

### Model D1: Hurwitz-Zeta Kernel with Universal Mass Scaling
- **Model ID:** `MODEL-D1-HURWITZ-MASS-SCALED` | **Version:** 1.0.0
- **Family:** `REGULARIZED_COMPACT_OBJECT`
- **Source Citation:** Pages 115–122, 133–158
- **Kernel Definition:**
  $$K_p(R) = \frac{\zeta(p, 1 + R/R_0)}{\zeta(p)}, \quad p \approx 2.14$$
- **Nath Mass-Scaling Law:**
  $$R_0(M) = \alpha \gamma \sqrt{GM}$$
  where $\alpha \approx 3.8 \times 10^4$ and $\gamma \approx 5.8557 \approx e + \pi$.
- **Acceleration:**
  $$g(R) = \frac{GM}{R^2} \frac{1}{K_p(R)}$$
- **Status:** `TRANSCRIBED` | **Scientific Status:** `UNDER_REVIEW`

---

### Model D2: Regularized Compact-Object Formulation (UV Cutoff)
- **Model ID:** `MODEL-D2-REGULARIZED-UV-CUTOFF` | **Version:** 1.0.0
- **Family:** `REGULARIZED_COMPACT_OBJECT`
- **Source Citation:** Pages 141–145, 171–178, 186–189
- **UV Cutoff Potential:**
  $$\Phi_{\text{reg}}(R) = -\frac{GM}{\sqrt{R^2 + r_0^2}} K_p\left(\frac{\sqrt{R^2 + r_0^2}}{R_0}\right)$$
- **Dynamical Planck Cutoff:**
  $$r_0(M) = (\ell_P^2 R_s)^{1/3} = \left(\frac{2 G \ell_P^2}{c^2}\right)^{1/3} M^{1/3}$$
- **QNM / LIGO GW150914 Bound:** $r_0 \le 0.367 R_s$.
- **Regular de Sitter Core:** As $R \to 0$, potential approaches finite value $\Phi_{\text{reg}}(0) = -\frac{GM}{r_0}\frac{\zeta(p, 1+r_0/R_0)}{\zeta(p)}$, with zero central gravitational force ($g(0) = 0$).
- **Status:** `TRANSCRIBED` | **Scientific Status:** `UNDER_REVIEW`

---

### Model D3: Environmentally Screened Non-Local Kernel
- **Model ID:** `MODEL-D3-SCREENED-NONLOCAL` | **Version:** 1.0.0
- **Family:** `REGULARIZED_COMPACT_OBJECT`
- **Source Citation:** Pages 181–185, 195–201
- **Screening Operator:**
  $$S(g_{\text{bar}}) = \frac{1}{1 + (g_{\text{bar}} / g^\dagger)^2}, \quad g^\dagger \approx 1.2 \times 10^{-10} \text{ m/s}^2$$
- **Screened Acceleration:**
  $$g_{\text{obs}}(R) = g_{\text{bar}}(R) + S(g_{\text{bar}}) \left[ \frac{g_{\text{bar}}(R)}{K_p(R/R_0)} - g_{\text{bar}}(R) \right]$$
  In the high-acceleration regime ($g_{\text{bar}} \gg g^\dagger$), $S(g_{\text{bar}}) \to 0$, suppressing non-Newtonian deviations to $< 10^{-15}$ across planetary orbits.
- **Status:** `TRANSCRIBED` | **Scientific Status:** `UNDER_REVIEW`

---

### Model E: Relativistic Schwarzschild Geodesic Reference
- **Model ID:** `MODEL-E-RELATIVISTIC-SCHWARZSCHILD` | **Version:** 1.0.0
- **Family:** `RELATIVISTIC_REFERENCE`
- **Source Citation:** Misner, Thorne & Wheeler (1973), Schutz (1985), Iyer & Will (1987)
- **Line Element:**
  $$ds^2 = -\left(1 - \frac{2GM}{c^2 r}\right) c^2 dt^2 + \left(1 - \frac{2GM}{c^2 r}\right)^{-1} dr^2 + r^2 (d\theta^2 + \sin^2\theta d\phi^2)$$
- **Timelike Equatorial Geodesics ($\theta = \pi/2$):**
  $$\left(\frac{dr}{d\tau}\right)^2 = \left(\frac{E}{mc^2}\right)^2 c^2 - c^2 \left(1 - \frac{2GM}{c^2 r}\right) \left(1 + \frac{L^2}{m^2 c^2 r^2}\right)$$
- **Physical Boundaries:**
  - Event horizon: $R_s = \frac{2GM}{c^2}$
  - Photon sphere: $r_{\text{ps}} = \frac{3GM}{c^2} = 1.5 R_s$
  - ISCO: $r_{\text{ISCO}} = \frac{6GM}{c^2} = 3 R_s$
- **Status:** `UNDER_REVIEW` | **Scientific Status:** `EMPIRICALLY_TESTED`
