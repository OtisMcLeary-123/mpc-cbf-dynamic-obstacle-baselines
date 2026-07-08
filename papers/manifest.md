# Block A Paper Corpus Manifest

This directory stores the local reading corpus for Block A. PDF files are kept locally and ignored by Git to avoid redistributing papers on GitHub. This manifest records source links, local filenames, and how each paper supports the experiments.

Source reference list:

```text
/home/otismcleary/Documents/paper/Safety-Aware_Optimal_Control_With_Language-Guided_Online_Parameter_Adjustment_via_Large_Language_Models.pdf
```

## Downloaded PDFs

| Ref | Local file | Source URL | Used by | SHA-256 |
|---|---|---|---|---|
| [3] | `ref03_zeng_2021_safety_critical_mpc_dcbf.pdf` | https://arxiv.org/pdf/2007.11718 | E3, E4 | `5b8789704c0a9faebac33a139840a5b43629bcc46219ee3598a83bbef9d6654c` |
| [4] | `ref04_ames_2019_cbf_theory_applications.pdf` | https://arxiv.org/pdf/1903.11199 | E3 | `c28cc757da65ebba5c2137253bfd0b80f07476c5e3c86ca234c3968d47415e8e` |
| [5] | `ref05_jian_2023_dynamic_cbf_mpc.pdf` | https://arxiv.org/pdf/2209.08539 | Background | `f610d8234b6841569db0d6a654cbb3c4359a6fa5e1c044350722787cde3081b2` |
| [7] | `ref07_vulcano_2022_safe_navigation_nmpc_cbf.pdf` | https://www.diag.uniroma1.it/~labrob/pub/papers/CDC22_CrowdNavigation.pdf | Background | `3b8a34b86dd5db62a4b4a0510d859a2ae22088226b1e170c619465f81ab92141` |
| [10] | `ref10_zhang_2024_online_safety_critical_dynamic_obstacles.pdf` | https://arxiv.org/pdf/2402.16449 | Background | `1458e8a8b5879dbf37c6d831912d9c453b10f1026f5153b02adf60651d8c6c5e` |
| [47] | `ref47_agrawal_2017_discrete_cbf.pdf` | https://roboticsproceedings.org/rss13/p73.pdf | E3 | `9018624cfdce8b2eb74c4705d549294530e3a71ae23c449c1b520c7125002632` |
| [48] | `ref48_andersson_2019_casadi.pdf` | https://optimization-online.org/wp-content/uploads/2018/01/6420.pdf | E0, E2, E3, E4 | `55106413bd7b129b173b32fac5007de604031a3296df731cd9a37bfc4c214239` |
| [52] | `ref52_wachter_2006_ipopt_filter_line_search.pdf` | https://cepac.cheme.cmu.edu/pasilectures/biegler/ipopt.pdf | E0, E2, E3, E4 | `2cd76f3309d034cadba43a419403fb53d6c398f0fa4e63f274907800403f078c` |

## Metadata / Link Only

| Ref | Paper | Source URL | Status | Used by |
|---|---|---|---|---|
| [2] | Garcia, Prett, and Morari, "Model predictive control: Theory and practice - A survey," 1989 | https://www.sciencedirect.com/science/article/pii/0005109889900022 | No open PDF found from an authoritative source during this pass; publisher PDF returned 403. | E0, E2, E3, E4 |
| [51] | Fiedler et al., "do-mpc: Towards FAIR nonlinear and robust model predictive control," 2023 | https://www.sciencedirect.com/science/article/pii/S0967066123002459 | Article is marked open access by ScienceDirect, but direct PDF download returned 403 from CLI. Use browser access or publisher page. | E0, E2, E3, E4 |

## Notes

- Do not commit PDF files unless the license explicitly allows redistribution and the repo policy is updated.
- Prefer arXiv, official conference proceedings, author pages, institutional repositories, and publisher open-access pages.
- Avoid uploading PDFs from ResearchGate, Academia, Scribd, or other mirrors unless rights are clear.
- If a later implementation uses a different solver stack, update the required references accordingly.
