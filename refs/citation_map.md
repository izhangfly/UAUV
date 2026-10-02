# Citation-key map — temporary keys that will survive the Zotero migration

## Convention
Keys follow Better BibTeX's common default `[surname:lower][year][firsttitleword:lower]`
(e.g. Hoburg & Abbeel 2014 "Geometric Programming..." -> `hoburg2014geometric`). To make a future
Zotero-exported `.bib` reproduce these exact keys so no `\cite{}` breaks, do ONE of:
- **(A)** Zotero -> Better BibTeX prefs -> citation-key format: `auth.lower + year + veryshorttitle(1,0).lower`; or
- **(B)** per item, right-click -> Better BibTeX -> **Pin citation key** and paste the key below.
Then export the collection as *Better BibTeX* and replace `refs/uauv.bib`.

## Map (citekey  ->  refs/ file  ->  reference; VERIFY = confirm from OCR)
| citekey | refs/ file | reference |
|---|---|---|
| hoburg2014geometric | 2012_gp_design (1).pdf | Hoburg & Abbeel, "Geometric Programming for Aircraft Design Optimization," AIAA J. 52(11), 2014 |
| boyd2007tutorial | gp_tutorial.pdf | Boyd, Kim, Vandenberghe, Hassibi, "A Tutorial on Geometric Programming," Optim. Eng. 8(1), 2007 |
| allen2000propulsion | Oceans2000final.pdf | Allen, Vorus, Prestero, "Propulsion System Performance Enhancements on REMUS AUVs," OCEANS 2000 |
| myring1976theoretical | (cited by allen2000) / 19750011517.pdf? | Myring, "A Theoretical Study of Body Drag in Subcritical Axisymmetric Flow," Aero. Q. 27(3), 1976 |
| hoerner1965fluid | Hoerner_1965_Fluid-dynamic_drag.pdf | Hoerner, "Fluid-Dynamic Drag," 1965 |
| hoerner1985fluid | Fluid-dynamic_lift__Hoerner__1985_text.pdf | Hoerner & Borst, "Fluid-Dynamic Lift," 1985 |
| renilson2018submarine | Submarine Hydrodynamics ( PDFDrive ).pdf | Renilson, "Submarine Hydrodynamics," Springer, 2nd ed. 2018 |
| newman2018marine | Marine_Hydrodynamics_Newman_2018.pdf | Newman, "Marine Hydrodynamics," MIT Press (40th anniv.) |
| brennen2014cavitation | brennen-...-2014.pdf | Brennen, "Cavitation and Bubble Dynamics," Cambridge, 2014 |
| fossen2011handbook | handbook-of-marine-craft-...pdf | Fossen, "Handbook of Marine Craft Hydrodynamics and Motion Control," Wiley, 2011 |
| dzielski2003benchmark | Dzielski_Kurdila_2003_....pdf | Dzielski & Kurdila, "A Benchmark Control Problem for Supercavitating Vehicles," 2003 — VERIFY venue |
| zou2023optimized | Zou et al_2023_....pdf | Zou et al., "Optimized design of ... supercavitating vehicles," 2023 — VERIFY authors/venue |
| long2025entire | (Desktop) | Long et al., "Entire aerial-aquatic trajectory...," Defence Technology 49, 2025 |

## Still to identify from OCR (no key yet)
- 19750011517.pdf (281 pp NASA compilation) — confirm what it is; may contain the true Myring source.
- EECS-2015-22.pdf — UC Berkeley EECS tech report; confirm author/title.
- bubbook.pdf — likely Brennen multiphase; confirm.
- preview-9781139089203_A23866158.pdf — Cambridge book preview (ISBN 9781139089203); confirm title.
