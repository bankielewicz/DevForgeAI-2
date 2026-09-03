# SubagentStop live prompts

1. `Launch exactly one registered red_dev subagent. Give it the task: "Run the disposable receipt-continuation probe." Wait for it to finish. Do not use any other tools or launch any other agent. Report the final outcome and stop.`
2. `Launch exactly one registered green_dev subagent. Give it the task: "Run the disposable bounded-invalid-output probe." Wait for it to finish. Do not use any other tools or launch any other agent. Report the final outcome and stop.`

The exact disposable role profiles are preserved in `receipts/red_dev.toml` and `receipts/green_dev.toml`.
