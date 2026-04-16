"""
Small toolkit for building generators over datetime ranges.

:copyright:
    2026, Conor A. Bacon.
:license:
    GNU General Public License, Version 3
    (https://www.gnu.org/licenses/gpl-3.0.html)

"""

from __future__ import annotations

from collections.abc import Generator, Iterable
from dataclasses import dataclass
from datetime import datetime as dt, time, timedelta as td


@dataclass(frozen=True)
class TimeChunk:
    start: dt
    end: dt
    index: int
    total: int | None = None

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def duration_seconds(self) -> float:
        return self.duration.total_seconds()


def fmt(datetime: dt) -> str:
    return datetime.isoformat(timespec="seconds")


def merge_intervals(intervals: Iterable[tuple[dt, dt]]) -> list[tuple[dt, dt]]:
    """
    Merge overlapping and contiguous time intervals.

    Parameters
    ----------
    intervals:
        Iterable of (start, end) datetime tuples. Intervals where start >= end are
        ignored.

    Returns
    -------
    merged:
        Sorted list of non-overlapping intervals covering the same time spans as the
        input.

    """

    merged = []
    for start, end in sorted(intervals, key=lambda x: x[0]):
        if start >= end:
            continue

        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))

    return merged


def subtract_intervals(
    start: dt, end: dt, covered: Iterable[tuple[dt, dt]]
) -> list[tuple[dt, dt]]:
    """
    Subtract covered intervals from a target interval.

    Parameters
    ----------
    start, end:
        Start and end of the target interval.
    covered:
        Iterable of (start, end) intervals representing time ranges to exclude from the
        target interval.

    Returns
    -------
    remaining:
        List of remaining (uncovered) intervals after subtraction. The result is sorted
        and non-overlapping.

    """

    if start >= end:
        return []

    remaining = [(start, end)]
    for c0, c1 in merge_intervals(covered):
        next_remaining = []
        for r0, r1 in remaining:
            if c1 <= r0 or c0 >= r1:
                next_remaining.append((r0, r1))
                continue

            if c0 > r0:
                next_remaining.append((r0, c0))
            if c1 < r1:
                next_remaining.append((c1, r1))

        remaining = next_remaining

        if not remaining:
            break

    return remaining


def ceil_time(t: dt, step: td, anchor: dt | None = None) -> dt:
    """
    Round a datetime up to the next multiple of a fixed step.

    Parameters
    ----------
    t:
        Input datetime to round.
    step:
        Step size as a timedelta. Must be positive.
    anchor:
        Reference datetime defining the alignment grid. If None, defaults to midnight
        (00:00:00) of `t`'s date, preserving timezone information.

    Returns
    -------
    t:
        The smallest datetime >= t that lies on the step grid defined by
        (anchor + n * step).

    """

    if step <= td(0):
        raise ValueError("step must be positive")

    if anchor is None:
        anchor = dt.combine(t.date(), time.min, tzinfo=t.tzinfo)

    offset = t - anchor
    remainder = offset % step
    if remainder == td(0):
        return t

    return t + (step - remainder)


def iter_time_chunks(
    starttime: dt,
    endtime: dt,
    *,
    chunk: td | None = None,
    chunk_days: int | None = None,
    align: bool = False,
    alignment_anchor: dt | None = None,
    skip_intervals: Iterable[tuple[dt, dt]] | None = None,
    include_total: bool = True,
) -> Generator[TimeChunk, None, None]:
    """
    Yield time chunks between starttime and endtime.

    Parameters
    ----------
    starttime:
        Timestamp of start of timespan requested.
    endtime:
        Timestamp of end of timespan requested.
    chunk:
        Chunk size as timedelta.
    chunk_days:
        Chunk size in days. Exactly one of chunk_seconds/chunk_days must be set.
    align:
        If True, align chunk boundaries to the chunk grid.
    alignment_anchor:
        Anchor used for alignment. Defaults to midnight of starttime's day.
    skip_intervals:
        Intervals to exclude from yielding, e.g., already-processed ranges.
    include_total:
        If True, populate the `total` field in yielded chunks.

    Yields
    ------
    TimeChunk

    """

    if (chunk is None) == (chunk_days is None):
        raise ValueError("Set exactly one of chunk or chunk_days")

    if chunk_days is not None:
        chunk = td(days=chunk_days)

    assert chunk is not None

    if chunk <= td(0):
        raise ValueError("Chunk size must be positive")

    if starttime >= endtime:
        return

    windows = [(starttime, endtime)]
    if skip_intervals:
        windows = subtract_intervals(starttime, endtime, skip_intervals)

    prepared = []
    for win_start, win_end in windows:
        current = win_start

        if align:
            current = ceil_time(current, chunk, alignment_anchor)
            if current > win_start:
                prepared.append((win_start, min(current, win_end)))

        while current < win_end:
            chunk_end = min(current + chunk, win_end)
            prepared.append((current, chunk_end))
            current = chunk_end

    total = len(prepared) if include_total else None

    for index, (chunk_start, chunk_end) in enumerate(prepared, start=1):
        yield TimeChunk(
            start=chunk_start,
            end=chunk_end,
            index=index,
            total=total,
        )
