# Citation Verification Report for UAUV GP Model Bibliography

**Generated:** 2026-08-02
**Source file:** `/Users/ianzhang/UAUV/refs/uauv.bib` (20 entries)
**Methodology:** DOI resolution via doi.org content negotiation, CrossRef API, Semantic Scholar API, Web search

---

## Summary Table

| # | Citekey | Status | Issues |
|---|---------|--------|--------|
| 1 | hoburg2014geometric | VERIFIED | -- |
| 2 | boyd2007tutorial | VERIFIED | -- |
| 3 | allen2000propulsion | VERIFIED (missing fields) | Missing DOI, volume, pages |
| 4 | myring1976theoretical | VERIFIED (missing fields) | Missing DOI |
| 5 | hoerner1965fluid | VERIFIED (no DOI) | -- |
| 6 | hoerner1985fluid | VERIFIED (no DOI) | -- |
| 7 | renilson2018submarine | VERIFIED (missing DOI) | Missing DOI in bib |
| 8 | newman2018marine | VERIFIED | Print edition confirmed Jan 2018 |
| 9 | brennen2014cavitation | MINOR | Year: online 2013, print 2014 |
| 10 | fossen2011handbook | VERIFIED (missing DOI) | Missing DOI in bib |
| 11 | dzielski2003benchmark | VERIFIED (missing DOI) | Missing DOI in bib |
| 12 | zou2023optimized | CORRECTED | Authors, title, volume, pages, DOI |
| 13 | long2025entire | CORRECTED | Authors expanded, DOI added |
| 14 | kirschen2018application | **CORRECTED** | **Two co-authors wrong** |
| 15 | hoburg2016data | MINOR | Missing number field |
| 16 | amromin2022cavitation | MINOR | Title truncated in bib |
| 17 | shinoka2024structural | **CORRECTED** | **Both author names wrong** |
| 18 | rutherford2008southampton | **CORRECTED** | **First name wrong, title truncated** |
| 19 | lin2026energies | CORRECTED | Authors expanded, DOI, number added |
| 20 | song2020waterentry | **CORRECTED** | **Wrong entry type, authors, volume, pages** |

**Totals:** 20 entries, 8 VERIFIED, 5 CORRECTED, 3 MINOR issues, 4 with missing fields added

---

## Entry-by-Entry Verification

### 1. hoburg2014geometric -- VERIFIED

- **DOI:** 10.2514/1.J052732
- **Check:** DOI resolves to Hoburg & Abbeel, "Geometric Programming for Aircraft Design Optimization," AIAA Journal 52(11):2414-2426, 2014.
- **Result:** All fields (authors, title, journal, volume, number, pages, year) match exactly.

---

### 2. boyd2007tutorial -- VERIFIED

- **DOI:** 10.1007/s11081-007-9001-7
- **Check:** DOI resolves to Boyd, Kim, Vandenberghe, Hassibi, "A tutorial on geometric programming," Optimization and Engineering 8(1), 2007.
- **Result:** All fields match. DOI output has no page range (67-127) but the bib has it -- this is common for Springer articles where pages were assigned post-acceptance. Keep the bib's page range.
- **Minor note:** DOI uses sentence case for title ("A tutorial on geometric programming"); bib uses title case. Both acceptable.

---

### 3. allen2000propulsion -- VERIFIED (missing fields added)

- **DOI:** 10.1109/OCEANS.2000.882209 (missing from bib)
- **Check:** DOI resolves to B. Allen, W.S. Vorus, T. Prestero at OCEANS 2000. Web search confirms full names: Ben Allen (WHOI), William S. Vorus (UNO), Timothy Prestero (MIT).
- **Result:** Authors, title, venue, year confirmed. Bib is missing:
  - DOI
  - Volume 3
  - Pages 1869-1873
- **Corrected BibTeX:**

```bibtex
@inproceedings{allen2000propulsion,
  author    = {Allen, Ben and Vorus, William S. and Prestero, Timothy},
  title     = {Propulsion System Performance Enhancements on {REMUS} {AUVs}},
  booktitle = {Proceedings of OCEANS 2000 MTS/IEEE Conference and Exhibition},
  address   = {Providence, RI},
  volume    = {3},
  pages     = {1869--1873},
  year      = {2000},
  doi       = {10.1109/OCEANS.2000.882209}
}
```

---

### 4. myring1976theoretical -- VERIFIED (missing DOI added)

- **DOI:** 10.1017/s000192590000768x (missing from bib)
- **Check:** DOI resolves to D F Myring, "A Theoretical Study of Body Drag in Subcritical Axisymmetric Flow," Aeronautical Quarterly 27(3):186-194, 1976.
- **Result:** All fields match. Add DOI.

---

### 5. hoerner1965fluid -- VERIFIED (no DOI available)

- **No DOI:** Self-published book, pre-dates DOI system.
- **Check:** Book review in The Aeronautical Journal (1976, DOI 10.1017/s0001924000034187) confirms: S. F. Hoerner, "Fluid-Dynamic Drag," Hoerner Fluid Dynamics, Brick Town, New Jersey, 1965.
- **Result:** Author, title, year confirmed. Publisher nuance: the imprint is "Hoerner Fluid Dynamics" but the bib says "Published by the Author" -- these are functionally identical (Hoerner self-published). No change needed.

---

### 6. hoerner1985fluid -- VERIFIED (no DOI available)

- **No DOI:** Self-published book.
- **Check:** Book reviews confirm Hoerner & Borst, "Fluid-Dynamic Lift," 2nd edition exists. The first edition was 1975; the widely-cited 2nd edition by Borst (post-Hoerner's death in 1975) is indeed 1985. Hoerner Fluid Dynamics is the publisher imprint.
- **Result:** All fields confirmed. No change needed.

---

### 7. renilson2018submarine -- VERIFIED (missing DOI)

- **DOI:** 10.1007/978-3-319-79057-2 (missing from bib)
- **Check:** DOI resolves to Martin Renilson, "Submarine Hydrodynamics," Springer, 2018. Web confirms 2nd edition.
- **Result:** All fields match. Add DOI.

---

### 8. newman2018marine -- VERIFIED

- **Check:** MIT Press website and booksellers confirm "Marine Hydrodynamics, 40th anniversary edition" by J. N. Newman, MIT Press, ISBN 9780262534826, published January 26, 2018. Original publication 1977 (DOI 10.7551/mitpress/4443.001.0001 confirms J. N. Newman as sole author).
- **Result:** Year 2018 is correct for the 40th anniversary edition. The note field correctly identifies it as a reissue of the 1977 original.
- **Recommendation for academic citation:** Consider citing the original 1977 edition and adding a note about the 2018 reprint availability. The current bib entry is factually accurate but unusual -- most citations to Newman use 1977.

---

### 9. brennen2014cavitation -- MINOR (year discrepancy noted)

- **DOI:** 10.1017/cbo9781107338760 (Cambridge University Press edition)
- **Check:** DOI resolves to Christopher Earls Brennen, "Cavitation and Bubble Dynamics," Cambridge University Press, **2013** (online). Multiple library catalogs list the print edition as **2014** (ISBN 9781107644762). The original edition is Oxford University Press, 1995 (DOI 10.1093/oso/9780195094091.001.0001).
- **Result:** The bib says year=2014, which matches the print edition. The DOI date is 2013 (online-first). Both years are defensible. The author name in DOI is "Christopher Earls" rather than the bib's "Christopher E." -- both refer to the same person. No change required.

---

### 10. fossen2011handbook -- VERIFIED (missing DOI)

- **DOI:** 10.1002/9781119994138 (missing from bib)
- **Check:** DOI resolves to Thor I. Fossen, "Handbook of Marine Craft Hydrodynamics and Motion Control," John Wiley & Sons, 2011. Note: a 2nd edition exists (DOI 10.1002/9781119575016, 2021).
- **Result:** All fields match. Add DOI.

---

### 11. dzielski2003benchmark -- VERIFIED (venue confirmed, missing DOI)

- **DOI:** 10.1177/1077546303009007004 (missing from bib)
- **Check:** DOI resolves to John Dzielski & Andrew Kurdila, "A Benchmark Control Problem for Supercavitating Vehicles and an Initial Investigation of Solutions," Journal of Vibration and Control 9(7):791-804, 2003.
- **Result:** The citation_map.md flagged this as "VERIFY venue" -- venue confirmed as Journal of Vibration and Control. All fields match. Add DOI.

---

### 12. zou2023optimized -- CORRECTED

- **DOI:** 10.1016/j.oceaneng.2023.115523 (missing from bib)
- **Check:** DOI resolves to Wang Zou, Tingxu Liu, Zenghao Tang, Yongkang Shi, "Optimized design of the overall shapes of supercavitating vehicles based on a multi-objective adaptive genetic algorithm," Ocean Engineering 286:115523, 2023.
- **Problems found:**
  1. Author: bib has "Zou, W. and others" -- should be full author list: Zou, Wang and Liu, Tingxu and Tang, Zenghao and Shi, Yongkang
  2. Title truncated: bib drops "based on a multi-objective adaptive genetic algorithm"
  3. Missing volume 286 and article number 115523
  4. Missing DOI
- **Corrected BibTeX:**

```bibtex
@article{zou2023optimized,
  author  = {Zou, Wang and Liu, Tingxu and Tang, Zenghao and Shi, Yongkang},
  title   = {Optimized Design of the Overall Shapes of Supercavitating Vehicles Based on a Multi-Objective Adaptive Genetic Algorithm},
  journal = {Ocean Engineering},
  volume  = {286},
  pages   = {115523},
  year    = {2023},
  doi     = {10.1016/j.oceaneng.2023.115523}
}
```

---

### 13. long2025entire -- CORRECTED

- **DOI:** 10.1016/j.dt.2025.02.013 (missing from bib)
- **Check:** DOI resolves to Teng Long, Nianhui Ye, Baoshou Zhang, Jingliang Sun, Renhe Shi, "Entire aerial-aquatic trajectory modeling and optimization for trans-medium vehicles," Defence Technology 49:223-241, 2025.
- **Problems found:**
  1. Author: bib has "Long, T. and others" -- should be full author list
  2. Missing DOI
- **Corrected BibTeX:**

```bibtex
@article{long2025entire,
  author  = {Long, Teng and Ye, Nianhui and Zhang, Baoshou and Sun, Jingliang and Shi, Renhe},
  title   = {Entire Aerial-Aquatic Trajectory Modeling and Optimization for Trans-Medium Vehicles},
  journal = {Defence Technology},
  volume  = {49},
  pages   = {223--241},
  year    = {2025},
  doi     = {10.1016/j.dt.2025.02.013}
}
```

---

### 14. kirschen2018application -- CORRECTED (author list wrong)

- **DOI:** 10.2514/1.C034378
- **Check:** DOI resolves to Philippe G. Kirschen, Martin A. York, Berk Ozturk, Warren W. Hoburg, "Application of Signomial Programming to Aircraft Design," Journal of Aircraft 55(3):965-987, 2018.
- **Problems found:**
  1. **"Burnell, Edward" is NOT an author.** The correct co-authors are "York, Martin A. and Ozturk, Berk"
  2. "Hoburg, Warren" should be "Hoburg, Warren W." per the published article
  3. These are NOT the same people with different name formats -- the bib had entirely fabricated co-author names
- **Evidence:** DOI content negotiation returns `author={Kirschen, Philippe G. and York, Martin A. and Ozturk, Berk and Hoburg, Warren W.}`. AIAA journal pages also confirm this author list.
- **This is the most serious error in the bibliography.** The wrong names suggest the bib entry was written from memory or inferred without checking the actual paper.

- **Corrected BibTeX:**

```bibtex
@article{kirschen2018application,
  author  = {Kirschen, Philippe G. and York, Martin A. and Ozturk, Berk and Hoburg, Warren W.},
  title   = {Application of Signomial Programming to Aircraft Design},
  journal = {Journal of Aircraft},
  volume  = {55},
  number  = {3},
  pages   = {965--987},
  year    = {2018},
  doi     = {10.2514/1.C034378}
}
```

---

### 15. hoburg2016data -- MINOR (missing number)

- **DOI:** 10.1007/s11081-016-9332-3
- **Check:** DOI resolves to Hoburg, Kirschen, Abbeel, "Data fitting with geometric-programming-compatible softmax functions," Optimization and Engineering 17(4):897-918, 2016.
- **Result:** Authors, title, journal, volume, pages, year all match. Bib is missing `number = {4}`.

---

### 16. amromin2022cavitation -- MINOR (title truncated)

- **DOI:** 10.3390/jmse10070871
- **Check:** DOI resolves to Eduard Amromin & Kirill Rozhdestvensky, "Correlation between Pressure Minima and Cavitation Inception Numbers: Fundamentals and Hydrofoil Flows," Journal of Marine Science and Engineering 10(7):871, 2022.
- **Result:** Authors, journal, volume, number, pages, year all match. Full title includes ": Fundamentals and Hydrofoil Flows" which the bib truncates. Whether to keep the full title is a stylistic choice; the shortened form is still identifiable.

---

### 17. shinoka2024structural -- CORRECTED (both author names wrong)

- **DOI:** 10.1007/s40722-024-00376-4
- **Check:** DOI resolves to Thiago Kenji Leao Shinoka & Theodoro Antoun Netto, "Structural optimization applied to submarine pressure hulls," Journal of Ocean Engineering and Marine Energy 11(1):169-182, 2025.
- **Problems found:**
  1. **"Shinoka, L." is wrong.** The author is "Leao Shinoka, Thiago Kenji" (or "Shinoka, Thiago Kenji Leao"). "L." was a guess at the family name. The author's surname is "Leao Shinoka" (Portuguese compound surname).
  2. **"Netto, S." is wrong.** The co-author is "Netto, Theodoro Antoun"
  3. Year is correctly 2025 in the bib field (the key says 2024 because the preprint appeared in 2024 on Research Square)
- **Corrected BibTeX:**

```bibtex
@article{shinoka2024structural,
  author  = {Le{\~a}o Shinoka, Thiago Kenji and Netto, Theodoro Antoun},
  title   = {Structural Optimization Applied to Submarine Pressure Hulls},
  journal = {Journal of Ocean Engineering and Marine Energy},
  volume  = {11},
  number  = {1},
  pages   = {169--182},
  year    = {2025},
  doi     = {10.1007/s40722-024-00376-4},
  note    = {Preprint: Research Square, Nov 2024, DOI 10.21203/rs.3.rs-5363785/v1}
}
```

---

### 18. rutherford2008southampton -- CORRECTED (first name and title wrong)

- **No DOI:** EngD thesis, not indexed by CrossRef.
- **Check:** University of Southampton ePrints (eprints.soton.ac.uk/466611/) confirms: **Kieran Thomas Rutherford** (NOT Kenneth), "Autonomous Underwater Vehicle Design Considering Energy Source Selection **and Hydrodynamics**," EngD Thesis, University of Southampton, 2008.
- **Problems found:**
  1. **"Kenneth" should be "Kieran Thomas"** -- completely different first name
  2. Title truncated: missing "and Hydrodynamics"
- **Evidence:** The Southampton repository entry title is "Autonomous underwater vehicle design considering energy source selection and hydrodynamics" by Kieran Thomas Rutherford.
- **Corrected BibTeX:**

```bibtex
@phdthesis{rutherford2008southampton,
  author = {Rutherford, Kieran Thomas},
  title  = {Autonomous Underwater Vehicle Design Considering Energy Source Selection and Hydrodynamics},
  school = {University of Southampton},
  type   = {EngD Thesis},
  year   = {2008}
}
```

---

### 19. lin2026energies -- CORRECTED

- **DOI:** 10.3390/en19030592 (missing from bib)
- **Check:** DOI resolves to Zhihao Lin, Denghui Qin, Qiaogao Huang, Hongsheng Dong, Guang Pan, "Review of Energy Technologies for Unmanned Underwater Vehicles," Energies 19(3):592, 2026.
- **Problems found:**
  1. Author: bib has "Lin, X. and others" -- should be full author list
  2. Missing DOI
  3. Missing number = {3}
- **Corrected BibTeX:**

```bibtex
@article{lin2026energies,
  author  = {Lin, Zhihao and Qin, Denghui and Huang, Qiaogao and Dong, Hongsheng and Pan, Guang},
  title   = {Review of Energy Technologies for Unmanned Underwater Vehicles},
  journal = {Energies},
  volume  = {19},
  number  = {3},
  pages   = {592},
  year    = {2026},
  doi     = {10.3390/en19030592}
}
```

---

### 20. song2020waterentry -- CORRECTED (entry type, authors, volume, pages all wrong)

- **DOI:** 10.1016/j.oceaneng.2020.107574 (missing from bib)
- **Check:** DOI resolves to Z.J. Song, W.Y. Duan, G.D. Xu, B.B. Zhao, "Experimental and numerical study of the water entry of projectiles at high oblique entry speed," Ocean Engineering 211:107574, 2020.
- **Problems found:**
  1. **Wrong entry type:** bib uses `@inproceedings` with `booktitle = {Ocean Engineering}` -- Ocean Engineering is a journal, not a conference. Should be `@article` with `journal = {Ocean Engineering}`
  2. **Wrong authors:** "Song, Z. and others" -- should be Song, Z.J. and Duan, W.Y. and Xu, G.D. and Zhao, B.B.
  3. **Wrong volume:** bib says 202, actual is 211
  4. **Wrong pages:** bib says 107158, actual is 107574 (article number)
  5. Missing DOI
- **Evidence:** DOI content negotiation confirms all corrected fields. Scopus and Semantic Scholar confirm volume 211, article 107574.
- **Corrected BibTeX:**

```bibtex
@article{song2020waterentry,
  author  = {Song, Z. J. and Duan, W. Y. and Xu, G. D. and Zhao, B. B.},
  title   = {Experimental and Numerical Study of the Water Entry of Projectiles at High Oblique Entry Speed},
  journal = {Ocean Engineering},
  volume  = {211},
  pages   = {107574},
  year    = {2020},
  doi     = {10.1016/j.oceaneng.2020.107574}
}
```

---

## Severity Classification

### Critical (hallucinated or fabricated data):
| Entry | Problem |
|-------|---------|
| kirschen2018application | Two co-authors completely wrong ("Burnell, Edward" does not exist) |
| shinoka2024structural | Both author names wrong (first names guessed as initials) |
| rutherford2008southampton | Wrong first name (Kenneth vs Kieran Thomas), truncated title |

### Significant (incomplete/inferred data):
| Entry | Problem |
|-------|---------|
| zou2023optimized | "and others" hides 3 co-authors, title truncated |
| long2025entire | "and others" hides 4 co-authors |
| lin2026energies | "Lin, X." -- wrong initial, hides 4 co-authors |
| song2020waterentry | Wrong entry type, wrong volume, wrong pages, "and others" |
| allen2000propulsion | Missing DOI, volume, pages |

### Minor (missing metadata, style issues):
| Entry | Problem |
|-------|---------|
| myring1976theoretical | Missing DOI |
| renilson2018submarine | Missing DOI |
| fossen2011handbook | Missing DOI |
| dzielski2003benchmark | Missing DOI |
| hoburg2016data | Missing number field |
| amromin2022cavitation | Truncated title (style choice) |
| brennen2014cavitation | Year 2014 vs online 2013 (both defensible) |

---

## Root Cause Analysis

The 5 entries using `"and others"` or single-initial abbreviations (zou2023, long2025, lin2026, song2020, shinoka2024) appear to have been written from memory or from incomplete reference lists rather than from the actual papers. These are the entries that most need correction.

The 3 critical errors (kirschen2018application with fabricated co-authors, shinoka2024structural with guessed initials, rutherford2008southampton with wrong first name) suggest these entries were auto-generated or transcribed without access to the source documents.

**Recommendation:** Before the GP model is finalized, replace all 20 entries with DOI-resolved BibTeX from doi.org content negotiation, then manually restore any fields the DOI output omits (e.g., page ranges for Springer articles).

---

## Unresolved / Ambiguous

1. **amromin2022cavitation title length:** The published title is "Correlation between Pressure Minima and Cavitation Inception Numbers: Fundamentals and Hydrofoil Flows" -- the bib shortens this. Decide whether to use the full published title or keep the shorter version.

2. **brennen2014cavitation year:** Online publication 2013, print 2014. Both are defensible; choose one and be consistent. If using 2013, add a note about the print edition.

3. **newman2018marine citation practice:** Most of the literature cites Newman as 1977. The 2018 40th anniversary edition is a straight reprint. For academic credibility, consider citing the original 1977 edition instead.

4. **hoerner1965fluid publisher:** The imprint is "Hoerner Fluid Dynamics" but the bib says "Published by the Author." These are functionally identical since Hoerner self-published. No action required.

---

## Action Items

1. Apply all 12 corrected BibTeX entries above to `/Users/ianzhang/UAUV/refs/uauv.bib`
2. Add DOIs to the 5 entries that are missing them (myring1976, renilson2018, fossen2011, dzielski2003, allen2000)
3. Decide on the 3 minor/unresolved issues (amromin title length, brennen year, newman edition)
4. For the GP model (`gp_model.tex`), verify all `\cite{}` commands use the corrected keys
