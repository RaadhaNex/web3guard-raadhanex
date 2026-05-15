# Web3Guard AI by RAADHANEX — Phase 14 Summary

## Added

- Deep-analysis scanner page: `/scanner/deep-analysis`
- Deep-analysis status API: `GET /scan/deep-analysis/status`
- Deep-analysis run API: `POST /scan/deep-analysis`
- Real-only tool runner architecture for:
  - Mythril
  - Manticore
  - Echidna
- Standard/deep mode ownership-verification gate
- Tool status findings when tools are disabled or missing
- Mythril JSON parser
- Echidna JSON parser
- Manticore text evidence parser
- Dashboard save support for deep-analysis scans
- Phase 14 tests and backend smoke coverage

## Real-only guarantee

No fake symbolic execution, no fake fuzzing result, no fake Mythril/Manticore/Echidna output.

## Manual setup required

Install tools separately and enable env flags only after installation.

```env
DEEP_ANALYSIS_ENABLED=true
MYTHRIL_ENABLED=true
MANTICORE_ENABLED=true
ECHIDNA_ENABLED=true
```

If binaries are not on PATH:

```env
MYTHRIL_BINARY=C:\\path\\to\\myth.exe
MANTICORE_BINARY=C:\\path\\to\\manticore.exe
ECHIDNA_BINARY=C:\\path\\to\\echidna.exe
```

## Production warning

For public production, deep tools should run in isolated Docker workers, not directly in the API server.
