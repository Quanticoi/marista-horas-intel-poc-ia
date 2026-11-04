# serving-after-restart

PASS — 2026-11-04T20:07:38.018293+00:00

Código: sha256:c3a9af6b6859448a4fba9603744e3529671c9b735b1eb6b668f9b4a7987b9c9e

Evidência: [serving-after-restart.json](serving-after-restart.json)

- Six explicit versions sampled from 500 real training results; not 500 concurrent loaded models
- Cold and warm requests mixed; six-version round robin exceeds four-entry cache