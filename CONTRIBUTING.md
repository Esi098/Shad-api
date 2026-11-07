# Built by Esi — https://t.me/Homosapien_001
# Contributing

Thanks for helping! A few ground rules:

1. **No live credentials.** Tests must stay offline; never commit session files
   or phone numbers. Use `tmp_path` fixtures.
2. **Small, typed, documented functions.** Keep the public API in `shad_api/client.py`
   and reuse `shad_api/http.py` for transport.
3. Run before opening a PR:

   ```bash
   python -m pip install -e ".[dev]"
   python -m pytest
   ```

4. Persian is welcome in issues; code and comments are English.
5. Reverse-engineered API details belong in `docs/API.md` with the endpoint name,
   payload shape and the date of verification.

Maintainer: **Esi** — [@Homosapien_001](https://t.me/Homosapien_001)
