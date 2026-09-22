# lib/ 第三方依赖说明

## 唯一依赖

| 项目 | 值 |
| --- | --- |
| 文件名 | `mysql-connector-j-9.1.0.jar` |
| 版本 | 9.1.0（MySQL 官方 JDBC 驱动） |
| 放置路径 | `lib/mysql-connector-j-9.1.0.jar` |
| 下载来源（二选一） | ① Maven Central：`https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.1.0/mysql-connector-j-9.1.0.jar`<br>② MySQL 官网 Connector/J 下载页 |
| 校验命令 | `sha256sum lib/mysql-connector-j-9.1.0.jar` |
| 期望 sha256 | `8776e2ebc46072c9a47ea59d98298c4273bd9f16a7b26b5dfa4744535aa26c62` |
| 文件大小 | 2597591 字节 |

## 下载命令

```bash
curl -L -o lib/mysql-connector-j-9.1.0.jar \
  https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/9.1.0/mysql-connector-j-9.1.0.jar
sha256sum lib/mysql-connector-j-9.1.0.jar
```

## 为什么 jar 不入版本库

`*.jar` 已被 `.gitignore` 忽略。驱动属于第三方二进制产物，体积大且可由上述命令一条指令复原；
提交源码时只保留本说明文件，评分人按本文档下载即可，下载后 `scripts/build.sh` 会自动带上 `lib/*` 作为
classpath。

## 校验方式

`scripts/build.sh` 在编译前检查 `lib/` 下是否存在 `*.jar`：不存在时退出码为 2 并打印上面的下载命令，
不尝试自动联网下载（避免在离线环境长时间等待）。

