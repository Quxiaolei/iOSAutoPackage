# iOSAutoPackage

## 使用方法

在工程根目录下运行下方命令即可:

* python脚本

```python
python autobuild.py -w XXX.xcworkspace -s XXX -m "1.测试description
2.测试描述2
3.测试描述3"
# -w:表示workspace文件
# -p:表示project文件
# -s:表示打包对应的scheme
# -m:表示打包更新描述信息,可不填
```

* shell脚本

```sh
sh autobuild.sh "1.测试description
2.测试描述2
3.测试描述3"
```

手动配置流程:

1. 使用脚本时,需要首先指定打包类型`Release`或`Debug`
2. 并在`exportOptions.plist`指定打包方法(常见有`app-store`,`ad-hoc`,`enterprise`,`package`,`development`)
3. 指定ipa包输出文件夹(默认为`~/Desktop/AutoPackage/`)
4. 设定蒲公英平台的`USER_KEY`,`API_KEY`和接受发送邮件的邮箱
5. 最后在工程文件夹下运行对应命令即可

## 常见问题

出现错误:

```python
import requests
ImportError: No module named requests
```

使用`$ sudo pip install requests`或者`sudo easy_install -U requests`即可解决.

## 参考资料

* [iOS自动打包并发布脚本](https://github.com/carya/Util)
* [iOS项目自动打包脚本](https://github.com/hades0918/ipapy)
* [关于持续集成打包平台的Jenkins配置和构建脚本实现细节](http://debugtalk.com/post/iOS-Android-Packing-with-Jenkins-details/)
* [iOS：使用jenkins实现xcode自动打包](http://blog.csdn.net/u014641783/article/details/50866196)
* [iOS Shell脚本自动构建打包、发布、部署jenkins](https://www.jianshu.com/p/ad4a9c40ae59)
* [iOS--脚本配置Xcode Project（打包）](http://blog.csdn.net/chsadin/article/details/61192923)