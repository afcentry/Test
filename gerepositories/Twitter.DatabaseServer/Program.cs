using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Twitter.DatabaseModel;
using Trinity.Core.Lib;
using Trinity;
using Trinity.Diagnostics;
using FanoutSearch;
using Trinity.Network;

namespace Twitter.DatabaseServer
{
    class Program
    {
        static unsafe void Main(string[] args)
        {
            //TrinityConfig.LoggingLevel = LogLevel.Debug;
            for (int i = -10; i < 10; i++)
            {
                Tweet t = new Tweet(cell_id: i, Content: $"推文正文：{i}", TweetTime: DateTime.Now);
                Global.LocalStorage.SaveTweet(t);
                
               
            }
            Global.LocalStorage.SaveStorage();
            FanoutSearchModule.EnableExternalQuery(true);
            LambdaDSL.SetDialect("LessNet", "Start", "Node", "Edge", "Action");
            FanoutSearchModule.SetQueryTimeout(3000);
            //FanoutSearchModule.RegisterIndexService(Indexer);
            FanoutSearchModule.RegisterExpressionSerializerFactory(ExpressionSerializerFactory);
            TwitterDatabaseServer server = new TwitterDatabaseServer();
            
            server.RegisterCommunicationModule<FanoutSearchModule>();
            server.Start();
        }

        private static IExpressionSerializer ExpressionSerializerFactory()
        {
            return new ExpressionSerializer();
        }

    }
}
