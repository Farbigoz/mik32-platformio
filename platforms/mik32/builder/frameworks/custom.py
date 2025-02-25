# Copyright 2020-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Custom 

get from

https://github.com/espressif/esp-idf
"""

import copy
import json
import subprocess
import sys
import os
import ctypes

import click
import semantic_version

from SCons.Script import (
    ARGUMENTS,
    COMMAND_LINE_TARGETS,
    DefaultEnvironment,
)

from platformio import fs
from platformio.proc import exec_command
from platformio.util import get_systype
from platformio.builder.tools.piolib import ProjectAsLibBuilder
from platformio.package.version import get_original_version, pepver_to_semver

env = DefaultEnvironment()
# env.SConscript("_embed_files.py", exports="env")

env.SConscript("_bare.py")

platform = env.PioPlatform()
board = env.BoardConfig()

TOOLCHAIN_DIR = platform.get_package_dir(
    "toolchain-mik32"
)

assert os.path.isdir(TOOLCHAIN_DIR)

BUILD_DIR = env.subst("$BUILD_DIR")
PROJECT_DIR = env.subst("$PROJECT_DIR")
PROJECT_SRC_DIR = env.subst("$PROJECT_SRC_DIR")
CMAKE_API_REPLY_PATH = os.path.join(".cmake", "api", "v1", "reply")

SHARED_DIR = os.path.join(TOOLCHAIN_DIR, "shared")
LDSCRIPTS_DIR = os.path.join(SHARED_DIR, "ldscripts")
RUNTIME_DIR = os.path.join(SHARED_DIR, "runtime")

def log(msg, should_append=False):
    LOG_FILE = os.path.join(PROJECT_DIR, "log.log")

    with open(LOG_FILE, 'a' if should_append else 'w') as f:
        f.write(msg + '\n')


if not os.path.isfile(os.path.join(RUNTIME_DIR, 'build', 'core_startup.o')):
    env.BuildSources(
        os.path.join(RUNTIME_DIR, 'build'),
        src_dir=RUNTIME_DIR
    )

if not os.path.isfile(os.path.join(RUNTIME_DIR, 'build', 'core_irq.o')):
    env.BuildSources(
        os.path.join(RUNTIME_DIR, 'build'),
        src_dir=RUNTIME_DIR
    )


board_config = board.manifest.get("debug", {})
if "tools" not in board_config:
    board_config["tools"] = {}

ldscript = board_config.get("ldscript", "eeprom")
ldscript_ld = os.path.join(LDSCRIPTS_DIR, ldscript + '.ld')
if not os.path.isfile(ldscript_ld):
    print('ERROR! No ld script file found for name', ldscript)


env.AppendUnique(
    CPPPATH=[
        '-v',
        "$PROJECT_SRC_DIR",
        os.path.join(SHARED_DIR, "include"),
        os.path.join(SHARED_DIR, "periphery"),
    ],
    LINKFLAGS=[
        "-nostartfiles",
        "-T", ldscript_ld,
        os.path.join(RUNTIME_DIR, 'build', 'core_startup.o'),
        os.path.join(RUNTIME_DIR, 'build', 'core_irq.o'),
        '-v',
        
        "-ffreestanding",
        "-nostdlib"
    ],
    LIBS=[
        
    ]
)

