# Esearch
一个基于 MySQL 和 MeiliSearch 的轻量级数据库架构，支持全文检索和向量检索，有效实现对MySQL模糊查询等功能的加速

我们编写了两个应用Demo，以验证此框架的有效性：
## 电影查询
   支持输入错误纠正，模糊检索，实时搜索
   QPS性能2000+
![image](https://github.com/user-attachments/assets/a3b354b5-7170-49fc-b862-7a57baaf9d0b)

   
## LUA代码检索
   支持对 Lua 语言指令的全文检索和向量检索，有效实现精准及模糊查询功能
   此外，我们进一步开发了基于 Retrieval-Augmented Generation (RAG) 的 AI 代码自动补全功能，以提高服务端 Lua 开发的效率与准确性。
   QPS性能1000+
![图片1](https://github.com/user-attachments/assets/05645bc7-bd0b-4da6-a71f-7f2717d5b949)

# 流程图：

## MySQL和MeiliSearch的双数据库框架
![图片2](https://github.com/user-attachments/assets/6eed4afe-bff1-49b5-bd83-9e55e45d9d43)

## 基于 RAG（检索增强生成）的AI代码补全框架
![图片3](https://github.com/user-attachments/assets/7f78c3c1-7175-468e-8650-a61bbf4fc038)


# 使用教程：

## mysql
1. 开启binlog 
2. ip-bind=0.0.0.0
    GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY '密码' WITH GRANT OPTION;
    flush privileges;

## canal

安装：
https://github.com/alibaba/canal/wiki/QuickStart

可能遇到的坑：
1. 连接建立不成功
    MySQL未开启允许外部连接访问 https://blog.csdn.net/sinat_42338962/article/details/108832723
2. 连接成功但监听不到数据
    MySQL未开启binlog服务 https://blog.csdn.net/u011110301/article/details/106854899
    MySQL的binlog未初始化 https://www.cnblogs.com/ykpkris/articles/13209013.html

## nginx

修改配置：

utils\nginx\conf\nginx.conf
1. 检查配置是否有语法错误（在utils\nginx目录下执行）：
    nginx -t
2. 动态刷新：
    nginx -s reload
