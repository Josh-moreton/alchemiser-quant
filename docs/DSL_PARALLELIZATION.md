# DSL Strategy Engine Parallelization

The DSL Strategy Engine now supports parallel evaluation of multiple strategy files to reduce wall-clock time while preserving deterministic results and maintaining the current synchronous public API.

## Overview

When multiple DSL strategy files are configured, they can now be evaluated in parallel using either thread-based or process-based parallelism. This is particularly beneficial when:

- Running 10-50+ strategy files
- Strategies perform I/O operations (data reads)
- Strategies use NumPy/pandas operations that release the GIL
- Pure Python CPU-bound processing can benefit from multiprocessing

## Usage

### Basic Usage

```python
from datetime import datetime
from the_alchemiser.strategy_v2.engines.dsl.strategy_engine import DslStrategyEngine

# Create engine
engine = DslStrategyEngine(market_data_port, "strategy.clj")

# Sequential execution (default)
signals = engine.generate_signals(datetime.now())

# Threaded execution
signals = engine.generate_signals(
    datetime.now(), 
    parallelism="threads", 
    max_workers=4
)

# Process-based execution
signals = engine.generate_signals(
    datetime.now(), 
    parallelism="processes", 
    max_workers=2
)
```

### Parameters

- **`parallelism`**: One of `"none"`, `"threads"`, or `"processes"` (default: `"none"`)
- **`max_workers`**: Maximum number of workers (default: `min(len(files), os.cpu_count())`)

### Environment Configuration

Override parallelism settings using environment variables:

```bash
export ALCHEMISER_DSL_PARALLELISM=threads
export ALCHEMISER_DSL_MAX_WORKERS=4
```

These environment variables take precedence over method parameters.

## Execution Modes

### Sequential (`parallelism="none"`)
- **Default behavior** - maintains backward compatibility
- Evaluates files one at a time in order
- Best for: debugging, single file, or when parallelism overhead isn't worth it

### Threaded (`parallelism="threads"`)
- Uses `ThreadPoolExecutor` for parallel execution
- **Recommended for most use cases**
- Best for: I/O-bound operations, NumPy/pandas work (GIL released)
- Lower overhead than processes

### Process-based (`parallelism="processes"`)
- Uses `ProcessPoolExecutor` for parallel execution
- Best for: CPU-bound pure Python operations
- Higher overhead due to process creation and IPC
- Note: Requires all inputs to be pickle-serializable

## Deterministic Ordering

**Key Feature**: Parallel execution preserves deterministic ordering of results.

- Uses `executor.map()` to maintain input file order
- Results are consolidated in the same order regardless of completion time
- Sequential and parallel modes produce identical outputs for the same inputs
- Essential for reproducible trading strategies

## Correlation ID Tracing

Correlation IDs are propagated to all parallel workers for end-to-end traceability:

```python
# Generated correlation ID flows through all workers
correlation_id = str(uuid.uuid4())
# Each worker logs with the same correlation_id for traceability
```

## Performance Considerations

### When to Use Threading
- **I/O-heavy strategies**: File reads, network requests, database queries
- **NumPy/pandas operations**: C extensions release the GIL
- **Mixed workloads**: Combination of I/O and computation
- **Lower overhead**: Faster startup, shared memory

### When to Use Processes
- **CPU-bound pure Python**: Heavy calculations without C extensions
- **Memory isolation**: When strategies might have memory leaks
- **Fault isolation**: Process crashes don't affect other evaluations

### Automatic Fallbacks
- **Single file**: Automatically uses sequential mode regardless of `parallelism` setting
- **Failed workers**: Gracefully handles individual file evaluation failures
- **Resource limits**: Respects `max_workers` to prevent resource exhaustion

## Observability & Logging

Structured logging includes parallelism configuration:

```json
{
  "message": "Generating DSL signals from 5 files",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "parallelism": "threads",
  "max_workers": 4,
  "timestamp": "2024-01-01T10:00:00Z"
}
```

## Error Handling

### Graceful Degradation
- Individual file failures don't stop the entire evaluation
- Failed files are skipped with error logging
- Successful files still contribute to the final allocation

### Exception Safety
- Worker exceptions are caught and logged
- Correlation IDs maintained for failed evaluations
- Deterministic error handling preserves result ordering

## Best Practices

1. **Start with threading**: Lower overhead, works for most cases
2. **Profile your workload**: Measure actual speedup in your environment
3. **Monitor resource usage**: Watch CPU, memory, and I/O utilization
4. **Use correlation IDs**: Essential for debugging parallel evaluations
5. **Test determinism**: Verify identical results across execution modes
6. **Environment overrides**: Use env vars for deployment-specific tuning

## Testing

Comprehensive test suite validates:
- Deterministic ordering across all execution modes
- Correlation ID propagation to workers
- Environment variable overrides
- Error handling and graceful degradation
- Performance characteristics

Run tests:
```bash
pytest tests/strategy_v2/engines/dsl/test_parallelization.py -v
```