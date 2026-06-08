# Material Defaults

MVP default yield strengths:

| Material | Yield strength MPa |
|---|---:|
| PETG | 45 |
| PLA | 55 |
| Nylon | 70 |
| Aluminum 6061-T6 | 275 |
| Aluminum 7075-T6 | 500 |

`fea_cases.yaml` should declare a material yield strength explicitly. Defaults are
only a fallback for smoke tests.
