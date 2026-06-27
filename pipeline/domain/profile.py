"""Backward-compatible Profile facade — use pipeline.domain.models.profile.Profile."""
from pipeline.domain.models.profile import Profile
from pipeline.domain.models.profile import Profile as CanonicalProfile


def from_customer(customer):
    from pipeline.domain.models.profile import Profile as P
    return P.from_customer(customer)


__all__ = ["CanonicalProfile", "Profile", "from_customer"]
