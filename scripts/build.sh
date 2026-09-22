#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

command -v java >/dev/null || { echo "[失败] 未找到 java，请安装 JDK 17 或更高版本" >&2; exit 2; }
command -v javac >/dev/null || { echo "[失败] 未找到 javac，请安装 JDK 17 或更高版本" >&2; exit 2; }

if ! ls lib/*.jar >/dev/null 2>&1; then
    echo "[失败] lib/ 下没有 JDBC 驱动，无法编译与运行" >&2
    echo "       下载命令（详见 lib/README.md）：" >&2
    echo "       curl -L -o lib/mysql-connector-j-9.1.0.jar \\" >&2
    echo "         https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.1.0/mysql-connector-j-9.1.0.jar" >&2
    exit 2
fi

mkdir -p out/classes
find src/main/java -name '*.java' | sort > out/sources.txt
echo "源文件数量: $(wc -l < out/sources.txt)"

javac --release 17 -encoding UTF-8 -cp "lib/*" -d out/classes @out/sources.txt

CLASS_COUNT="$(find out/classes -name '*.class' | wc -l)"
echo "编译完成: out/classes 下 $CLASS_COUNT 个 class 文件"
