# Demo: a release with exactly the gaps real releases have

```
demo/
├── paper.md      # three paper claims, two baselines, one table
└── code/         # a plausible release with three different failure modes
```

Run it:

```bash
reprocheck assess examples/demo/paper.md --repo examples/demo/code --smoke
```

Expected verdict: **R2**, because the release has no missing checkpoint and no
restricted dataset, but three claims sit at different evidence levels:

| Claim | Why | Level |
|---|---|---|
| ImageNet top-1 = 72.3 | `top1_accuracy` exists, ImageNet is referenced, the number itself is absent | E2 |
| Zero-shot ImageNet = 45.1 | no zero-shot implementation, only the dataset is mentioned | E3 |
| COCO mAP = 0.41 | nothing in the repository matches metric, dataset or value | X |

The release also trips RC02 (unpinned torch/numpy/pyyaml/tqdm), RC03
(`/data/imagenet` hard-coded in two files), RC13 (`sklearn` imported but never
declared), and RC17 (one claim with no counterpart).

What would move it to R1: publish `evaluate.py` with a checkpoint path that does
not exist, or gate the dataset behind a request form.

What would move it to R3: ship a `results.json` containing `72.3` and `45.1`,
implement zero-shot evaluation, and run with `--smoke`.
