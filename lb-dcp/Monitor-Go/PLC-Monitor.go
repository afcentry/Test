package main

import (
	ui "github.com/gizak/termui"
	psNet "github.com/shirou/gopsutil/net"
	// psCpu "github.com/shirou/gopsutil/cpu"
	psMem "github.com/shirou/gopsutil/mem"
	"net/http"
	"io/ioutil"
	"strings"
	"errors"
	"encoding/json"
	"time"
	"fmt"

	"strconv"
)

type PLCMsg struct {
	Monitor_type string `json:"monitor_type"`
	Level string `json:"level"`
	Target string `json:"target,omitempty"`
	Plugin_id int `json:"plugin_id"`
	Block_id string `json:"block_id,omitempty"`
	Block_size int `json:"block_size"`
	Free_size int `json:"free_size"`
	Wait_size int `json:"wait_size"`
	Success_size int `json:"success_size"`
	Result_code int `json:"result_code"`
	Msg string `json:"msg,omitempty"`
}

type PLCMonitor struct {
	Monitor string `json:"monitor"`
	Time string `json:"time"`
	Msg PLCMsg `json:"msg"`
}

func GetMonitorMsg() (PLCMonitor,error) {
	var plc PLCMonitor
	resp,err:=http.Get("http://localhost:36500/monitor")
	if err!=nil{
		return plc,err
	}
	defer resp.Body.Close()
	body,err:=ioutil.ReadAll(resp.Body)
	if err!=nil{
		return plc,err
	}
	dataJson:=string(body[:])

	if !strings.Contains(dataJson,"msg"){
		return plc,errors.New("No avaliable monitor message.This means the message queue is empty.")
	}
	err=json.Unmarshal([]byte(body),&plc)
	if err!=nil{
		return plc,err
	}
	return plc,nil
}

func UpdateListData(orgStrs []string,dataStr string,timeStr string,level string) []string  {
	length :=len(orgStrs)
	var dt string
	if timeStr==""{
		dt = time.Now().Format("2006-01-02 15:04:05")//后面的参数是固定的 否则将无法正常输出
	}else {
		dt=timeStr
	}

	var colorStr string
	switch level {
	case "info":
		colorStr="fg-green"
	case "error":
		colorStr="fg-red"
	case "warning":
		colorStr="fg-yellow"
	default:
		colorStr="fg-magenta"
	}

	if length<8{
		orgStrs=append(orgStrs,fmt.Sprintf("[[%s] %s](%s)",dt,dataStr,colorStr))
	}else{
		orgStrs=append(orgStrs[1:],fmt.Sprintf("[[%s] %s](%s)",dt,dataStr,colorStr))
	}
	return orgStrs
}

func GetPluginName(id int) string {
	switch id {
	case 1,2:
		return "Ping"
	case 3,4:
		return "Web Crawler"
	case 5,6:
		return "Route Trace"
	case 7,8:
		return "DNS Trace"
	default:
		return "Unknown"
	}
}

func main() {
	if err:=ui.Init();err!=nil{
		panic(err)
	}
	defer ui.Close()
	isPause:=false //是否暂停滚动刷新

	datetime := time.Now().Format("2006-01-02 15:04:05")//后面的参数是固定的 否则将无法正常输出
	p := ui.NewPar(fmt.Sprintf("[PLC] Monitor Dashboard,Showing status of tasks... [%s]",datetime) )

	p.Height = 3
	p.Width = 120
	p.TextFgColor = ui.ColorWhite
	p.BorderLabel = "AI Distributed Computing System V1.0 @LessNet.cn"
	p.BorderLabelFg=ui.ColorCyan
	p.BorderLabelBg=ui.ColorDefault
	p.BorderFg = ui.ColorDefault
	p.BorderBg=ui.ColorDefault
	p.Handle("/timer/1s", func(e ui.Event) {
		dt := time.Now().Format("2006-01-02 15:04:05")//后面的参数是固定的 否则将无法正常输出
		cnt := e.Data.(ui.EvtTimer)
		if cnt.Count%2 == 0 {
			p.Text=fmt.Sprintf("[PLC] Monitor Dashboard,Showing status of tasks... [[%s]](fg-blue)",dt)
		} else {
			p.Text=fmt.Sprintf("[PLC] Monitor Dashboard,Showing status of tasks... [[%s]](fg-red)",dt)
		}


	})

	pluginName:="Loading..."
	pluginID:="Loading..."
	pluginFree:="Loading..."
	cpu:="Loading..."
	memory:="Loading..."
	network:="Loading..."
	var network_up_last uint64 =0
	var network_down_last uint64 =0

	rowsPlugin:=[][]string{
		[]string{"Plugin Name","Plugin ID","Free Worker","CPU","Memory","Network"},
		[]string{pluginName,pluginID,pluginFree,cpu,memory,network},
	}
	tablePlugin:=ui.NewTable()
	tablePlugin.Rows=rowsPlugin
	tablePlugin.FgColor=ui.ColorYellow
	tablePlugin.BgColor=ui.ColorDefault
	tablePlugin.BorderLabelBg=ui.ColorBlue
	tablePlugin.BorderFg=ui.ColorYellow
	tablePlugin.BorderBg=ui.ColorDefault
	tablePlugin.TextAlign=ui.AlignCenter
	tablePlugin.Width=120
	tablePlugin.Height=6
	tablePlugin.X=0
	tablePlugin.Y=3
	tablePlugin.Handle("/timer/1s", func(e ui.Event) {
		ios,err:=psNet.IOCounters(true)
		if err!=nil{
			network="Loading..."
		}else{
			//network=fmt.Sprintf(" ↑ %.2vKB/s  ↓ %.2vKB/s ",ios[0].BytesSent/1024.0/1024.0,ios[0].BytesRecv/1024.0/1024.0)
			if network_up_last==0{
				network_up_last=ios[0].BytesSent
			}
			if network_down_last==0{
				network_down_last=ios[0].BytesRecv
			}
			network=fmt.Sprintf(" ↑ %vKB/s  ↓ %vKB/s",(ios[0].BytesSent-network_up_last)/1024.0,(ios[0].BytesRecv-network_down_last)/1024.0)
			network_up_last=ios[0].BytesSent
			network_down_last=ios[0].BytesRecv
		}

		// cpus,err:=psCpu.Percent(0,false)
		// if err!=nil{
		//	cpu="Loading..."
		//}else{
		//	cpu=fmt.Sprintf("%.1f%%",cpus[0])
		//}

		m, err := psMem.VirtualMemory()
		if err!=nil{
			memory="Loading..."
		}else{
			//memory=fmt.Sprintf("%.2f%% [%.2vGB/%.2vGB]",m.UsedPercent,m.Used/1024.0/1024.0/1024.0,m.Total/1024.0/1024.0/1024.0)
			memory=fmt.Sprintf("%.2f%% [%vMB/%vMB]",m.UsedPercent,m.Used/1024.0/1024.0,m.Total/1024.0/1024.0)
		}
		rowsPlugin=[][]string{
			[]string{"Plugin Name","Plugin ID","Free Worker","CPU","Memory","Network"},
			[]string{pluginName,pluginID,pluginFree,cpu,memory,network},
		}
		tablePlugin.Rows=rowsPlugin

	})



	strResults := []string{}
	lbResult := ui.NewList()
	lbResult.Items = strResults
	lbResult.ItemFgColor = ui.ColorWhite
	lbResult.BorderLabel = "[Result View]"
	lbResult.BorderLabelFg=ui.ColorMagenta
	lbResult.BorderFg=ui.ColorMagenta
	lbResult.Height = 10
	lbResult.Width =120
	lbResult.Y = 9


	strStatus := []string{}
	lbStatus := ui.NewList()
	lbStatus.Items = strStatus
	lbStatus.ItemFgColor = ui.ColorYellow
	lbStatus.BorderLabel = "[Status View]"
	lbStatus.BorderLabelFg=ui.ColorGreen
	lbStatus.BorderFg=ui.ColorGreen
	lbStatus.Height = 10
	lbStatus.Width =120
	lbStatus.Y = 19

	tip:=ui.NewPar("")
	tip.Height=1
	tip.Y=29
	tip.Width=60
	tip.BorderLabel="[Press 'q' to exit.]  [Press 'p' to pause.]"
	tip.BorderLabelBg=ui.ColorRed
	tip.BorderLabelFg=ui.ColorWhite
	tip.BorderTop=false
	tip.BorderBottom=false
	tip.BorderLeft=false
	tip.BorderRight=false
	tip.BorderBg=ui.ColorRed

	stat:=ui.NewPar("")
	stat.Height=1
	stat.X=105
	stat.Y=29
	stat.Width=15
	stat.BorderLabel="[Running]"
	stat.BorderLabelBg=ui.ColorRed
	stat.BorderLabelFg=ui.ColorWhite
	stat.BorderTop=false
	stat.BorderBottom=false
	stat.BorderLeft=false
	stat.BorderRight=false
	stat.BorderBg=ui.ColorRed

	draw := func() {
		if isPause{
			ui.Render(p,lbResult,lbStatus)
			return
		}
		plc,err:=GetMonitorMsg()
		if err!=nil {
			//lbStatus.Items=UpdateListData(strStatus,fmt.Sprintf("Get Monitor data error:%s",err),"","error")
			ui.Render(p,lbResult,lbStatus,tip,stat,tablePlugin)
			return
		}


		dt:=plc.Time
		switch plc.Msg.Monitor_type {
		case "status":
			strStatus=UpdateListData(strStatus,plc.Msg.Msg,dt,plc.Msg.Level)
			lbStatus.Items=strStatus
		case "result":
			pluginID=strconv.Itoa(plc.Msg.Plugin_id)
			pluginName=GetPluginName(plc.Msg.Plugin_id)
			dataStr:=fmt.Sprintf("Received Result ---> Plguin ID:%d, Target:%s, Result:%s",plc.Msg.Plugin_id,plc.Msg.Target,plc.Msg.Msg)
			strResults=UpdateListData(strResults,dataStr,dt,"")
			lbResult.Items=strResults
		case "send-task-block":
			pluginID=string(plc.Msg.Plugin_id)
			pluginName=GetPluginName(plc.Msg.Plugin_id)
			dataStr:=fmt.Sprintf("Send Task Block ---> Plguin ID:%d, Block ID:%s, Block Size:%d",plc.Msg.Plugin_id,plc.Msg.Block_id,plc.Msg.Block_size)
			strStatus=UpdateListData(strStatus,dataStr,dt,plc.Msg.Level)
			lbStatus.Items=strStatus
		case "recv-task-block-free":
			pluginID=strconv.Itoa(plc.Msg.Plugin_id)
			pluginName=GetPluginName(plc.Msg.Plugin_id)
			pluginFree=strconv.Itoa(plc.Msg.Free_size)
			dataStr:=fmt.Sprintf("Free Task Count ---> Plguin ID:%d, Free Size:%d",plc.Msg.Plugin_id,plc.Msg.Free_size)
			strStatus=UpdateListData(strStatus,dataStr,dt,plc.Msg.Level)
			lbStatus.Items=strStatus
		case "block-finish-reply":
			dataStr:=fmt.Sprintf("Task Block Finished ---> Plguin ID:%d, Block ID:%s, Wait Size:%d, Result Code:%d",plc.Msg.Plugin_id,plc.Msg.Block_id,plc.Msg.Wait_size,plc.Msg.Result_code)
			strResults=UpdateListData(strResults,dataStr,dt,"")
			lbResult.Items=strResults
		case "send-task-block-reply":
			dataStr:=fmt.Sprintf("Send Task Success ---> Plguin ID:%d, Success Count:%d",plc.Msg.Plugin_id,plc.Msg.Success_size)
			strStatus=UpdateListData(strStatus,dataStr,dt,plc.Msg.Level)
			lbStatus.Items=strStatus
		}

		rowsPlugin=[][]string{
			[]string{"Plugin Name","Plugin ID","Free Worker","CPU","Memory","Network"},
			[]string{pluginName,pluginID,pluginFree,cpu,memory,network},
		}
		tablePlugin.Rows=rowsPlugin


		ui.Render(p,lbResult,lbStatus,tip,stat,tablePlugin)



	}

	ui.Handle("/sys/kbd/q", func(ui.Event) {
		ui.StopLoop()
	})
	ui.Handle("/sys/kbd/p", func(ui.Event) {
		isPause=!isPause
		if isPause{
			stat.BorderLabel="[Paused]"
		}else {
			stat.BorderLabel="[Running]"
		}
		ui.Render(stat)
	})
	ui.Handle("/timer/1s", func(e ui.Event) {
		draw()
	})

	ui.Loop()




}

