# Running act with workflows

## Single workflow events

If you want to run a single integration test with inputs use one of the event files in this directory, or create
your own.

```shell
act -W .github/workflows/single_integration_test.yml --eventpath .github/examples/bdr-simple-event.json workflow_dispatch
```
