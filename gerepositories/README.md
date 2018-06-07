# GERepositories

图库数据仓库实现集合，所有Fiber涉及到的图库实现将在这里存放。

# 图库实现方式说明
* 图库以.Net为初步实现验证，.NetCore作为实际生产部分（便于跨平台）;
* .NetCore版本的项目实现均在项目名称上前缀.NetCore,如：Twitter.DatabaseModel 为.Net环境版本，Twitter.NetCore.DatabaseModel 为.NetCore版本实现。

# 开发环境搭建说明
1. 安装VS2017
2. 安装LessNetNugetPackages目录下的GraphEngine 插件：GraphEngineVSExtension.vsix
3. 若在通过插件创建项目，在编译时提示问题缺少相关dll，则可将下列NuGet包添加到项目引用中：Newtonsoft.Json，Microsoft.Extensions.ObjectPool，System.Runtime.Loader，Serialize.Linq。注意：提示缺什么，引用什么即可。 


# 文档目录
* [Twitter数据仓库](docs/twitter.readme.md)

# ChangeLog：
* 2018年5月14日：更新GraphEngine为最新2.0.9328版本，解决LIKQ索引为负值的BUG，同时使用全新配置文件格式。详见项目目录下：[trinity.xml](Twitter.DatabaseServer/trinity.xml)


