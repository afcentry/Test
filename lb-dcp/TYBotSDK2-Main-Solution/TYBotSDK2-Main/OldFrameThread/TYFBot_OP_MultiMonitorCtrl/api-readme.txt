{
  "table_name": "ow_kshow_command",
  "insert_data": {
    "type": 3,
    "status": 0,
    "command": "Data:index:深圳市"
  }
}



{
  "table_name": "ow_kshow_command",
  "insert_data": {
    "type": 2,
    "status": 0,
    "command": "EarlyWarning:asset:EarlyWarning:index"
  }
}


table_name  表名
type    
    2为页面切换
    3为内部数据切换
command
    type为3是command对应的格式为    Data:index:深圳市
                                    (数据:首页:深圳市)
                                    
    type为2是command对应的格式为    EarlyWarning:asset:EarlyWarning:index
                                    (态势模块:资产页面:态势模块:首页)