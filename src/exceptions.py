# src/exceptions.py
"""Project-specific exceptions. Failures are raised, never signalled with None."""
from __future__ import annotations


class ProjectError(Exception):
    """Base class for all errors raised by this project."""


class ProfileLoadError(ProjectError):
    """The raw profiles file is missing, unreadable or has the wrong shape."""


class ProfileValidationError(ProjectError):
    """A single profile is incomplete or contains invalid values."""


class AnalysisError(ProjectError):
    """The analysis cannot run on the given data (e.g. too few profiles)."""
