# Wheel provenance

Downloaded on 2026-09-04 from PyPI with:

```bash
python3 -m pip download --only-binary=:all: --platform manylinux2014_x86_64 --python-version 3.12 \
  --implementation cp --abi cp312 -d wheels 'PyYAML==6.0.3' 'jsonschema==4.26.0'
```

`pypi_sha256` is the digest PyPI publishes for the file (JSON API `https://pypi.org/pypi/<project>/<version>/json`, fetched 2026-09-04T15:51:34Z); `local_sha256` was computed from the downloaded bytes; both must be equal and both equal the `--hash` in `requirements.lock`. A reviewer re-derives every line with `sha256sum wheels/*.whl` and the API.

| File | Project | Version | Size | PyPI URL | PyPI upload time | pypi_sha256 | local_sha256 |
|---|---|---|---|---|---|---|---|
| `attrs-26.1.0-py3-none-any.whl` | attrs | 26.1.0 | 67548 | https://files.pythonhosted.org/packages/64/b4/17d4b0b2a2dc85a6df63d1157e028ed19f90d4cd97c36717afef2bc2f395/attrs-26.1.0-py3-none-any.whl | 2026-03-19T14:22:23.645947Z | `c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309` | `c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309` |
| `jsonschema-4.26.0-py3-none-any.whl` | jsonschema | 4.26.0 | 90630 | https://files.pythonhosted.org/packages/69/90/f63fb5873511e014207a475e2bb4e8b2e570d655b00ac19a9a0ca0a385ee/jsonschema-4.26.0-py3-none-any.whl | 2026-01-07T13:41:05.306692Z | `d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce` | `d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce` |
| `jsonschema_specifications-2025.9.1-py3-none-any.whl` | jsonschema-specifications | 2025.9.1 | 18437 | https://files.pythonhosted.org/packages/41/45/1a4ed80516f02155c51f51e8cedb3c1902296743db0bbc66608a0db2814f/jsonschema_specifications-2025.9.1-py3-none-any.whl | 2025-09-08T01:34:57.871954Z | `98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe` | `98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe` |
| `pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | PyYAML | 6.0.3 | 807870 | https://files.pythonhosted.org/packages/8b/9d/b3589d3877982d4f2329302ef98a8026e7f4443c765c46cfecc8858c6b4b/pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl | 2025-09-25T21:32:16.431392Z | `ba1cc08a7ccde2d2ec775841541641e4548226580ab850948cbfda66a1befcdc` | `ba1cc08a7ccde2d2ec775841541641e4548226580ab850948cbfda66a1befcdc` |
| `referencing-0.37.0-py3-none-any.whl` | referencing | 0.37.0 | 26766 | https://files.pythonhosted.org/packages/2c/58/ca301544e1fa93ed4f80d724bf5b194f6e4b945841c5bfd555878eea9fcb/referencing-0.37.0-py3-none-any.whl | 2025-10-13T15:30:47.625937Z | `381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231` | `381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231` |
| `rpds_py-2026.6.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | rpds-py | 2026.6.3 | 366189 | https://files.pythonhosted.org/packages/04/8f/d2f3f532616be4d06c316ef119683e832bd3d41e112bf3a88f4151c95b17/rpds_py-2026.6.3-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl | 2026-06-30T07:15:23.371495Z | `ecabd69db66de867690f9797f2f8fa27ba501bbc24540cbdbdc649cd15888ba6` | `ecabd69db66de867690f9797f2f8fa27ba501bbc24540cbdbdc649cd15888ba6` |
| `typing_extensions-4.16.0-py3-none-any.whl` | typing-extensions | 4.16.0 | 45571 | https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl | 2026-07-02T08:40:04.659120Z | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` | `481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8` |

Direct dependencies: PyYAML (record loading), jsonschema (Draft 2020-12 validation). The rest are jsonschema's transitive dependencies as resolved by pip on the download date: attrs, jsonschema-specifications, referencing, rpds-py, typing-extensions.

No wheel is executed or imported by DevForgeAI's own tests except through `pip install --no-index --require-hashes` into a scratch `lib/` in `tests/test_devforge_release.py`; the staged validator in this repository keeps using the developer's environment.
