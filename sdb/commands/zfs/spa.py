#
# Copyright 2019 Delphix
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# pylint: disable=missing-docstring

import argparse
from typing import Iterable, List, Optional

import drgn
import sdb
from sdb.commands.spl.avl import Avl
from sdb.commands.zfs.vdev import Vdev
from sdb.commands.zfs.histograms import ZFSHistogram


class Spa(sdb.Locator, sdb.PrettyPrinter):
    names = ["spa"]
    input_type = "spa_t *"
    output_type = "spa_t *"

    @classmethod
    def _init_parser(cls, name: str) -> argparse.ArgumentParser:
        parser = super()._init_parser(name)
        parser.add_argument("-v",
                            "--vdevs",
                            action="store_true",
                            help="vdevs flag")
        parser.add_argument("-m",
                            "--metaslab",
                            action="store_true",
                            help="metaslab flag")
        parser.add_argument("-H",
                            "--histogram",
                            action="store_true",
                            help="histogram flag")
        parser.add_argument("-w",
                            "--weight",
                            action="store_true",
                            help="weight flag")
        parser.add_argument("poolnames", nargs="*")
        return parser

    def __init__(self,
                 args: Optional[List[str]] = None,
                 name: str = "_") -> None:
        super().__init__(args, name)
        self.arg_list: List[str] = []
        if self.args.metaslab:
            self.arg_list.append("-m")
        if self.args.histogram:
            self.arg_list.append("-H")
        if self.args.weight:
            self.arg_list.append("-w")

    def pretty_print(self, objs: Iterable[drgn.Object]) -> None:
        print(f"{'ADDR':18} NAME")
        print(f"{('-' * 60)}")
        for spa in objs:
            spa_name = spa.spa_name.string_().decode("utf-8")
            print(f"{hex(spa):18} {spa_name}")
            if self.args.histogram:
                ZFSHistogram.print_histogram(spa.spa_normal_class.mc_histogram,
                                             0, 5)

            if self.args.vdevs or self.args.metaslab:
                vdevs = sdb.execute_pipeline([spa], [Vdev()])
                Vdev(self.arg_list).print_indented(vdevs, 5)

    def no_input(self) -> drgn.Object:
        spas = sdb.execute_pipeline(
            [sdb.get_object("spa_namespace_avl").address_of_()],
            [Avl(), sdb.Cast(["spa_t *"])],
        )
        for spa in spas:
            if (self.args.poolnames and spa.spa_name.string_().decode("utf-8")
                    not in self.args.poolnames):
                continue
            yield spa
