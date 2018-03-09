#!/usr/bin/env python
# coding: utf-8

# python autobuild.py -p youproject.xcodeproj -s schemename -m description
# python autobuild.py -w youproject.xcworkspace -s schemename -m description

import argparse
import subprocess
import requests
import os, sys
import time

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.image import MIMEImage

# configuration for iOS build setting
# 会在桌面创建输出ipa文件的目录
CONFIGURATION = "Release"
# AutoPackage路径下
EXPORT_OPTIONS_PLIST = "AutoPackage/exportOptions.plist"
# 会在桌面创建输出ipa文件的目录
EXPORT_MAIN_DIRECTORY = "~/Desktop/AutoPackage/"

# configuration for pgyer
PGYER_UPLOAD_URL = "http://www.pgyer.com/apiv1/app/upload"
DOWNLOAD_BASE_URL = "http://www.pgyer.com"
# 填写对应key值
USER_KEY = ""
API_KEY = ""
# 设置从蒲公英下载应用时的密码
PYGER_PASSWORD = ""
# 蒲公英更新描述
PGYDESC = "Default update description"
# 应用内安装地址
QuicklyInstallURL = ""

# 邮件参数
# FIXME: YOUR_EMAIL
emailFromUser = "YOUR_EMAIL"
# 多个邮箱使用,分割
# FIXME: list of postUser
emailToUser = ["",""]
# FIXME: list of CCUser
accUser = ["",""]
# FIXME: YOUR_EMAIL_PASSWORD
emailPassword = "YOUR_PASSWORD"
emailHost = "smtp.exmail.qq.com"

# 临时变量
appBuildTime = ""

def cleanArchiveFile(archiveFile):
	cleanCmd = "rm -r %s" % (archiveFile)
	process = subprocess.Popen(cleanCmd, shell=True)
	process.wait()
	print("cleaned archiveFile: %s" % (archiveFile))


def parserUploadResult(jsonResult):
	resultCode = jsonResult['code']
	if resultCode == 0:
		downUrl = DOWNLOAD_BASE_URL + "/" + jsonResult['data']['appShortcutUrl']
		print("Upload Success")
		print("DownUrl is:" + downUrl)
		# 发送邮件
		sendEmail(jsonResult)
	else:
		print("Upload Fail!")
		print("Reason:" + jsonResult['message'])

# 修改邮箱格式为字符串
def formatForEmailUser(userList):
	if isinstance(userList,list) and len(userList) >0:
		if len(userList) == 1:
			return  userList[0]
		else:
			return ",".join(userList)
	elif isinstance(userList,str):
		return userList
	else:
		print("邮箱格式转换失败")
		exit(0)

# 发邮件给测试不带附件
def sendEmail(jsonResult):
	# guard
	if not emailFromUser.strip():
		print("emailFromUser或者emailToUser格式数据不对")
		exit(0)
	formatForEmailUser(emailToUser)
	downUrl = DOWNLOAD_BASE_URL +"/"+jsonResult['data']['appShortcutUrl']
	appQRCodeURL = jsonResult['data']['appQRCodeURL']
	appVersion = jsonResult['data']['appVersion']
	downUrl = DOWNLOAD_BASE_URL +"/"+jsonResult['data']['appShortcutUrl']
	appQRCodeURL = jsonResult['data']['appQRCodeURL']
	appVersion = jsonResult['data']['appVersion']
	appUpdateDescription = PGYDESC.replace("\n", "<br>")

	print("\nappVersion:%s,\nappBuildTime:%s,\nappQRCodeURL:%s,\ndownUrl:%s\ndes:%s\nappUpdateDescription:%s\n---end" % (
	appVersion, appBuildTime, appQRCodeURL, downUrl, PGYDESC, appUpdateDescription))

	# 邮件正文第三方内容
	msg = MIMEMultipart('related')
	msgtext = MIMEText("<font><h3>iOS测试包_%s(%s)</h3><p><h4>更新说明：</h4>%s</font>	\
    <p>安装二维码(最新包)：<br><img src='%s' /><br>具体版本信息详见：<a href='%s'>%s</a><p>应用内安装地址：<a href= '%s' >安装</a>(仅iOS 11以下机型可用)   \
    <font color = gray><h5 >NOTICE：本邮件由系统自动发送，请勿回复。</h5></font>" % (
	appVersion, appBuildTime, appUpdateDescription, appQRCodeURL, downUrl, downUrl, QuicklyInstallURL), "html", "utf-8")
	msg.attach(msgtext)

	msg['to'] = formatForEmailUser(emailToUser)
	msg['cc'] = formatForEmailUser(accUser)
	msg['from'] = emailFromUser
	msg['subject'] = '【iOS测试】新的iOS测试包已经上传，请注意查收'

	try:
		server = smtplib.SMTP()
		server.connect(emailHost)
		server.login(emailFromUser, emailPassword)
		server.sendmail(msg['from'], msg['to'], msg.as_string())
		server.quit()
		print('发送成功')
	except Exception as e:
		print(str(e))
	return


def uploadIpaToPgyer(ipaPath):
	print("uploadIpaToPgyer_ipaPath:" + ipaPath)
	if USER_KEY == "" or API_KEY == "":
		return
	ipaPath = os.path.expanduser(ipaPath)
	ipaPath = unicode(ipaPath, "utf-8")
	files = {'file': open(ipaPath, 'rb')}
	headers = {'enctype': 'multipart/form-data'}
	payload = {'uKey': USER_KEY, '_api_key': API_KEY, 'publishRange': '2', 'isPublishToPublic': '2',
	           'password': PYGER_PASSWORD, 'updateDescription': PGYDESC}
	print("update desc：%s" % (PGYDESC))
	print("uploading....")
	r = requests.post(PGYER_UPLOAD_URL, data=payload, files=files, headers=headers)
	if r.status_code == requests.codes.ok:
		result = r.json()
		parserUploadResult(result)
	else:
		print('HTTPError,Code:' + r.status_code)


# 创建输出ipa文件路径: ~/Desktop/AutoPackage/{scheme}{2018-2-27_14-05-10}
def buildExportDirectory(scheme):
	dateCmd = 'date "+%Y-%m-%d_%H-%M-%S"'
	process = subprocess.Popen(dateCmd, stdout=subprocess.PIPE, shell=True)
	(stdoutdata, stderrdata) = process.communicate()
	exportDirectory = "%s%s%s" % (EXPORT_MAIN_DIRECTORY, scheme, stdoutdata.strip())
	return exportDirectory


def buildArchivePath(tempName):
	process = subprocess.Popen("pwd", stdout=subprocess.PIPE)
	(stdoutdata, stderrdata) = process.communicate()
	archiveName = "%s.xcarchive" % (tempName)
	archivePath = "%s/%s" % (stdoutdata.strip(), archiveName)
	return archivePath


def getNewIpaPath(exportPath, scheme):
	ipaName = scheme + ".ipa"
	ipaPath = exportPath + "/" + ipaName
	print("getNewIpaPath_ipaPath: " + ipaPath)
	return ipaPath


def getIpaPath(exportPath):
	cmd = "ls %s" % (exportPath)
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
	(stdoutdata, stderrdata) = process.communicate()
	ipaName = stdoutdata.strip()
	ipaPath = exportPath + "/" + ipaName
	print("getIpaPath_ipaPath: " + ipaPath)
	return ipaPath


def exportArchive(scheme, archivePath):
	exportDirectory = buildExportDirectory(scheme)
	exportCmd = "xcodebuild -exportArchive -archivePath %s -exportPath %s -exportOptionsPlist %s" % (
	archivePath, exportDirectory, EXPORT_OPTIONS_PLIST)
	process = subprocess.Popen(exportCmd, shell=True)
	(stdoutdata, stderrdata) = process.communicate()

	signReturnCode = process.returncode
	if signReturnCode != 0:
		print("export %s failed" % (scheme))
		return ""
	else:
		return exportDirectory


def changeBundle_identifier(workspace, scheme):
	# 获取项目名称
	project_name = workspace.split(".")[0]
	# 获取版本号,内部版本号,bundleID
	info_plist_path = "%s/%s.plist" % (project_name, scheme)
	# 3.1.0
	bundle_version = commands.getstatusoutput("/usr/libexec/PlistBuddy -c 'Print CFBundleShortVersionString' %s" % (info_plist_path))[1]
	# $(PRODUCT_BUNDLE_IDENTIFIER)
	bundle_build_version = commands.getstatusoutput("/usr/libexec/PlistBuddy -c 'Print CFBundleIdentifier' %s" % (info_plist_path))[1]
	# 0226_142435
	bundle_identifier = commands.getstatusoutput("/usr/libexec/PlistBuddy -c 'Print CFBundleVersion' %s" % (info_plist_path))[1]

	# 更新build号
	timestamp = time.strftime("%m%d_%H%M%S")
	commands.getstatusoutput("/usr/libexec/PlistBuddy -c 'Set :CFBundleVersion %s' '%s'" % (timestamp, info_plist_path))

	global appBuildTime
	appBuildTime = timestamp
	print("project_name: %s,\nbundle_version:%s,\nbundle_build_version:%s,\nbundle_identifier:%s" % (
	project_name, bundle_version, bundle_build_version, bundle_identifier))


def buildProject(project, scheme):
	# 更新build号
	changeBundle_identifier(project, scheme)

	# clean 工程
	cleanCmd = "xcodebuild clean -workspace %s -scheme %s -configuration %s" % (
	workspace, scheme, CONFIGURATION)
	process = subprocess.Popen(cleanCmd, shell=True)
	process.wait()
	print("\n\033[32m************************* clean完成 ************************* \033[0m\n")

	archivePath = buildArchivePath(scheme)
	print("archivePath: " + archivePath)
	archiveCmd = 'xcodebuild -project %s -scheme %s -configuration %s archive -archivePath %s -destination generic/platform=iOS' % (
	project, scheme, CONFIGURATION, archivePath)
	process = subprocess.Popen(archiveCmd, shell=True)
	process.wait()

	archiveReturnCode = process.returncode
	if archiveReturnCode != 0:
		print("archive workspace %s failed" % (workspace))
		cleanArchiveFile(archivePath)
	else:
		exportDirectory = exportArchive(scheme, archivePath)
		cleanArchiveFile(archivePath)
		if exportDirectory != "":
			ipaPath = getIpaPath(exportDirectory)
			uploadIpaToPgyer(ipaPath)


def buildWorkspace(workspace, scheme):
	# 更新build号
	changeBundle_identifier(workspace, scheme)

	# 更新pod 仓库
	print("\n\033[32m************************* 开始pod ************************* \033[0m")
	podCmd = 'pod install --verbose --no-repo-update'
	process = subprocess.Popen(podCmd, shell=True)
	process.wait()
	print("\033[32m************************* pod完成 ************************* \033[0m\n")

	# clean 工程
	cleanCmd = "xcodebuild clean -workspace %s -scheme %s -configuration %s" % (
	workspace, scheme, CONFIGURATION)
	process = subprocess.Popen(cleanCmd, shell=True)
	process.wait()
	print("\n\033[32m************************* clean完成 ************************* \033[0m\n")

	archivePath = buildArchivePath(scheme)
	print("buildWorkspace_archivePath: " + archivePath)
	archiveCmd = 'xcodebuild -workspace %s -scheme %s -configuration %s archive -archivePath %s -destination generic/platform=iOS' % (
	workspace, scheme, CONFIGURATION, archivePath)
	process = subprocess.Popen(archiveCmd, shell=True)
	process.wait()

	archiveReturnCode = process.returncode
	if archiveReturnCode != 0:
		print("archive workspace %s failed" % (workspace))
		cleanArchiveFile(archivePath)
	else:
		exportDirectory = exportArchive(scheme, archivePath)
		cleanArchiveFile(archivePath)
		if exportDirectory != "":
			print("buildWorkspace_exportDirectory: " + exportDirectory)
			# 旧的getIpaPath方法会出现莫名其妙的bug
			ipaPath = getNewIpaPath(exportDirectory, scheme)
			uploadIpaToPgyer(ipaPath)


def xcbuild(options):
	project = options.project
	workspace = options.workspace
	scheme = options.scheme
	desc = options.desc

	global PGYDESC
	if desc != "":
		PGYDESC = desc

	if project is None and workspace is None:
		pass
	elif project is not None:
		buildProject(project, scheme)
	elif workspace is not None:
		buildWorkspace(workspace, scheme)


def main():

	parser = argparse.ArgumentParser()
	parser.add_argument("-w", "--workspace", help="Build the workspace name.xcworkspace.", metavar="name.xcworkspace")
	parser.add_argument("-p", "--project", help="Build the project name.xcodeproj.", metavar="name.xcodeproj")
	parser.add_argument("-s", "--scheme",
	                    help="Build the scheme specified by schemename. Required if building a workspace.",
	                    metavar="schemename")
	parser.add_argument("-m", "--desc", help="Pgyer update description.", metavar="description")
	options = parser.parse_args()

	print("options: %s" % (options))

	xcbuild(options)


if __name__ == '__main__':
	main()
