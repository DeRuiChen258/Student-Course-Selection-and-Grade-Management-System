#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! ls lib/*.jar >/dev/null 2>&1; then
    echo "[失败] lib/ 下没有 JDBC 驱动，先按 lib/README.md 下载" >&2
    exit 2
fi

mkdir -p out/classes out/test-classes
find src/main/java -name '*.java' | sort > out/sources.txt
javac --release 17 -encoding UTF-8 -cp "lib/*" -d out/classes @out/sources.txt

find src/test/java -name '*.java' | sort > out/test-sources.txt
javac --release 17 -encoding UTF-8 -cp "out/classes:lib/*" -d out/test-classes @out/test-sources.txt

java -Dfile.encoding=UTF-8 -cp "out/classes:out/test-classes:lib/*" edu.scut.db.tests.TestRunner "$@"
