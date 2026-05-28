# API Reference

MOLRAPTOR exposes an intended public API through five symbols. The project is
pre-stable, so this API may change before 1.0. Internal modules are importable
directly but are not part of the public contract.

```python
from molraptor import MolraptorConfig
from molraptor import validate_config
from molraptor import run
from molraptor import DataValidator
from molraptor import __version__
```

---

## MolraptorConfig

::: molraptor.config.MolraptorConfig

---

## validate_config

::: molraptor.pipeline.validate_config

---

## run

::: molraptor.pipeline.run

---

## DataValidator

::: molraptor.validators.DataValidator

---

## Version

::: molraptor.version