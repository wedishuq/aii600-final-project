# Data, CERT r6.1

`analysis_cert.ipynb` reads a local extract of the CERT Insider Threat Test Dataset, release r6.1. The ICD 8031 exports stay in `data/README.md`. These archives are not republished. The ExactData terms in `data/12841247/r6.1/license-exactdata.txt` prohibit publishing the files. Download them from https://doi.org/10.1184/R1/12841247.v1 (Lindauer, Brian, 2020, Carnegie Mellon University). `answers.tar.bz2` in that record matches `CHECKSUMS-sha256.txt`.

The notebook uses `device.csv`, `logon.csv`, `file.csv`, the monthly files in `LDAP/`, and `answers.tar.bz2`. It does not read `http.csv` (78 GB), `email.csv` (7.7 GB), or `psychometric.csv`. Device time in the three logs used here runs from 2010-01-02 through 2011-05-31. The unit is one USB connect. `r6.1-4.csv` is named in `answers/insiders.csv` and is not in this copy of `answers.tar.bz2`.

SHA-256 of the files the notebook checks:

- `4d95a992730325e0704869f2e03014132ee9f98e681d8bd9c47dbbbabb36d0ac` `device.csv`
- `22b2671d1d8229c287837a958a3d2e26529ce3e2e6bbb8be06226d1e16064700` `logon.csv`
- `25050ecf9f40d9cf599dd594b43a79790e4bce29095f5bd3cfb189a0f74bd2c7` `file.csv`
- `ed21bf921def01e97326b314f2d1fa77651a945bd31bf513095f8ac7658c9ddd` `answers.tar.bz2`
