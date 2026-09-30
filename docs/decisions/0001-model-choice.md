# ADR 0001: start with an explainable local policy

## Decision

We start the working demo with a deterministic, inspectable policy rather than pretending a graph model has been trained. It gives the payer and guardian flows genuine end-to-end behaviour while preserving the boundary for a future SageLite model.

## Consequences

The policy is not a fraud probability and its smoke-evaluation metrics are not comparable with the proposed federated benchmark. A future SageLite MLP over fixed-size neighbourhood aggregates remains the chosen served architecture because it can export to ONNX and run efficiently on CPU.

