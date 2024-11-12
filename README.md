# azure-db

Operations related to semantic search on our Azure document index.

## Packaging and release workflow

The pipeline triggers on PRs to check code quality, markdown, repository
standards, and ensures that the version in `setup.py` is bumped depending on the
project folder. When a PR is merged, the workflow automatically creates a
release based on the version in `seetup.py` of the respective folder and
packages only the project files. The latest releases and changelogs are
available [here](https://github.com/ai-cfia/azure-db/releases).

To use packages from this monorepo in other projects, add the specific package
to your `requirements.txt` :

```sh
git+https://github.com/ai-cfia/azure-db.git@vX.X.X-azure-ai-search
```

Where `vX.X.X` is the version from the [release
page](https://github.com/ai-cfia/azure-db/releases).
