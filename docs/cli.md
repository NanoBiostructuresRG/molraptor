# CLI Reference

The `molraptor` console command exposes the molecular pipeline and metadata checks.

## Help and Version

```bash
molraptor --help
molraptor run --help
molraptor --version
```

## Run the Pipeline

Run with the default example configuration:

```bash
molraptor run
```

Use a custom YAML configuration:

```bash
molraptor run --config path/to/config.yaml
```

Enable verbose logs:

```bash
molraptor run --verbose
```

Run with both a custom config and verbose logging:

```bash
molraptor run --config path/to/config.yaml --verbose
```

## Notes

- The `--config` flag defaults to `examples/example_config.yaml` when not specified.
- The `--verbose` flag sets the logger to `INFO` level, exposing progress
  messages from all `molraptor.*` modules. Without it, only `WARNING` and
  above are shown.