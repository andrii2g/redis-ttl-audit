from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


MAX_EXAMPLES_PER_GROUP = 3


class TtlStatus(str, Enum):
    EXPIRES = "EXPIRES"
    NONE = "NONE"
    DISAPPEARED = "DISAPPEARED"


@dataclass
class GroupStats:
    group: str
    total_count: int = 0
    expiring_count: int = 0
    persistent_count: int = 0
    disappeared_count: int = 0
    min_ttl: int | None = None
    max_ttl: int | None = None
    ttl_sum: int = 0
    ttl_count: int = 0
    examples_persistent: list[str] = field(default_factory=list)
    examples_expiring: list[str] = field(default_factory=list)

    @property
    def avg_ttl(self) -> float | None:
        if self.ttl_count == 0:
            return None
        return self.ttl_sum / self.ttl_count

    def add_expiring_key(self, key: str, ttl: int) -> None:
        self.total_count += 1
        self.expiring_count += 1
        self.ttl_sum += ttl
        self.ttl_count += 1
        self.min_ttl = ttl if self.min_ttl is None else min(self.min_ttl, ttl)
        self.max_ttl = ttl if self.max_ttl is None else max(self.max_ttl, ttl)
        if len(self.examples_expiring) < MAX_EXAMPLES_PER_GROUP:
            self.examples_expiring.append(key)

    def add_persistent_key(self, key: str) -> None:
        self.total_count += 1
        self.persistent_count += 1
        if len(self.examples_persistent) < MAX_EXAMPLES_PER_GROUP:
            self.examples_persistent.append(key)

    def add_disappeared_key(self) -> None:
        self.total_count += 1
        self.disappeared_count += 1


@dataclass
class AuditSummary:
    scanned_keys: int = 0
    expiring_keys: int = 0
    persistent_keys: int = 0
    disappeared_keys: int = 0
    groups: dict[str, GroupStats] = field(default_factory=dict)

    def get_group(self, group: str) -> GroupStats:
        if group not in self.groups:
            self.groups[group] = GroupStats(group=group)
        return self.groups[group]

