# iOSAutoPackage

## 使用方法

在工程根目录下运行下方命令即可:

```python
python autobuild.py -w XXX.xcworkspace -s XXX -m "1.测试description
2.测试描述2
3.测试描述3"
# -w:表示workspace文件
# -p:表示project文件
# -s:表示打包对应的scheme
# -m:表示打包更新描述信息,可不填
```

手动配置流程:

1. 使用脚本时,需要首先指定打包类型`Release`或`Debug`
2. 并在`exportOptions.plist`指定打包方法(常见有`app-store`,`ad-hoc`,`enterprise`,`package`,`development`)
3. 指定ipa包输出文件夹(默认为`~/Desktop/AutoPackage/`)
4. 设定蒲公英平台的`USER_KEY`和`API_KEY`
5. 最后在工程文件夹下运行对应命令即可

## 常见问题

出现错误:

```python
import requests
ImportError: No module named requests
```

使用`$ sudo pip install requests`或者`sudo easy_install -U requests`即可解决.