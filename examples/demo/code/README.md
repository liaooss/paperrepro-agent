# TinyCLIP

Official code release for **TinyCLIP: Efficient Contrastive Pretraining at Small Scale**.

## Setup

```bash
pip install -r requirements.txt
```

## Train

```bash
python train.py --config configs/tinyclip.yaml
```

## Evaluate

```bash
python evaluate.py --checkpoint runs/last --config configs/tinyclip.yaml
```

## Data

Download ImageNet-1k yourself and point `data.root` in `configs/tinyclip.yaml` at it.
