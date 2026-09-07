"""Ortak faker / seed yardımcıları."""

from __future__ import annotations

import random

from faker import Faker


def make_faker(seed: int | None = None) -> Faker:
    """tr_TR öncelikli, yedekli Faker döndürür."""
    fake = Faker(["tr_TR", "en_US"])
    if seed is not None:
        Faker.seed(seed)
        random.seed(seed)
        fake.seed_instance(seed)
    return fake
