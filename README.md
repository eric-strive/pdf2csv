
## 前言

本项目实现了一个 PDF 格式行程单的解析，可以将网约车平台导出的 PDF 格式电子行程单，转换成 CSV 或者 Excel 格式。目前支持的平台有：
 * 滴滴出行
 * 高德地图
 * 首汽约车
 * 美团打车

## 使用方法

### 环境依赖的初始化
```shell
# 安装包
pip install -r requirements.pip

# 初始化配置
sh init.sh dev
dev 开发
test 测试
pro 正式
```
### gunicorn配置文件修改
```shell
dev.conf 开发环境
pro.conf 正式环境
test.conf 测试环境
gunicorn.conf 正式使用数据

Configuration instructions
# 并行工作线程数
workers = 4
# 监听内网端口5000【按需要更改】
bind = '127.0.0.1:5001'
# 设置守护进程【关闭连接时，程序仍在运行】
daemon = False
# 设置超时时间120s，默认为30s。按自己的需求进行设置
timeout = 120
```
### flask配置文件修改
```shell
dev.cfg 开发环境
pro.cfg 正式环境
test.cfg 测试环境
settings.cfg 正式使用数据
```

### nginx配置

```shell
  server {
    listen 80;
    server_name 127.0.0.1; # 实际外界访问的地址
    location / {
        proxy_pass        http://127.0.0.1:5001/; # 对应不同环境访问的地址
        proxy_redirect     off;

        proxy_set_header   Host             $http_host;
        proxy_set_header   X-Real-IP        $remote_addr;
        proxy_set_header   X-Forwarded-For  $proxy_add_x_forwarded_for;

    }
}

```
### nginx重新加载配置
```shell
   nginx -s reload
```

### 项目启动
```shell
 gunicorn app:app -c ./gunicorn/gunicorn.conf
```
### 项目测试
```shell
python client.py
```
### 访问
```
根据设置环境的配置文件访问相应地址 http://127.0.0.1/itinerary-parser
127.0.0.1 是nginx提供外界服务的地址
```
## 开发说明

开发版本要求：

 * Python 3.7.6
 * **Java 1.8.0_121**（tabula-py 是对 tabula-java 的封装，所以需要依赖 Java）
 * nignx