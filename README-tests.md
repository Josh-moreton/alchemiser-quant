# Test Coverage Waiver

The current suite contains many failing integration and performance tests
requiring real services. For this iteration only lightweight CLI smoke
checks were added. As a result the coverage remains well below the desired
thresholds (approx. 20% lines, 3.6% branches).

## TODO
- Implement stable fakes for external dependencies (Alpaca, AWS secrets).
- Trim or quarantine flaky performance/regression tests.
- Add focused unit tests for trading engine, strategy manager and broker
  services.
