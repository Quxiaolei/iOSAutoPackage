#!/bin/sh

#  Script.sh
#  
#
#  Created by Apple on 2018/2/24.
#  Copyright © 2018年 Apple. All rights reserved.
# 工程绝对路径
# cd $1
project_path=$(pwd)
# build文件夹路径
build_path=${project_path}/build

# 编译类型
CONFIGURATION="Release"
BuidType="enterprise"
Scheme="XXX"
USER_KEY="XXX"
API_KEY="XXX"
ToEmail="XXX"

# 工程配置文件路径
project_name=$(ls | grep xcodeproj | awk -F.xcodeproj '{print $1}')
project_infoplist_path=${project_path}/${project_name}/${Scheme}.plist
# 取版本号
bundleShortVersion=$(/usr/libexec/PlistBuddy -c "print CFBundleShortVersionString" ${project_infoplist_path})
# 取build值
bundleVersion=$(/usr/libexec/PlistBuddy -c "print CFBundleVersion" ${project_infoplist_path})
# 取bundle Identifier前缀
bundlePrefix=$(/usr/libexec/PlistBuddy -c "print CFBundleIdentifier" `find . -name "*InHouse.plist"` | awk -F$ '{print $1}')

# echo ${project_infoplist_path} ${bundleShortVersion} ${bundleVersion} ${bundlePrefix}

cd $project_path

# 安装pod
pod install --verbose --no-repo-update

# 清理工程
echo clean workspace ...
xcodebuild clean -workspace ${project_path}/${project_name}.xcworkspace -scheme ${Scheme} -configuration ${CONFIGURATION} || exit
echo clean workspace success
# 去掉xcode源码末尾的空格
# find . -name "*.[hm]" | xargs sed -Ee 's/ +$//g' -i ""

# 修改版本信息
timestamp=$(date +%Y-%m-%d_%H-%M-%S)
newBundleVersion=$(date +%m%d_%H%M%S)
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion ${newBundleVersion}" ${project_infoplist_path}

# 编译工程
xcodebuild -workspace ${project_path}/${project_name}.xcworkspace -scheme ${Scheme} -configuration ${CONFIGURATION} \
archive -archivePath ${build_path}/${Scheme} -destination generic/platform=iOS
if [ -e ${build_path}/${Scheme}.xcarchive ]
then
echo archive success
else
exit
fi

# 打包
xcodebuild -exportArchive -archivePath ${build_path}/${Scheme}.xcarchive \
-exportPath ~/Desktop/AutoPackage/${Scheme}${timestamp} -exportOptionsPlist ${project_path}/exportOptions.plist
if [ -e ~/Desktop/AutoPackage/${Scheme}${timestamp}/${Scheme}.ipa ]
then
echo ipa create success
else
exit
fi

# 删除bulid目录
echo clean start ...
if  [ -d ${build_path} ];then
rm -rf ${build_path}
echo clean build_path success.
fi

# 判断jq库是否存在
# brew install jq
# echo $?
# jqVersion=$(jq --version)
# if [ -z ${jqVersion} ]
# then
# brew install jq
# else
# echo ${jqVersion}
# exit
# fi

# 上传蒲公英
returnMessage=$(curl -F "file=@~/Desktop/AutoPackage/${Scheme}${timestamp}/${Scheme}.ipa" \
-F "uKey=${USER_KEY}" -F "_api_key=${API_KEY}" -F "updateDescription=$1" https://qiniu-storage.pgyer.com/apiv1/app/upload)

parse_json(){
echo "${3//\"/}" | sed "s/.*$4:\([^,}]*\).*/\1/"
}
value=$(parse_json ${returnMessage} "appQRCodeURL")
echo appQRCodeURL:${value}

if [ -z ${value} ]
then
echo 上传错误,请稍后重试
exit
fi

# 发送邮件通知
echo "iOS测试包_${bundleShortVersion}(${newBundleVersion})
更新说明：
$1

具体信息请点击:XXX

NOTICE：本邮件由系统自动发送，请勿回复。" | mail -s "[iOS Test]The new iOS TestPackage had been uploaded,pls checkout" ${ToEmail}

exit 0