import requests

# https://my-test-server.oss-cn-shanghai.aliyuncs.com/avatars/2020-03-15/5e6dc988b990c252的副本.pdf
# http://127.0.0.1:5001/trip
pdf_file_path = input("请输入pdf文件地址：")
request_url = input("请输入接口请求地址：")
trip_data = {'pdf_file_path': pdf_file_path}
r = requests.post(request_url, data=trip_data)
print(r.text)
