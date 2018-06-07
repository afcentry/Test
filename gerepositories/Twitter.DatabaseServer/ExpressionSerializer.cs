using System.Linq.Expressions;
using FanoutSearch;
using Serialize.Linq.Factories;
using Serialize.Linq.Serializers;
using Serialize.Linq.Exceptions;
using Serialize.Linq.Nodes;
using Trinity.Storage;
using System;
using Serialize.Linq.Extensions;
using Action = FanoutSearch.Action;


namespace Twitter.DatabaseServer
{
    public class ExpressionSerializer:IExpressionSerializer
    {
        private static XmlSerializer m_serializer = null;
        private static NodeFactory m_factory = null;

        public ExpressionSerializer()
        {
            m_serializer=new XmlSerializer();
            m_serializer.AddKnownType(typeof(FanoutSearch.Action));
            m_factory=new NodeFactory();
        }
        
        public string Serialize(Expression pred)
        {
            return pred.ToXml(m_factory,m_serializer);
        }

        public Func<ICellAccessor, Action> DeserializeTraverseAction(string pred)
        {
            var func_exp = m_serializer.Deserialize<LambdaExpressionNode>(pred)
                .ToExpression<Func<ICellAccessor, FanoutSearch.Action>>();
            return func_exp.Compile();
        }

        public Func<ICellAccessor, bool> DeserializeOriginPredicate(string pred)
        {
            var fun_exp = m_serializer.Deserialize<LambdaExpressionNode>(pred)
                .ToExpression<Func<ICellAccessor, bool>>();
            return fun_exp.Compile();
        }
    }
}