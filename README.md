# iteye-migration
将自己iteye上的博客导出

## 使用方法
在migration.py里面更新iteye的用户名和密码，进入migration.py所在目录，并执行以下命令
```shell
$ python3 migration.py
```
执行命令以后将会在当前目录下生成backup文件夹,文件以json文件存储，或者在migration.py里面打开写入db,编写合适自己的sql
