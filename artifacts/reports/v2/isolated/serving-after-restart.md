# serving-after-restart

PASS — 2026-11-04T16:57:45.634954+00:00

Código: sha256:0133b02d6c27fba2db326cf52ccdeada7ec5f05c63034629b818fcfaa783637c

Evidência: [serving-after-restart.json](serving-after-restart.json)

- Six explicit versions sampled from 500 real training results; not 500 concurrent loaded models
- Cold and warm requests mixed; six-version round robin exceeds four-entry cache