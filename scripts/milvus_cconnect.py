from pymilvus import connections
from pymilvus import Collection
from pymilvus import utility
from pymilvus import CollectionSchema, FieldSchema, DataType

connections.connect(
  alias="default",     # 链接别名
  host='29.16.21.80',  # 服务端主机
  port='19530'         # 服务端端口
)


book_id    = FieldSchema(name="book_id",     dtype=DataType.INT64,  is_primary=True,)
book_name  = FieldSchema(name="book_name",   dtype=DataType.VARCHAR, max_length=200,)
word_count = FieldSchema(name="word_count",  dtype=DataType.INT64, )
book_intro = FieldSchema(name="book_intro",  dtype=DataType.FLOAT_VECTOR, dim=2)

schema          = CollectionSchema(fields=[book_id, book_name, word_count, book_intro], description="Test book search")
collection_name = "book"



collection = Collection(name=collection_name, schema=schema, using='default', shards_num=2)
collection.set_properties(properties={"collection.ttl.seconds": 1800})


has = utility.has_collection("book")
ls  = utility.list_collections()
suc = utility.drop_collection("book")

print(has, ls, suc)

connections.disconnect("default")