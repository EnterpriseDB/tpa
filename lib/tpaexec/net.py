#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.
"""IP network operations."""


from argparse import ArgumentParser
from ipaddress import IPv4Network, ip_network
from random import shuffle
from typing import Iterator, MutableSequence, List

DEFAULT_NETWORK_CIDR = "10.33.0.0/16"
DEFAULT_SUBNET_PREFIX_LENGTH = 28

TypeNets = Iterator[IPv4Network]
TypeSubnets = MutableSequence[IPv4Network]


class Network:
    """Interface for calculating and determining super-net size."""

    def __init__(self, cidr: str, size: int = DEFAULT_SUBNET_PREFIX_LENGTH) -> None:
        """
        Configure a network using CIDR notation capable of creating subnets with configured prefix length.

        For example, if a CIDR of 10.0.0.0/16 is given and a size of 28 then the bits 16-28 will denote subnets.
            10.0.0.0/16 = 10.0.0.0/28 -> 10.0.255.240/28

        Args:
            cidr: Network IP range using CIDR notation.
            size: Network prefix length to denote what address range will be used for subnetting.

        """
        self.net = IPv4Network(cidr)
        self.subnet_prefix = size
        self.prefix = self.net.prefixlen
        self._subnets = None

    def subnets(self, limit=1):
        """Generate subnets for use with TPAexec."""
        return Subnets(self.net.with_prefixlen, limit, self.subnet_prefix)

    def overlaps(self, other):
        """
        Compare network range of network with other.

        Returns:
            bool: True if network range addresses overlap.

        """
        return self.net.overlaps(other)

    def __repr__(self):
        """String representation of class object."""
        return f"{self.__class__.__name__}({self.net.with_prefixlen})"

    def __str__(self):
        """String representation of class data."""
        return self.net.with_prefixlen


class Subnets:
    """Interface for defining the IP address ranges and selecting subnets for a given network."""

    MIN_PREFIX = 23
    MAX_PREFIX = 29

    def __init__(self, cidr: str, limit: int = 1, new_prefix: int = 28) -> None:
        """
        Supply initial values for calculating number of subnets and their sizes for the given network.

        Args:
            limit: Limit number of subnets
            cidr: Initial network range using CIDR notation
            new_prefix: Prefix of new subnets

        """
        self.cidr = ip_network(cidr)
        self.limit = limit
        self.new_prefix = new_prefix
        self._ranges = None

    def validate(self):
        """Validate the prefix length restrictions."""
        if not (self.MAX_PREFIX > self.new_prefix > self.MIN_PREFIX):
            raise ValueError(
                f"prefix length for subnets must be between "
                f"{self.MIN_PREFIX}-{self.MAX_PREFIX}: {self.new_prefix}"
            )

    @property
    def ranges(self) -> TypeSubnets:
        """Calculate and store subnet ranges for the defined IP network."""
        if self._ranges is None:
            self._ranges = list(self.__get_subnet_ranges(self.cidr))
        return self._ranges

    @ranges.setter
    def ranges(self, value: TypeSubnets) -> None:
        """Setter method for ranges property."""
        self._ranges = value

    def __get_subnet_ranges(self, net: IPv4Network) -> TypeNets:
        """Return a generator object with the subnets for the defined network according to new_prefix length."""
        self.validate()
        return net.subnets(new_prefix=self.new_prefix)

    def exclude(self, excludes: Iterator[str]) -> None:
        """Remove any subnet in stored ranges which overlaps with any range in an excludes list of CIDR addresses."""
        self.ranges = list(
            r
            for r in self.ranges
            if not any(map(r.overlaps, map(ip_network, excludes)))
        )

    def shuffle(self) -> None:
        """Randomise the order of the stored subnets ranges."""
        shuffle(self.ranges)

    def slice(self, num: int = None) -> List:
        """Return a list with the first num nets in nets or stored subnet ranges."""
        return list(self.ranges[: num or self.limit])

    def __repr__(self) -> str:
        """String representation of class object."""
        return f"{self.__class__.__name__}({self.cidr}): {self.__str__()}"

    def __str__(self) -> str:
        """String representation of class data."""
        return " ".join(str(subnet) for subnet in self.slice())

    def __iter__(self) -> Iterator:
        """Make this object behave like an iterator."""
        return iter(self.slice())

    def __getitem__(self, item):
        """Support lookup of value by the get index or key method."""
        return self.slice()[item]


def main():  # pragma: no cover
    """Function is executed when this module is ran as a command line script."""
    parser = ArgumentParser()
    parser.add_argument("num", type=int)
    parser.add_argument("net", nargs="?", default="10.33.0.0/16")
    parser.add_argument("--new-prefix", default=28, type=int)
    parser.add_argument("--exclude", action="append", dest="excludes", default=[])
    parser.add_argument("--shuffle", action="store_true")
    args = parser.parse_args()

    subnets = Subnets(cidr=args.net, limit=args.num, new_prefix=int(args.new_prefix))
    subnets.exclude(args.excludes)
    if args.shuffle:
        subnets.shuffle()
    print(subnets)


if __name__ == "__main__":  # pragma: no cover
    main()
