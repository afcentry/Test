#coding:utf-8

from py2neo import Graph, Node, Relationship

# 连接neo4j数据库
graph = Graph("http://localhost:7474",username="neo4j",password="afcentry")
print(graph)
# 创建结点：label结点，方便以后的结点查找操作
temp_node1 = Node(lable="Person",name="张三")
temp_node2 = Node(lable="Person",name="李四")
graph.create(temp_node1)
graph.create(temp_node2)
# 建立关系
node_1_call_node_2 = Relationship(temp_node1,'CALL',temp_node2)
node_1_call_node_2['count'] = 1
node_2_call_node_1 = Relationship(temp_node2,'CALL',temp_node1)
graph.create(node_2_call_node_1)
graph.create(node_1_call_node_2)
# 更新关系或节点的属性 push提交
node_1_call_node_2['count']+=1
graph.push(node_1_call_node_2)

# 通过属性值来查找节点和关系find_one
find_code = graph.find_one(
    label="明教",
    property_key="name",
    property_value="张无忌"
    )
print(find_code['name'])

# find方法已被弃用：通过属性值来查找所有节点和关系find替换为：NodeSelector
find = NodeSelector(graph).select('明教')
for f in find:
    print(f['name'])