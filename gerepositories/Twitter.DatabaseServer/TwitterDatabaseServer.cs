using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Twitter.DatabaseModel;
using Twitter.DatabaseModel.TwitterDatabaseServer;

namespace Twitter.DatabaseServer
{
    public class TwitterDatabaseServer : TwitterDatabaseServerBase
    {
        public override void QueryHandler(QueryRequest request, out QueryResponse response)
        {
            response.Error = 111;
            response.Message = "查询结果为：" + request.JsonParams;
            response.JsonResponse = "fdsfsfdsfds";
        }
    }
}
