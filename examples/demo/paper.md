# TinyCLIP: Efficient Contrastive Pretraining at Small Scale

## Abstract

We study contrastive image-text pretraining under a tight compute budget. TinyCLIP
distils the geometry of a large teacher into a 12M-parameter student while keeping
the training recipe simple: no extra data, no architectural tricks beyond width and
depth scaling.

## 3 Method

TinyCLIP keeps the standard CLIP objective and replaces the visual tower with a
6-layer transformer of width 256. Text is encoded by a frozen 12-layer BERT-base.
We train for 30 epochs with AdamW and a batch size of 256.

## 4 Experiments

### 4.1 Main results

All models are evaluated on the ImageNet validation split, following the standard
protocol of reporting top-1 accuracy after fine-tuning a linear head for 10 epochs.

| Method | ImageNet Top-1 | Zero-shot ImageNet | Params |
|---|---|---|---|
| CLIP-B/32 | 68.3 | 43.3 | 88M |
| TinyCLIP (ours) | 72.3 | 45.1 | 12M |

### 4.2 Detection transfer

We transfer the frozen backbone to COCO detection with a standard Mask R-CNN head.
On the detection task we reach 0.41 mAP on COCO.

## 5 Limitations

The student inherits the teacher's bias, and our evaluation covers a single data
distribution. Detection transfer was measured on one split only.
