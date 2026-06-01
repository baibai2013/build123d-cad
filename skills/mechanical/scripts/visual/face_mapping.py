#!/usr/bin/env python3
"""Load and validate part_face_mapping.yaml.
加载并校验 part_face_mapping.yaml。

Why: different parts orient "FRONT" along different world axes. Keeping
the mapping in a per-part YAML lets multi_view_screenshot.py and
skybox_unfold.py emit semantically labelled views without hard-coding.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml


VALID_CAMERAS = {"FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM", "ISO"}
VALID_SEMANTICS = {"FRONT", "BACK", "LEFT", "RIGHT", "TOP", "BOTTOM"}

DEFAULT_MAPPING: Dict[str, str] = {v: v for v in VALID_SEMANTICS}


@dataclass
class FaceMapping:
    mapping: Dict[str, str]
    is_default: bool
    source_path: Optional[Path]

    def semantic_to_camera(self, semantic_view: str) -> str:
        if semantic_view not in self.mapping:
            raise KeyError(
                f"unknown semantic view {semantic_view!r}; valid: {sorted(VALID_SEMANTICS)}"
            )
        return self.mapping[semantic_view]


def load_face_mapping(path: Optional[Path]) -> FaceMapping:
    if path is None:
        return FaceMapping(mapping=dict(DEFAULT_MAPPING), is_default=True, source_path=None)
    data = yaml.safe_load(path.read_text()) or {}
    raw = data.get("face_mapping", {}) or {}
    mapping = dict(DEFAULT_MAPPING)
    for sem, cam in raw.items():
        if sem not in VALID_SEMANTICS:
            raise ValueError(f"unknown semantic view {sem!r} in {path}")
        if cam not in VALID_CAMERAS:
            raise ValueError(f"invalid camera target {cam!r} for {sem} in {path}")
        mapping[sem] = cam
    return FaceMapping(mapping=mapping, is_default=False, source_path=path)
